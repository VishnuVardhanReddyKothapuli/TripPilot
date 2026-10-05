"""Destination-specific Wikivoyage research, without an API key."""
import logging
import asyncio
from html.parser import HTMLParser
from urllib.parse import quote, unquote
import httpx
from .base import simple_cache

logger = logging.getLogger(__name__)


class GuideParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.section = ""
        self.listing = None
        self.attractions, self.restaurants, self.food_notes = [], [], []
        self.linked_pages = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "h2":
            self.section = attrs.get("id", "").lower()
        if "vcard" in classes:
            self.listing = {"section": self.section}
            for item in self.stack:
                item[4] = True
        if tag == "a" and attrs.get("href", "").startswith("/wiki/"):
            self.linked_pages.append(unquote(attrs["href"][6:].split("#")[0]).replace("_", " "))
        fields = {"listing-name": "name", "listing-content": "description",
                  "listing-address": "address", "latitude": "lat", "longitude": "lon"}
        field = next((value for key, value in fields.items() if key in classes), None)
        if tag not in {"br", "hr", "img", "input", "meta", "link", "wbr"}:
            ignored = bool(set(classes) & {"reference", "references", "reflist", "mw-editsection", "navbox"})
            self.stack.append([tag, field, [], "vcard" in classes, False, ignored])

    def handle_data(self, data):
        if any(item[0] in {"style", "script"} or item[5] for item in self.stack):
            return
        for item in self.stack:
            if item[1] or item[0] in {"p", "figcaption", "li"}:
                item[2].append(data)

    def handle_endtag(self, tag):
        index = next((i for i in range(len(self.stack) - 1, -1, -1)
                      if self.stack[i][0] == tag), None)
        if index is None:
            return
        items, self.stack = self.stack[index:], self.stack[:index]
        for element, field, parts, is_listing, contains_listing, _ in reversed(items):
            text = " ".join("".join(parts).split())
            if field and self.listing is not None:
                self.listing[field] = text
            if is_listing and self.listing is not None:
                place, self.listing = self.listing, None
                section = place.pop("section")
                if not place.get("name"):
                    continue
                for coord in ("lat", "lon"):
                    try:
                        place[coord] = float(place[coord])
                    except (KeyError, ValueError):
                        place[coord] = None
                place.update(type="travel guide listing", data_source="api")
                if section in {"see", "do"}:
                    self.attractions.append(place)
                elif section.startswith("eat"):
                    self.restaurants.append(place)
            if element in {"p", "figcaption", "li"} and self.section.startswith("eat") and text and not self.listing and not contains_listing:
                self.food_notes.append(text[:1200])


async def _research_travel_guide(destination: str) -> dict:
    """Resolve the destination guide and preserve source attribution with excerpts."""
    empty = {"attractions": [], "restaurants": [], "food_notes": [], "sources": []}
    try:
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": "TripPilot/0.1 (travel research)"}) as client:
            async def query(params):
                response = await client.get("https://en.wikivoyage.org/w/api.php",
                                            params={"format": "json", "formatversion": 2, **params})
                response.raise_for_status()
                return response.json()

            # Search within the destination's title; never substitute a different city.
            title = destination.split(",")[0].strip()
            data = await query({"action": "parse", "page": title, "prop": "text", "redirects": 1})
            if "parse" not in data:
                results = await query({"action": "query", "list": "search", "srsearch": f'intitle:"{title}"', "srlimit": 5})
                matches = results.get("query", {}).get("search", [])
                match = next((m for m in matches if m["title"].casefold() == title.casefold()
                              or m["title"].casefold().startswith(title.casefold() + " (")), None)
                if not match:
                    return empty
                data = await query({"action": "parse", "page": match["title"], "prop": "text", "redirects": 1})
            page = data.get("parse", {})
            result = {"attractions": [], "restaurants": [], "food_notes": [], "sources": []}

            def collect(page):
                parser = GuideParser()
                parser.feed(page.get("text", ""))
                page_title = page.get("title", title)
                url = "https://en.wikivoyage.org/wiki/" + quote(page_title.replace(" ", "_"), safe="/")
                for key, anchor in (("attractions", "See"), ("restaurants", "Eat")):
                    for place in getattr(parser, key):
                        place["source_url"] = url + "#" + anchor
                    result[key].extend(getattr(parser, key))
                result["food_notes"].extend(parser.food_notes)
                result["sources"].append({"title": page_title + " — Wikivoyage contributors (CC BY-SA)", "url": url})
                return parser

            parser = collect(page)
            # Large cities keep named sights and restaurants on district pages.
            districts = list(dict.fromkeys(p for p in parser.linked_pages if p.startswith(page.get("title", title) + "/")))[:3]
            if districts and (not result["attractions"] or not result["restaurants"]):
                pages = await asyncio.gather(*(query({"action": "parse", "page": district, "prop": "text", "redirects": 1}) for district in districts), return_exceptions=True)
                for district in pages:
                    if isinstance(district, dict) and "parse" in district:
                        collect(district["parse"])
            result["attractions"] = result["attractions"][:80]
            result["restaurants"] = result["restaurants"][:60]
            result["food_notes"] = list(dict.fromkeys(result["food_notes"]))[:8]
            return result
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        logger.warning("Travel guide research unavailable")
        return empty


async def _research_cuisine(destination: str) -> dict:
    """Search the destination article's cuisine section for regional dishes."""
    try:
        async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "TripPilot/0.1 (travel research)"}) as client:
            async def query(params):
                response = await client.get("https://en.wikipedia.org/w/api.php", params={"action": "parse", "format": "json", "formatversion": 2, "redirects": 1, **params})
                response.raise_for_status()
                return response.json().get("parse", {})
            page = await query({"page": destination.split(",")[0].strip(), "prop": "sections"})
            section = next((s for s in page.get("sections", []) if any(term in s.get("line", "").casefold() for term in ("cuisine", "food and"))), None)
            if not section:
                return {}
            content = await query({"page": page["title"], "prop": "text", "section": section["index"]})
            parser = GuideParser()
            parser.section = "eat"
            # The requested API section may use any heading level.
            parser.feed(content.get("text", "").replace('<h2 ', '<h3 ').replace('</h2>', '</h3>'))
            url = "https://en.wikipedia.org/wiki/" + quote(page["title"].replace(" ", "_")) + "#" + quote(section["anchor"])
            return {"food_notes": parser.food_notes[:4], "source": {"title": page["title"] + " cuisine — Wikipedia contributors (CC BY-SA)", "url": url}}
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        logger.warning("Local cuisine research unavailable")
        return {}


@simple_cache(ttl_seconds=21600)
async def research_destination(destination: str) -> dict:
    guide, cuisine = await asyncio.gather(_research_travel_guide(destination), _research_cuisine(destination))
    if cuisine.get("food_notes"):
        guide["food_notes"] = cuisine["food_notes"] + guide["food_notes"][:4]
        guide["sources"].append(cuisine["source"])
    return guide
