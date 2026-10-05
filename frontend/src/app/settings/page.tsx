"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Settings, Check } from "lucide-react";
import { CURRENCIES, TRAVEL_STYLES } from "@/lib/types";

export default function SettingsPage() {
  const [currency, setCurrency] = useState("USD");
  const [travelStyle, setTravelStyle] = useState("balanced");
  const [saved, setSaved] = useState(false);

  const [accessKey, setAccessKey] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    try {
      const storedCurrency = localStorage.getItem("trippilot_default_currency");
      const storedStyle = localStorage.getItem("trippilot_default_style");
      if (CURRENCIES.some(c => c.code === storedCurrency)) setCurrency(storedCurrency!);
      if (TRAVEL_STYLES.some(s => s.value === storedStyle)) setTravelStyle(storedStyle!);
      setAccessKey(sessionStorage.getItem("trippilot_access_key") || "");
    } catch { setError("Browser storage is unavailable. Allow site storage to save settings."); }
  }, []);

  const handleSave = () => {
    try {
    sessionStorage.setItem("trippilot_access_key", accessKey.trim());
    setError("");
    // Save to localStorage for MVP
    localStorage.setItem("trippilot_default_currency", currency);
    localStorage.setItem("trippilot_default_style", travelStyle);
    setSaved(true);
    } catch { setError("Could not save settings. Allow site storage and retry."); }
  };

  return (
    <div className="container mx-auto py-10 px-4 max-w-2xl">
      <div className="flex items-center gap-3 mb-8">
        <Settings className="h-8 w-8 text-gray-400" />
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Default Preferences</CardTitle>
          <CardDescription>
            These defaults will be pre-filled when you create a new trip.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="access-key" className="text-sm font-medium">Workspace access key</label>
            <input id="access-key" type="password" autoComplete="off" maxLength={256}
              className="flex h-10 w-full rounded-md border px-3 py-2 text-sm"
              value={accessKey} onChange={e => { setAccessKey(e.target.value); setSaved(false); }} />
            <p className="text-xs text-gray-500">Use the server SECRET_KEY. Kept only for this browser tab; clear it and save to disconnect.</p>
          </div>
          {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
          <div className="space-y-2">
            <label htmlFor="default-currency" className="text-sm font-medium text-gray-700">
              Default Currency
            </label>
            <select id="default-currency"
              className="flex h-10 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm"
              value={currency}
              onChange={(e) => { setCurrency(e.target.value); setSaved(false); }}
            >
              {CURRENCIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} ({c.symbol}) — {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            <label className="text-sm font-medium text-gray-700">
              Preferred Travel Style
            </label>
            <div className="grid grid-cols-3 gap-3">
              {TRAVEL_STYLES.map((style) => (
                <button
                  key={style.value}
                  type="button"
                  aria-pressed={travelStyle === style.value}
                  onClick={() => { setTravelStyle(style.value); setSaved(false); }}
                  className={`p-3 rounded-lg border-2 text-center transition-all ${
                    travelStyle === style.value
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-gray-200 hover:border-gray-300 text-gray-600"
                  }`}
                >
                  <span className="font-medium text-sm">{style.label}</span>
                  <p className="text-xs text-gray-500 mt-1">
                    {style.description}
                  </p>
                </button>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t">
            <Button onClick={handleSave} className="w-full">
              {saved ? (
                <>
                  <Check className="mr-2 h-4 w-4" /> Saved!
                </>
              ) : (
                "Save Settings"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
