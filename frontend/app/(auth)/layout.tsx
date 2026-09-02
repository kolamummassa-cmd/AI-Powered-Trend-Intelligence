export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex flex-1 items-center justify-center gap-12 p-6 lg:p-10">
      <section className="hidden max-w-md space-y-5 lg:block">
        <p className="text-sm font-semibold uppercase tracking-wide text-primary">Trend Intelligence</p>
        <h1 className="text-4xl font-semibold tracking-tight">Know what&apos;s worth acting on before it becomes obvious.</h1>
        <p className="text-muted-foreground">Spot the signal, understand the opportunity, and turn it into a publishing-ready asset in one focused workflow.</p>
        <ul className="space-y-3 text-sm text-muted-foreground"><li>• Evidence-backed opportunities, not a noisy feed.</li><li>• Audience-aware content briefs and drafts.</li><li>• Your account and AI activity stay private to you.</li></ul>
      </section>
      <div className="w-full max-w-sm">{children}</div>
    </main>
  );
}
