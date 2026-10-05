"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  MapPin,
  Calendar,
  Users,
  DollarSign,
  Heart,
  CheckCircle2,
  ArrowLeft,
  ArrowRight,
  Plane,
  Compass,
  Star,
  Backpack,
  Loader2,
} from "lucide-react";
import { api } from "@/lib/api";
import { TRAVEL_PREFERENCES, TRAVEL_STYLES, CURRENCIES, TripCreate } from "@/lib/types";

const STEPS = [
  { title: "Destination", icon: MapPin },
  { title: "Dates", icon: Calendar },
  { title: "Budget", icon: DollarSign },
  { title: "Preferences", icon: Heart },
  { title: "Review", icon: CheckCircle2 },
];

export default function NewTripPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Form state
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [numTravelers, setNumTravelers] = useState(1);
  const [budgetAmount, setBudgetAmount] = useState<number>(1000);
  const [budgetCurrency, setBudgetCurrency] = useState("USD");
  const [travelStyle, setTravelStyle] = useState("balanced");
  const [preferences, setPreferences] = useState<string[]>([]);
  const [additionalNotes, setAdditionalNotes] = useState("");

  const today = new Date().toLocaleDateString("en-CA");
  useEffect(() => {
    try {
      const currency = localStorage.getItem("trippilot_default_currency");
      const style = localStorage.getItem("trippilot_default_style");
      if (CURRENCIES.some(c => c.code === currency)) setBudgetCurrency(currency!);
      if (TRAVEL_STYLES.some(s => s.value === style)) setTravelStyle(style!);
    } catch { /* Defaults still work without storage. */ }
  }, []);

  const togglePreference = (pref: string) => {
    setPreferences((prev) =>
      prev.includes(pref) ? prev.filter((p) => p !== pref) : [...prev, pref]
    );
  };

  const canAdvance = () => {
    switch (step) {
      case 0:
        return origin.trim() && destination.trim();
      case 1:
        return startDate >= today && endDate >= startDate && (Date.parse(endDate) - Date.parse(startDate)) / 86400000 < 30;
      case 2:
        return Number.isFinite(budgetAmount) && budgetAmount > 0 && budgetAmount <= 100000000 && travelStyle;
      case 3:
        return true;
      case 4:
        return true;
      default:
        return false;
    }
  };

  const handleSubmit = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setError("");
    try {
      const tripData: TripCreate = {
        origin,
        destination,
        start_date: startDate,
        end_date: endDate,
        num_travelers: numTravelers,
        budget_amount: budgetAmount,
        budget_currency: budgetCurrency,
        travel_style: travelStyle,
        preferences: preferences.map((p) => p.toLowerCase()),
        additional_notes: additionalNotes || undefined,
      };
      const trip = await api.createTrip(tripData);
      try { await api.generateItinerary(trip.id); } catch { /* Open the saved trip so generation can be retried without duplicating it. */ }
      router.push(`/trips/${trip.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create trip");
      setIsSubmitting(false);
    }
  };

  const styleIcons: Record<string, React.ReactNode> = {
    budget: <Backpack className="h-6 w-6" />,
    balanced: <Compass className="h-6 w-6" />,
    luxury: <Star className="h-6 w-6" />,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8 px-4 max-w-3xl">
        <h1 className="text-2xl font-bold mb-6">New trip</h1>
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              return (
                <div key={s.title} className="flex items-center">
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors ${
                      i <= step
                        ? "bg-blue-600 border-blue-600 text-white"
                        : "border-gray-300 text-gray-400"
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  {i < STEPS.length - 1 && (
                    <div
                      className={`hidden sm:block w-16 md:w-24 h-0.5 mx-2 ${
                        i < step ? "bg-blue-600" : "bg-gray-200"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
          <p className="text-center text-sm text-gray-500">
            Step {step + 1} of {STEPS.length}: {STEPS[step].title}
          </p>
        </div>

        {/* Step Content */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="text-2xl">{STEPS[step].title}</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Step 0: Destination */}
            {step === 0 && (
              <div className="space-y-6">
                <div className="space-y-2">
                  <label htmlFor="origin" className="text-sm font-medium text-gray-700">
                    Where are you starting from?
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      className="pl-10"
                      placeholder="e.g., New York, USA"
                      id="origin" maxLength={200} value={origin}
                      onChange={(e) => setOrigin(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label htmlFor="destination" className="text-sm font-medium text-gray-700">
                    Where do you want to go?
                  </label>
                  <div className="relative">
                    <Plane className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      className="pl-10"
                      placeholder="e.g., Tokyo, Japan"
                      id="destination" maxLength={200} value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 1: Dates & Travelers */}
            {step === 1 && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label htmlFor="startDate" className="text-sm font-medium text-gray-700">
                      Start Date
                    </label>
                    <Input
                      type="date"
                      id="startDate" value={startDate}
                      onInput={(e) => setStartDate(e.currentTarget.value)}
                      min={today}
                    />
                  </div>
                  <div className="space-y-2">
                    <label htmlFor="endDate" className="text-sm font-medium text-gray-700">
                      End Date
                    </label>
                    <Input
                      type="date"
                      id="endDate" value={endDate}
                      onInput={(e) => setEndDate(e.currentTarget.value)}
                      min={startDate || today}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">
                    Number of Travelers
                  </label>
                  <div className="flex items-center gap-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setNumTravelers(Math.max(1, numTravelers - 1))
                      }
                      aria-label="Fewer travelers" disabled={numTravelers <= 1}
                    >
                      -
                    </Button>
                    <div className="flex items-center gap-2">
                      <Users className="h-5 w-5 text-gray-500" />
                      <span className="text-xl font-semibold w-8 text-center">
                        {numTravelers}
                      </span>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setNumTravelers(Math.min(20, numTravelers + 1))
                      }
                      aria-label="More travelers" disabled={numTravelers >= 20}
                    >
                      +
                    </Button>
                  </div>
                </div>
                {startDate && endDate && (endDate < startDate || (Date.parse(endDate) - Date.parse(startDate)) / 86400000 >= 30) && (
                  <p className="text-sm text-red-500">
                    Choose 1 to 30 days, with end date on or after start date
                  </p>
                )}
              </div>
            )}

            {/* Step 2: Budget & Style */}
            {step === 2 && (
              <div className="space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-2 space-y-2">
                    <label htmlFor="budgetAmount" className="text-sm font-medium text-gray-700">
                      Total Budget
                    </label>
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        type="number"
                        className="pl-10"
                        placeholder="1000"
                        id="budgetAmount" value={budgetAmount || ""}
                        onChange={(e) =>
                          setBudgetAmount(parseFloat(e.target.value) || 0)
                        }
                        min={0}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label htmlFor="budgetCurrency" className="text-sm font-medium text-gray-700">
                      Currency
                    </label>
                    <select
                      className="flex h-10 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm"
                      id="budgetCurrency" value={budgetCurrency}
                      onChange={(e) => setBudgetCurrency(e.target.value)}
                    >
                      {CURRENCIES.map((c) => (
                        <option key={c.code} value={c.code}>
                          {c.code} ({c.symbol})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="text-sm font-medium text-gray-700">
                    Travel Style
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {TRAVEL_STYLES.map((style) => (
                      <button
                        key={style.value}
                        type="button"
                        aria-pressed={travelStyle === style.value}
                        onClick={() => setTravelStyle(style.value)}
                        className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all ${
                          travelStyle === style.value
                            ? "border-blue-600 bg-blue-50 text-blue-700"
                            : "border-gray-200 hover:border-gray-300 text-gray-600"
                        }`}
                      >
                        {styleIcons[style.value]}
                        <span className="font-medium text-sm">
                          {style.label}
                        </span>
                        <span className="text-xs text-center text-gray-500">
                          {style.description}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Preferences */}
            {step === 3 && (
              <div className="space-y-6">
                <CardDescription>
                  Select the types of experiences you enjoy
                </CardDescription>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {TRAVEL_PREFERENCES.map((pref) => (
                    <button
                      key={pref}
                      type="button"
                      aria-pressed={preferences.includes(pref)}
                      onClick={() => togglePreference(pref)}
                      className={`px-4 py-3 rounded-lg border-2 text-sm font-medium transition-all ${
                        preferences.includes(pref)
                          ? "border-blue-600 bg-blue-50 text-blue-700"
                          : "border-gray-200 hover:border-gray-300 text-gray-600"
                      }`}
                    >
                      {pref}
                    </button>
                  ))}
                </div>
                <div className="space-y-2">
                  <label htmlFor="additionalNotes" className="text-sm font-medium text-gray-700">
                    Additional Notes (optional)
                  </label>
                  <textarea
                    className="flex min-h-[80px] w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Any special requirements, dietary needs, accessibility needs..."
                    id="additionalNotes" maxLength={4000} value={additionalNotes}
                    onChange={(e) => setAdditionalNotes(e.target.value)}
                  />
                </div>
              </div>
            )}

            {/* Step 4: Review */}
            {step === 4 && (
              <div className="space-y-6">
                <CardDescription>
                  Review your trip details before generating the itinerary
                </CardDescription>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500 uppercase tracking-wide">
                        From
                      </p>
                      <p className="font-medium">{origin}</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500 uppercase tracking-wide">
                        To
                      </p>
                      <p className="font-medium">{destination}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500 uppercase tracking-wide">
                        Dates
                      </p>
                      <p className="font-medium text-sm">
                        {startDate} → {endDate}
                      </p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500 uppercase tracking-wide">
                        Travelers
                      </p>
                      <p className="font-medium">{numTravelers}</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500 uppercase tracking-wide">
                        Budget
                      </p>
                      <p className="font-medium">
                        {budgetAmount.toLocaleString()} {budgetCurrency}
                      </p>
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">
                      Style & Preferences
                    </p>
                    <p className="font-medium capitalize mb-2">{travelStyle}</p>
                    <div className="flex flex-wrap gap-2">
                      {preferences.map((p) => (
                        <span
                          key={p}
                          className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium"
                        >
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                  {additionalNotes && (
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500 uppercase tracking-wide">
                        Notes
                      </p>
                      <p className="text-sm">{additionalNotes}</p>
                    </div>
                  )}
                </div>
                {error && (
                  <div role="alert" className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                    {error}
                  </div>
                )}
              </div>
            )}

            {/* Navigation */}
            <div className="flex justify-between mt-8 pt-6 border-t">
              <Button
                variant="outline"
                onClick={() => setStep(Math.max(0, step - 1))}
                disabled={step === 0 || isSubmitting}
              >
                <ArrowLeft className="mr-2 h-4 w-4" /> Back
              </Button>

              {step < 4 ? (
                <Button
                  onClick={() => setStep(step + 1)}
                  disabled={!canAdvance()}
                >
                  Next <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating Trip...
                    </>
                  ) : (
                    <>
                      <Plane className="mr-2 h-4 w-4" />
                      Create & Generate Itinerary
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
