import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Map, Plane, Compass, DollarSign, Cloud, Calendar } from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center">
      {/* Hero Section */}
      <section className="w-full py-24 md:py-32 lg:py-48 bg-gradient-to-b from-blue-50 to-white flex flex-col items-center text-center px-4">
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 mb-6">
          Plan Your Perfect Trip with <span className="text-blue-600">AI</span>
        </h1>
        <p className="text-lg md:text-xl text-slate-600 max-w-2xl mb-10">
          Intelligent trip planning that understands your preferences, tracks your budget, and builds personalized itineraries in seconds.
        </p>
        <Button asChild size="lg" className="h-14 px-8 text-lg rounded-full"><Link href="/trips/new">
            <Plane className="mr-2 h-5 w-5" /> Start Planning
          </Link></Button>
      </section>

      {/* Features Section */}
      <section className="w-full max-w-6xl py-16 px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-4">Everything you need for the perfect journey</h2>
          <p className="text-slate-600">Our AI agent handles the heavy lifting so you can focus on the adventure.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <Card>
            <CardHeader>
              <Calendar className="h-10 w-10 text-blue-500 mb-2" />
              <CardTitle>Smart Itineraries</CardTitle>
              <CardDescription>AI-generated day-by-day plans tailored to your exact preferences and travel style.</CardDescription>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader>
              <DollarSign className="h-10 w-10 text-emerald-500 mb-2" />
              <CardTitle>Budget Tracking</CardTitle>
              <CardDescription>Estimated accommodation, meals, local transport, and activity costs for your group. Flight fares are not included.</CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Cloud className="h-10 w-10 text-sky-500 mb-2" />
              <CardTitle>Weather Insights</CardTitle>
              <CardDescription>Available forecasts for the next 16 days to help you pack and plan appropriately.</CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Map className="h-10 w-10 text-indigo-500 mb-2" />
              <CardTitle>Location Details</CardTitle>
              <CardDescription>Explore attraction names and location details alongside your daily itinerary.</CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Compass className="h-10 w-10 text-amber-500 mb-2" />
              <CardTitle>Easy Modifications</CardTitle>
              <CardDescription>Simply tell the AI what you want to change (&quot;Make day 2 more relaxing&quot;) using your connected Ollama model.</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full border-t py-8 mt-12 text-center text-slate-500">
        <p>© {new Date().getFullYear()} TripPilot AI. All rights reserved.</p>
      </footer>
    </div>
  );
}
