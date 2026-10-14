import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/AppShell";
import { GameConfigurationProvider } from "@/lib/game-configuration-context";
import { ProfileProvider } from "@/lib/profile-context";
import { ThemeProvider } from "@/lib/theme";

export const metadata: Metadata = {
  title: "Pokeria - Professional Poker Training & Adaptive Mastery",
  description:
    "Professional No-Limit Texas Hold'em deliberate practice, solver strategy library, and adaptive learning platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col">
        <ThemeProvider>
          <ProfileProvider>
            <GameConfigurationProvider>
              <AppShell>{children}</AppShell>
            </GameConfigurationProvider>
          </ProfileProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
