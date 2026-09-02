import type { Metadata } from "next";
import { Manrope, Sora } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { Providers } from "./providers";

// Runs before hydration so returning dark-mode users never see a flash
// of the light-mode default while React boots. Mirrors the
// localStorage-only resolution in lib/theme-provider.tsx exactly — light
// is the deliberate default for first-time visitors regardless of OS
// preference, so this deliberately does NOT check
// prefers-color-scheme.
const NO_FLASH_THEME_SCRIPT = `
(function () {
  try {
    var stored = window.localStorage.getItem("trend-intelligence-theme");
    document.documentElement.classList.toggle("dark", stored === "dark");
  } catch (e) {}
})();
`;

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI-Powered Trend Intelligence",
  description:
    "From trend detected to publishable content, in under 30 minutes.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${manrope.variable} ${sora.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <Script id="no-flash-theme" strategy="beforeInteractive">
          {NO_FLASH_THEME_SCRIPT}
        </Script>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
