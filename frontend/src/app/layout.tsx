import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";


export const metadata: Metadata = {
  title: "TripPilot AI",
  description: "Plan Your Perfect Trip with AI",
};

function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container mx-auto flex min-h-16 flex-wrap gap-3 py-3 items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2">
          <svg
            className="h-7 w-7 text-blue-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
          <span className="text-xl font-bold text-gray-900">
            Trip<span className="text-blue-600">Pilot</span>
          </span>
        </Link>

        <nav className="flex flex-wrap items-center gap-3 sm:gap-6">
          <Link
            href="/"
            className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            Home
          </Link>
          <Link
            href="/trips"
            className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            My Trips
          </Link>
          <Link
            href="/settings"
            className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            Settings
          </Link>
          <Link
            href="/trips/new"
            className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            New Trip
          </Link>
        </nav>
      </div>
    </header>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans">
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
