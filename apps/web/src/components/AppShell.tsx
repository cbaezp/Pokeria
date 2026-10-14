"use client";

import type React from "react";
import { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { SectionSubnav } from "@/components/navigation/SectionSubnav";
import { ProfileModal } from "@/components/ProfileModal";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

  return (
    <>
      <Navbar onOpenProfileModal={() => setIsProfileModalOpen(true)} />
      <SectionSubnav />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">{children}</main>
      <footer className="border-t border-slate-200 dark:border-slate-800 py-6 text-center text-xs text-slate-500 dark:text-slate-400">
        Pokeria — Architecture, Infrastructure, and Application Foundation
      </footer>
      <ProfileModal isOpen={isProfileModalOpen} onClose={() => setIsProfileModalOpen(false)} />
    </>
  );
}
