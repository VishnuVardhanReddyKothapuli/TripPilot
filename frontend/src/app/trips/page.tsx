"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Trip } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  MapPin,
  Calendar,
  DollarSign,
  Plus,
  Loader2,
  Plane,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";

function TripCard({ trip }: { trip: Trip }) {
  const statusColors: Record<string, string> = {
    draft: "bg-gray-100 text-gray-700",
    planning: "bg-blue-100 text-blue-700",
    generated: "bg-green-100 text-green-700",
    error: "bg-red-100 text-red-700",
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg">{trip.title}</CardTitle>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              statusColors[trip.status] || statusColors.draft
            }`}
          >
            {trip.status}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-gray-400" />
            <span>
              {trip.origin} → {trip.destination}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <span>
              {trip.start_date} → {trip.end_date}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-gray-400" />
            <span>
              {trip.budget_amount.toLocaleString()} {trip.budget_currency} ·{" "}
              <span className="capitalize">{trip.travel_style}</span>
            </span>
          </div>
        </div>

        {trip.preferences?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {trip.preferences.slice(0, 4).map((p) => (
              <span
                key={p}
                className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs"
              >
                {p}
              </span>
            ))}
            {trip.preferences.length > 4 && (
              <span className="px-2 py-0.5 bg-gray-50 text-gray-500 rounded text-xs">
                +{trip.preferences.length - 4} more
              </span>
            )}
          </div>
        )}

        <div className="mt-4 pt-3 border-t">
          <Button asChild variant="outline" size="sm" className="w-full"><Link href={`/trips/${trip.id}`}>
              Continue Planning <ArrowRight className="ml-2 h-3 w-3" />
            </Link></Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function TripsPage() {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function loadTrips() {
      setLoading(true);
      setError("");
      try {
        const response = await api.getTrips(page * 20);
        if (cancelled) return;
        setTotal(response.total);
        setTrips(response.items);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load trips");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadTrips();
    return () => { cancelled = true; };
  }, [page, retry]);

  return (
    <div className="container mx-auto py-10 px-4 max-w-6xl">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight">My Trips</h1>
        <Button asChild><Link href="/trips/new">
            <Plus className="mr-2 h-4 w-4" /> New Trip
          </Link></Button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      )}

      {error && (
        <div role="alert" className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 mb-6">
          {error}
          <div className="flex gap-4 mt-2"><Button variant="outline" onClick={() => setRetry(retry + 1)}>Retry</Button><Link href="/settings">Open Settings</Link></div>
        </div>
      )}

      {!loading && !error && trips.length === 0 && (
        <div className="text-center py-20 border-2 border-dashed rounded-lg">
          <Plane className="mx-auto h-12 w-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No trips yet
          </h3>
          <p className="text-gray-500 mb-6">
            Start planning your first adventure!
          </p>
          <Button asChild><Link href="/trips/new">
              <Plus className="mr-2 h-4 w-4" /> Create Your First Trip
            </Link></Button>
        </div>
      )}

      {!loading && !error && trips.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {trips.map((trip) => (
            <TripCard key={trip.id} trip={trip} />
          ))}
        </div>
      )}
      {total > 20 && <nav aria-label="Trip pages" className="flex justify-between mt-6">
        <Button variant="outline" disabled={loading || page === 0} onClick={() => setPage(page - 1)}>Previous</Button>
        <span>Page {page + 1} of {Math.ceil(total / 20)}</span>
        <Button variant="outline" disabled={loading || (page + 1) * 20 >= total} onClick={() => setPage(page + 1)}>Next</Button>
      </nav>}
    </div>
  );
}
