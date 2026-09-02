"use client";

import {
  ActivityIcon,
  ArrowRightIcon,
  BrainCircuitIcon,
  FilterIcon,
  RadarIcon,
  RocketIcon,
  SparklesIcon,
  TrendingUpIcon,
  UsersIcon,
} from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useAuth } from "@/features/auth/context/auth-context";
import { TrendingTicker } from "@/features/trends/components/trending-ticker";

const PIPELINE_STEPS = [
  {
    icon: RadarIcon,
    label: "Collect",
    description: "RSS sources are polled automatically on a fixed schedule, day and night.",
  },
  {
    icon: FilterIcon,
    label: "Filter",
    description: "Duplicates are stripped and only startup, tech, AI and Africa-relevant signals move forward.",
  },
  {
    icon: BrainCircuitIcon,
    label: "Analyze",
    description: "AI scores momentum, audience fit, lifespan and the strongest content angle.",
  },
  {
    icon: SparklesIcon,
    label: "Deliver",
    description: "You open the dashboard to a ranked view of what matters — ready to turn into content.",
  },
] as const;

const AUDIENCE_LENSES = [
  {
    icon: SparklesIcon,
    label: "Content Creators",
    description: "Hooks, 30s and 60s scripts, captions and remix templates you can shoot today.",
  },
  {
    icon: RocketIcon,
    label: "Founders",
    description: "Where demand is forming, what to build next, and how to position it.",
  },
  {
    icon: TrendingUpIcon,
    label: "Investors",
    description: "Which categories are heating up, and how durable each move looks.",
  },
] as const;

export default function LandingPage() {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <div className="relative flex flex-1 flex-col bg-background text-foreground">
      <div className="dashboard-backdrop" aria-hidden="true" />
      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-border bg-background/95 px-4 py-4 backdrop-blur-[18px] sm:px-8">
        <div className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="flex size-8 items-center justify-center rounded-lg bg-[linear-gradient(135deg,#f97316,#fb923c_55%,#14b8a6)] text-white shadow-[0_0_20px_rgba(249,115,22,0.35)]">
            <ActivityIcon className="size-4" />
          </span>
          AI-Powered Trend Intelligence
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          {!isLoading && isAuthenticated ? (
            <Button asChild size="sm">
              <Link href="/dashboard">
                Go to dashboard <ArrowRightIcon />
              </Link>
            </Button>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/login">Sign in</Link>
              </Button>
              <Button asChild size="sm">
                <Link href="/register">Get started</Link>
              </Button>
            </>
          )}
        </div>
      </header>

      <TrendingTicker />

      <main className="relative z-10 mx-auto w-full max-w-5xl flex-1 px-4 py-16 sm:px-8 sm:py-24">
        <section className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Always-on trend engine
          </p>
          <h1 className="mt-4 text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
            Know what&apos;s <span className="text-primary">rising</span> before the feed
            catches up.
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            We collect trend sources continuously, strip duplicates, keep only what&apos;s
            relevant to startups, tech, AI and Africa, then score each trend for momentum,
            audience fit and lifespan. You just read the ranking — and generate a content
            brief.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <Link href="/register">
                Get started <ArrowRightIcon />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/login">Sign in</Link>
            </Button>
          </div>
        </section>

        <section id="how-it-works" className="mt-20 grid gap-4 scroll-mt-24 sm:grid-cols-2 lg:grid-cols-4">
          {PIPELINE_STEPS.map((step, i) => (
            <Card key={step.label}>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <span className="flex size-10 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <step.icon className="size-4" />
                  </span>
                  <Badge variant="outline" className="font-normal">
                    0{i + 1} · automatic
                  </Badge>
                </div>
                <CardTitle className="mt-2 text-base text-foreground">
                  {step.label}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{step.description}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <section id="who-its-for" className="mt-20 scroll-mt-24">
          <div className="flex items-center gap-2">
            <UsersIcon className="size-5 text-primary" />
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              One trend, three lenses
            </h2>
          </div>
          <p className="mt-2 max-w-2xl text-muted-foreground">
            Every trend is scored separately for each audience, so the same signal reads
            differently depending on who you are — and you can generate content from any
            perspective, regardless of which one the trend scores highest for.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {AUDIENCE_LENSES.map((lens) => (
              <Card key={lens.label} className="h-full">
                <CardHeader>
                  <span className="flex size-10 items-center justify-center rounded-full bg-accent/15 text-accent">
                    <lens.icon className="size-4" />
                  </span>
                  <CardTitle className="mt-2 text-base text-foreground">
                    {lens.label}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{lens.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section className="mt-20 rounded-2xl border border-border bg-card p-8 text-center sm:p-12">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            Nothing here requires you to trigger a run.
          </h2>
          <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
            Collection, deduplication, filtering and scoring all happen automatically in the
            background. Open the dashboard and the intelligence is already there.
          </p>
          <Button asChild size="lg" className="mt-6">
            <Link href="/register">
              Get started <ArrowRightIcon />
            </Link>
          </Button>
        </section>
      </main>

      <footer className="relative z-10 mt-8 bg-slate-950 px-4 py-12 text-slate-300 sm:px-8 sm:py-16">
        <div className="mx-auto grid w-full max-w-5xl gap-10 sm:grid-cols-2 lg:grid-cols-[1.6fr_1fr_1fr_1fr]">
          <div className="max-w-xs">
            <div className="flex items-center gap-2 font-semibold tracking-tight text-white">
              <span className="flex size-8 items-center justify-center rounded-lg bg-[linear-gradient(135deg,#f97316,#fb923c_55%,#14b8a6)] text-white">
                <ActivityIcon className="size-4" />
              </span>
              Kuzana
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-400">
              Find the conversations worth acting on, then turn them into a clear next move.
            </p>
          </div>

          <nav aria-label="Product links">
            <h2 className="text-sm font-medium text-white">Product</h2>
            <ul className="mt-4 space-y-3 text-sm">
              <li><Link className="transition-colors hover:text-white" href="#how-it-works">How it works</Link></li>
              <li><Link className="transition-colors hover:text-white" href="/trends">Trend intelligence</Link></li>
              <li><Link className="transition-colors hover:text-white" href="/content">Content Studio</Link></li>
            </ul>
          </nav>

          <nav aria-label="Audience links">
            <h2 className="text-sm font-medium text-white">Built for</h2>
            <ul className="mt-4 space-y-3 text-sm">
              <li><Link className="transition-colors hover:text-white" href="#who-its-for">Founders</Link></li>
              <li><Link className="transition-colors hover:text-white" href="#who-its-for">Investors</Link></li>
              <li><Link className="transition-colors hover:text-white" href="#who-its-for">Content creators</Link></li>
            </ul>
          </nav>

          <nav aria-label="Account links">
            <h2 className="text-sm font-medium text-white">Get started</h2>
            <ul className="mt-4 space-y-3 text-sm">
              <li><Link className="transition-colors hover:text-white" href="/register">Create an account</Link></li>
              <li><Link className="transition-colors hover:text-white" href="/login">Sign in</Link></li>
              <li><span className="text-slate-500">Privacy and terms coming soon</span></li>
            </ul>
          </nav>
        </div>

        <div className="mx-auto mt-12 flex w-full max-w-5xl flex-col gap-3 border-t border-white/10 pt-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 Kuzana. Built for people acting early.</p>
          <p>AI-Powered Trend Intelligence · Built by Foluxnova</p>
        </div>
      </footer>
    </div>
  );
}
