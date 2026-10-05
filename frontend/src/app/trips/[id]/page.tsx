"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Trip, AgentStatus, Itinerary, BudgetBreakdown, WeatherData } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  MapPin,
  Calendar,
  Users,
  DollarSign,
  Send,
  Loader2,
  CheckCircle2,
  Circle,
  AlertCircle,
  CloudSun,
  Thermometer,
  Droplets,
  ChevronDown,
  ChevronUp,
  Clock,
  Car,
  Hotel,
  UtensilsCrossed,
  Camera,
  Map,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import { formatCurrency } from "@/lib/utils";

// ─── Data Source Badge ────────────────────────────────────────────────────────
function DataSourceBadge({ source }: { source: string }) {
  const config: Record<string, { label: string; className: string }> = {
    api: { label: "Live data", className: "bg-green-100 text-green-700" },
    estimated: { label: "Estimated", className: "bg-amber-100 text-amber-700" },
    user: { label: "User", className: "bg-blue-100 text-blue-700" },
    mock: { label: "Demo", className: "bg-gray-100 text-gray-500" },
    "mock/demo": { label: "Demo", className: "bg-gray-100 text-gray-500" },
  };
  const c = config[source] || config.estimated;
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${c.className}`}>
      {c.label}
    </span>
  );
}

// ─── Category Icon ────────────────────────────────────────────────────────────
function CategoryIcon({ category }: { category: string }) {
  const icons: Record<string, React.ReactNode> = {
    transport: <Car className="h-4 w-4 text-blue-500" />,
    accommodation: <Hotel className="h-4 w-4 text-purple-500" />,
    food: <UtensilsCrossed className="h-4 w-4 text-orange-500" />,
    activity: <Camera className="h-4 w-4 text-emerald-500" />,
    sightseeing: <Map className="h-4 w-4 text-indigo-500" />,
  };
  return <>{icons[category] || <MapPin className="h-4 w-4 text-gray-500" />}</>;
}

// ─── Agent Status Panel ───────────────────────────────────────────────────────
const AGENT_STEPS = [
  { key: "collect_preferences", label: "Understanding preferences" },
  { key: "validate_preferences", label: "Validating information" },
  { key: "destination_research", label: "Researching destination" },
  { key: "weather_research", label: "Checking weather" },
  { key: "attraction_research", label: "Finding attractions" },
  { key: "itinerary_planner", label: "Creating itinerary" },
  { key: "budget_calculator", label: "Calculating budget" },
  { key: "validate_itinerary", label: "Validating plan" },
  { key: "generate_final_response", label: "Finalizing trip" },
];

function AgentStatusPanel({ status }: { status: AgentStatus | null }) {
  if (!status || status.status === "idle") return null;

  const completedSteps = status.steps
    ?.filter((s) => s.status === "completed")
    .map((s) => s.node_name) || [];
  const currentNode = status.current_node;

  return (
    <Card className="mb-6 border-blue-200 bg-blue-50/50">
      <CardContent className="py-4">
        <div className="flex items-center gap-2 mb-3">
          {status.status === "running" && (
            <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
          )}
          {status.status === "completed" && (
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          )}
          {status.status === "failed" && (
            <AlertCircle className="h-4 w-4 text-red-600" />
          )}
          <span className="text-sm font-medium text-gray-700">
            {status.status === "running" && "AI Agent is planning your trip..."}
            {status.status === "completed" && "Trip plan ready!"}
            {status.status === "failed" && "Something went wrong"}
          </span>
        </div>
        <div className="space-y-1.5">
          {AGENT_STEPS.map((step) => {
            const isCompleted = completedSteps.includes(step.key);
            const isCurrent = currentNode === step.key;
            return (
              <div key={step.key} className="flex items-center gap-2">
                {isCompleted ? (
                  <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                ) : isCurrent ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-500" />
                ) : (
                  <Circle className="h-3.5 w-3.5 text-gray-300" />
                )}
                <span
                  className={`text-xs ${
                    isCompleted
                      ? "text-green-700"
                      : isCurrent
                      ? "text-blue-700 font-medium"
                      : "text-gray-400"
                  }`}
                >
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Day Card ─────────────────────────────────────────────────────────────────
function DayCard({
  day, currency,
}: {
  currency: string;
  day: { day_number: number; date: string; title: string; summary?: string; activities: Array<{
    title: string; description?: string; location_name?: string;
    start_time?: string; end_time?: string; duration_minutes?: number;
    category?: string; estimated_cost?: number; cost_currency?: string;
    data_source?: string; latitude?: number; longitude?: number;
    source_url?: string; notes?: string;
  }> };
}) {
  const [expanded, setExpanded] = useState(true);
  const totalCost = day.activities.reduce(
    (sum, a) => sum + (a.estimated_cost || 0), 0
  );

  return (
    <Card className="mb-4">
      <button
        aria-expanded={expanded}
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-700 text-sm font-bold">
            {day.day_number}
          </div>
          <div className="text-left">
            <p className="font-medium text-gray-900">{day.title}</p>
            <p className="text-xs text-gray-500">{day.date}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">
            {day.activities.length} activities · ~{formatCurrency(totalCost, currency)}
          </span>
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </button>

      {expanded && (
        <CardContent className="pt-0 pb-4">
          {day.summary && <p className="mb-4 text-sm text-gray-600">{day.summary}</p>}
          <div className="border-l-2 border-gray-200 ml-4 pl-6 space-y-4">
            {day.activities.map((activity, i) => (
              <div key={i} className="relative">
                <div className="absolute -left-[31px] top-1 w-3 h-3 rounded-full bg-white border-2 border-blue-400" />
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <CategoryIcon category={activity.category || "activity"} />
                      <span className="font-medium text-sm text-gray-900">
                        {activity.title}
                      </span>
                      {activity.data_source && (
                        <DataSourceBadge source={activity.data_source} />
                      )}
                    </div>
                    {activity.description && (
                      <p className="text-xs text-gray-500 ml-6 mb-1">
                        {activity.description}
                      </p>
                    )}
                    {activity.notes && <p className="ml-6 mb-2 text-xs text-gray-600">{activity.notes}</p>}
                    <div className="flex flex-wrap items-center gap-3 ml-6 text-xs text-gray-600">
                      {activity.start_time && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {activity.start_time}
                          {activity.end_time && ` - ${activity.end_time}`}
                        </span>
                      )}
                      {activity.location_name && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {activity.location_name}
                        </span>
                      )}
                      {activity.source_url?.startsWith("https://") && (
                        <a href={activity.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-700 underline">Place source</a>
                      )}
                      {activity.latitude != null && activity.longitude != null && (
                        <a href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${activity.latitude},${activity.longitude}`)}`} target="_blank" rel="noopener noreferrer" className="text-blue-700 underline">View map</a>
                      )}
                    </div>
                  </div>
                  {activity.estimated_cost != null && activity.estimated_cost > 0 && (
                    <span className="text-sm font-medium text-gray-700 whitespace-nowrap">
                      {formatCurrency(activity.estimated_cost, activity.cost_currency || currency)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

// ─── Main Trip Workspace ──────────────────────────────────────────────────────
export default function TripWorkspacePage() {
  const params = useParams();
  const tripId = params.id as string;

  const [trip, setTrip] = useState<Trip | null>(null);
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [modifyInput, setModifyInput] = useState("");
  const [modifying, setModifying] = useState(false);
  const [error, setError] = useState("");

  // Load trip data
  const loadTrip = useCallback(async () => {
    try {
      const tripData = await api.getTrip(tripId);
      setTrip(tripData);
      setError("");

      // Load agent status to check for itinerary
      try {
        const status = await api.getTripStatus(tripId);
        setAgentStatus(status);
        setGenerating(status.status === "running");
        if (status.error) setError(status.error);
        if (status.itinerary) {
          setItinerary(status.itinerary);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load planning status. Reload to retry.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load trip");
    } finally {
      setLoading(false);
    }
  }, [tripId]);

  useEffect(() => {
    setLoading(true);
    setTrip(null);
    setAgentStatus(null);
    setGenerating(false);
    setModifying(false);
    setItinerary(null);
    setWeatherData(null);
    loadTrip();
  }, [loadTrip]);

  // Optional weather must not block opening the saved itinerary.
  useEffect(() => {
    if (!trip) return;
    let cancelled = false;
    api.getWeather(trip.destination, trip.start_date, trip.end_date)
      .then(weather => { if (!cancelled) setWeatherData(weather.data); })
      .catch(() => { /* Forecasts are optional. */ });
    return () => { cancelled = true; };
  }, [trip]);

  const running = agentStatus?.status === "running";
  // Poll agent status while running
  useEffect(() => {
    if (!running) return;

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    let failures = 0;
    const poll = async () => {
      try {
        const status = await api.getTripStatus(tripId);
        if (cancelled) return;
        failures = 0;
        setAgentStatus(status);
        if (status.itinerary) setItinerary(status.itinerary);
        if (status.status !== "running") {
          setGenerating(false);
          setModifying(false);
          if (status.error) setError(status.error);
          setTrip(await api.getTrip(tripId));
          return;
        }
      } catch {
        if (++failures >= 5) {
          if (!cancelled) {
            setError("Connection lost. Reload to check planning progress.");
            setGenerating(false);
            setModifying(false);
          }
          return;
        }
      }
      if (!cancelled) timer = setTimeout(poll, 2000);
    };
    timer = setTimeout(poll, 2000);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [running, tripId]);

  const busy = generating || modifying || agentStatus?.status === "running";

  const handleGenerate = async () => {
    if (busy) return;
    setGenerating(true);
    setError("");
    try {
      const status = await api.generateItinerary(tripId);
      setAgentStatus(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start generation");
      setGenerating(false);
    }
  };

  const handleModify = async () => {
    if (busy || !modifyInput.trim()) return;
    setModifying(true);
    setError("");
    try {
      const status = await api.modifyItinerary(tripId, modifyInput);
      setAgentStatus(status);
      setModifyInput("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to modify itinerary");
      setModifying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!trip) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <AlertCircle className="h-12 w-12 text-red-400" />
        <p role="alert" className="text-lg text-gray-600">{error || "Trip not found"}</p>
        <Link href="/settings">Open Settings</Link>
        <Button asChild variant="outline"><Link href="/trips">Back to Trips</Link></Button>
      </div>
    );
  }

  // Calculate budget breakdown from itinerary
  const budgetBreakdown: BudgetBreakdown | null = itinerary
    ? (() => {
        let transport = 0, accommodation = 0, food = 0, activities = 0;
        itinerary.days?.forEach((day) => {
          day.activities?.forEach((a) => {
            const cost = a.estimated_cost || 0;
            switch (a.category) {
              case "transport": transport += cost; break;
              case "accommodation": accommodation += cost; break;
              case "food": food += cost; break;
              default: activities += cost;
            }
          });
        });
        const total = transport + accommodation + food + activities;
        return {
          transport, accommodation, food, activities,
          total_cost: total,
          currency: itinerary.currency || trip.budget_currency,
          within_budget: (itinerary.currency || trip.budget_currency) === trip.budget_currency && total <= trip.budget_amount,
        };
      })()
    : null;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex flex-col xl:flex-row xl:h-[calc(100vh-64px)]">
        {/* ─── Left Sidebar ──────────────────────────────────────────── */}
        <aside className="w-full xl:w-64 shrink-0 bg-white border-r overflow-y-auto">
          <div className="p-4">
            <h1 className="font-semibold text-gray-900 text-lg mb-4">
              {trip.title}
            </h1>

            <div className="space-y-3 text-sm">
              <div className="flex items-center gap-2 text-gray-600">
                <MapPin className="h-4 w-4 text-gray-400" />
                <span>
                  {trip.origin} → {trip.destination}
                </span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Calendar className="h-4 w-4 text-gray-400" />
                <span>
                  {trip.start_date} → {trip.end_date}
                </span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Users className="h-4 w-4 text-gray-400" />
                <span>{trip.num_travelers} traveler(s)</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <DollarSign className="h-4 w-4 text-gray-400" />
                <span>
                  {trip.budget_amount.toLocaleString()} {trip.budget_currency}
                </span>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-1.5">
              {trip.preferences?.map((p) => (
                <span
                  key={p}
                  className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs"
                >
                  {p}
                </span>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t">
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  trip.status === "generated"
                    ? "bg-green-100 text-green-800"
                    : trip.status === "planning"
                    ? "bg-blue-100 text-blue-800"
                    : trip.status === "error"
                    ? "bg-red-100 text-red-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {trip.status.charAt(0).toUpperCase() + trip.status.slice(1)}
              </span>
            </div>
          </div>

          {/* Saved Trips Navigation */}
          <div className="border-t p-4">
            <Button asChild variant="ghost" size="sm" className="w-full justify-start"><Link href="/trips">
                ← All Trips
              </Link></Button>
          </div>
        </aside>

        {/* ─── Main Content ──────────────────────────────────────────── */}
        <section className="min-w-0 flex-1 overflow-y-auto p-3 sm:p-6">
          <div className="max-w-3xl mx-auto">
            {/* Agent Status */}
            <AgentStatusPanel status={agentStatus} />

            {/* Error Display */}
            {error && (
              <div role="alert" className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Generate Button (when no itinerary) */}
            {!itinerary && !busy && (
              <Card className="mb-6">
                <CardContent className="py-8 text-center">
                  <Map className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Ready to plan your trip?
                  </h3>
                  <p className="text-gray-500 mb-6 text-sm">
                    Our AI agent will research your destination, check weather,
                    find attractions, and create a personalized itinerary.
                  </p>
                  <Button
                    onClick={handleGenerate}
                    size="lg"
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    Generate Itinerary
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Generating spinner */}
            {generating && !itinerary && !agentStatus && (
              <Card className="mb-6">
                <CardContent className="py-8 text-center">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
                  <p className="text-gray-600">Starting AI agent...</p>
                </CardContent>
              </Card>
            )}

            {/* Itinerary Display */}
            {itinerary && itinerary.days && (
              <>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Your day-by-day plan</h2>
                {itinerary.days.map((day) => (
                  <DayCard key={day.day_number} day={day} currency={itinerary.currency || trip.budget_currency} />
                ))}

                <Card className="mt-6">
                  <CardHeader><CardTitle className="text-lg">Trip summary</CardTitle></CardHeader>
                  <CardContent className="space-y-5">
                    <p className="text-sm leading-relaxed text-gray-700 whitespace-pre-line">
                      {itinerary.summary || `${itinerary.days.length} days in ${trip.destination}. Review the daily stops above for your route.`}
                    </p>
                    {budgetBreakdown && <p className="text-sm text-gray-700">Estimated total for {trip.num_travelers} traveler(s): <strong>{formatCurrency(budgetBreakdown.total_cost, budgetBreakdown.currency)}</strong>. Timings and prices need confirmation before booking.</p>}
                    {(itinerary.research_warnings || []).map((warning) => <p key={warning} className="text-sm text-amber-800">{warning}</p>)}
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">What to eat & where</h3>
                      {itinerary.food_guide?.map((note, index) => <p key={index} className="text-sm leading-relaxed text-gray-700 mb-3">{note}</p>)}
                      {itinerary.food_places?.length ? (
                        <ul className="space-y-3">
                          {itinerary.food_places.map((place, index) => (
                            <li key={`${place.name}-${index}`} className="text-sm border-t pt-3">
                              <p className="font-medium text-gray-900">{place.name}</p>
                              {place.description && <p className="mt-1 leading-relaxed text-gray-600">{place.description}</p>}
                              {place.source_url?.startsWith("https://") && <a href={place.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-700 underline">Read food guide</a>}
                            </li>
                          ))}
                        </ul>
                      ) : <p className="text-sm text-gray-600">No restaurant research is saved for this plan. Regenerate to search for local food and places.</p>}
                    </div>
                    {!!itinerary.research_sources?.length && (
                      <div className="border-t pt-4">
                        <h3 className="font-semibold text-gray-900 mb-2">Research sources</h3>
                        <ul className="space-y-2 text-sm">
                          {itinerary.research_sources.filter(source => source.url.startsWith("https://")).map(source => <li key={source.url}><a href={source.url} target="_blank" rel="noopener noreferrer" className="text-blue-700 underline">{source.title}</a></li>)}
                        </ul>
                        <p className="mt-2 text-xs text-gray-600">Guide and cuisine excerpts are from the linked Wikimedia contributors, CC BY-SA. Place listings are recommendations, not confirmed bookings or current menus.</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Modification Input */}
                <Card className="mt-6">
                  <CardContent className="py-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">
                      Want to change something?
                    </p>
                    <div className="flex gap-2">
                      <Input
                        aria-label="Modification instruction" maxLength={4000}
                        placeholder='e.g., "Add more adventure activities to day 2"'
                        value={modifyInput}
                        onChange={(e) => setModifyInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleModify()}
                        disabled={busy}
                      />
                      <Button
                        onClick={handleModify}
                        aria-label="Modify itinerary" disabled={busy || !modifyInput.trim()}
                        size="sm"
                      >
                        {modifying ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Send className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </section>

        {/* ─── Right Panel ───────────────────────────────────────────── */}
        <aside className="w-full xl:w-80 shrink-0 bg-white border-l overflow-y-auto">
          <div className="p-4 space-y-4">
            {/* Budget Summary */}
            {budgetBreakdown && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <DollarSign className="h-4 w-4" /> Budget
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {[
                      { label: "Transport", value: budgetBreakdown.transport, color: "bg-blue-400" },
                      { label: "Accommodation", value: budgetBreakdown.accommodation, color: "bg-purple-400" },
                      { label: "Food", value: budgetBreakdown.food, color: "bg-orange-400" },
                      { label: "Activities", value: budgetBreakdown.activities, color: "bg-emerald-400" },
                    ].map((item) => (
                      <div key={item.label}>
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                          <span>{item.label}</span>
                          <span>{formatCurrency(item.value, budgetBreakdown.currency)}</span>
                        </div>
                        <div className="h-1.5 bg-gray-100 rounded-full">
                          <div
                            className={`h-1.5 rounded-full ${item.color}`}
                            style={{
                              width: `${Math.min(
                                100,
                                (item.value / (budgetBreakdown.total_cost || 1)) * 100
                              )}%`,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                    <div className="pt-2 mt-2 border-t flex justify-between">
                      <span className="text-sm font-medium">Total</span>
                      <span
                        className={`text-sm font-bold ${
                          budgetBreakdown.within_budget
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {formatCurrency(budgetBreakdown.total_cost, budgetBreakdown.currency)} / {formatCurrency(trip.budget_amount, trip.budget_currency)}
                      </span>
                    </div>
                    <DataSourceBadge source="estimated" />
                    {budgetBreakdown.currency !== trip.budget_currency && <p className="text-xs text-amber-800">Fallback estimates are in USD. Currency conversion and budget comparison are unavailable.</p>}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Weather */}
            {weatherData && weatherData.forecast?.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <CloudSun className="h-4 w-4" /> Weather
                    <DataSourceBadge source="api" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {weatherData.forecast.slice(0, 5).map((day) => (
                      <div
                        key={day.date}
                        className="flex items-center justify-between text-xs"
                      >
                        <span className="text-gray-500 w-20">{day.date}</span>
                        <span className="flex items-center gap-1">
                          <Thermometer className="h-3 w-3 text-red-400" />
                          {day.temp_high}° / {day.temp_low}°
                        </span>
                        <span className="flex items-center gap-1 text-gray-400">
                          <Droplets className="h-3 w-3" />
                          {day.precipitation_mm}mm
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Quick Stats */}
            {itinerary && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Trip Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <p className="text-xl font-bold text-gray-900">
                        {itinerary.days?.length || 0}
                      </p>
                      <p className="text-xs text-gray-500">Days</p>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <p className="text-xl font-bold text-gray-900">
                        {itinerary.days?.reduce(
                          (sum, d) => sum + (d.activities?.length || 0),
                          0
                        ) || 0}
                      </p>
                      <p className="text-xs text-gray-500">Activities</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Regenerate */}
            {itinerary && (
              <Button
                variant="outline"
                className="w-full"
                onClick={handleGenerate}
                disabled={busy}
              >
                <RefreshCw className="h-4 w-4 mr-2" /> Regenerate
              </Button>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
