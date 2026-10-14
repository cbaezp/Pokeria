import {
  BarChart3,
  BookOpen,
  Brain,
  Calculator,
  Clock,
  Cpu,
  FlaskConical,
  Gamepad2,
  GraduationCap,
  History,
  Layers,
  LayoutDashboard,
  LineChart,
  Network,
  Sparkles,
  Swords,
  Target,
  Zap,
} from "lucide-react";
import type React from "react";

export interface NavSubItem {
  id: string;
  label: string;
  shortLabel: string;
  href: string;
  description: string;
  icon: React.ElementType;
  badge?: string;
}

export interface NavPillar {
  id: "overview" | "learn" | "play" | "progress";
  label: string;
  href: string;
  icon: React.ElementType;
  description: string;
  subItems?: NavSubItem[];
}

export const NAV_PILLARS: NavPillar[] = [
  {
    id: "overview",
    label: "Overview",
    href: "/",
    icon: LayoutDashboard,
    description: "Learning command center, daily recommendations, streak & activity.",
  },
  {
    id: "learn",
    label: "Learn & Train",
    href: "/learn",
    icon: GraduationCap,
    description: "Curriculum lessons, deliberate solver drills, math lab, and theory.",
    subItems: [
      {
        id: "curriculum",
        label: "Guided Learning Path",
        shortLabel: "Learning Path",
        href: "/learn",
        description: "Step-by-step master curriculum from fundamentals to high-stakes solver play.",
        icon: GraduationCap,
        badge: "CORE",
      },
      {
        id: "practice",
        label: "Practice Drills",
        shortLabel: "Drills",
        href: "/practice",
        description:
          "Deliberate preflop and postflop decision drills backed by GTO reference ranges.",
        icon: Swords,
        badge: "DRILLS",
      },
      {
        id: "math-lab",
        label: "Poker Math Lab",
        shortLabel: "Math Lab",
        href: "/math-lab",
        description:
          "Master equity, expected value, mental math speed, and real-hand calculations.",
        icon: Calculator,
        badge: "16 MODULES",
      },
      {
        id: "strategy",
        label: "Strategy Library",
        shortLabel: "Strategy",
        href: "/strategy",
        description: "Searchable poker theory, 13x13 matrices, postflop charts, and formulas.",
        icon: BookOpen,
        badge: "REFERENCE",
      },
      {
        id: "assessment",
        label: "Skill Assessment",
        shortLabel: "Assessment",
        href: "/assessment",
        description:
          "Benchmark your capabilities and diagnose your decision quality under pressure.",
        icon: Target,
        badge: "DIAGNOSTIC",
      },
      {
        id: "skill-map",
        label: "Curriculum Skill Tree",
        shortLabel: "Skill Tree",
        href: "/skill-map",
        description: "Visual dependency graph across 6 core poker competency domains.",
        icon: Network,
      },
    ],
  },
  {
    id: "play",
    label: "Play & Analyze",
    href: "/play",
    icon: Gamepad2,
    description: "Live table copilot, equity simulation, solver trees, and range analysis.",
    subItems: [
      {
        id: "live-helper",
        label: "Live Helper",
        shortLabel: "Live Copilot",
        href: "/live-helper",
        description: "Real-time decision assistant with Guided Copilot and Decision Check modes.",
        icon: FlaskConical,
        badge: "COPILOT",
      },
      {
        id: "simulate",
        label: "Equity Simulator",
        shortLabel: "Simulator",
        href: "/simulate",
        description:
          "Combinatorial and Monte Carlo equity calculation for hands and weighted ranges.",
        icon: Cpu,
        badge: "MONTE CARLO",
      },
      {
        id: "workbench",
        label: "Solver Workbench",
        shortLabel: "Solver",
        href: "/workbench",
        description: "Deep DCFR game trees, action distribution inspector, and strategy packs.",
        icon: Layers,
        badge: "DCFR SOLVER",
      },
      {
        id: "preflop",
        label: "Preflop Ranges",
        shortLabel: "Ranges",
        href: "/preflop",
        description: "Interactive 13x13 opening matrices, 3-bet charts, and Push/Fold solver.",
        icon: Sparkles,
      },
    ],
  },
  {
    id: "progress",
    label: "My Progress",
    href: "/progress",
    icon: BarChart3,
    description: "Performance metrics, hand history, spaced retention, and learner profile.",
    subItems: [
      {
        id: "performance",
        label: "Performance Dashboard",
        shortLabel: "Performance",
        href: "/performance",
        description: "Comprehensive win-rate alignment, position trends, and competency radar.",
        icon: LineChart,
        badge: "ANALYTICS",
      },
      {
        id: "review",
        label: "Hand Review & History",
        shortLabel: "Hand Review",
        href: "/review",
        description: "Replay past sessions, inspect decision regrets, and analyze specific leaks.",
        icon: History,
        badge: "REPLAYER",
      },
      {
        id: "retention",
        label: "Spaced Retention",
        shortLabel: "Retention",
        href: "/retention",
        description: "SM-2 flashcard recall drills for strategic leaks & math formulas.",
        icon: Clock,
        badge: "MEMORY QUEUE",
      },
      {
        id: "learner",
        label: "Learner Profile & Leaks",
        shortLabel: "Learner Profile",
        href: "/learner",
        description: "Empirical Bayes shrinkage model revealing your detected strategic leaks.",
        icon: Brain,
      },
      {
        id: "skill-map",
        label: "Skill Map & Tree",
        shortLabel: "Skill Map",
        href: "/skill-map",
        description:
          "Visual knowledge graph of mastery thresholds, prerequisites, and milestone progression.",
        icon: Network,
        badge: "MASTERY",
      },
      {
        id: "math-progress",
        label: "Math Lab Mastery",
        shortLabel: "Math Mastery",
        href: "/math-lab?tab=overview",
        description:
          "Track equity estimation error (MAE), signed bias, and mental math response times.",
        icon: Zap,
      },
    ],
  },
];

/**
 * Returns which primary navigation pillar is active for a given pathname.
 */
export function getActivePillar(pathname: string): NavPillar {
  if (pathname === "/" || pathname === "/overview" || pathname.startsWith("/overview")) {
    return NAV_PILLARS[0]; // overview
  }

  if (
    pathname.startsWith("/learn") ||
    pathname.startsWith("/practice") ||
    pathname.startsWith("/training") ||
    pathname.startsWith("/math-lab") ||
    pathname.startsWith("/strategy") ||
    pathname.startsWith("/assessment")
  ) {
    return NAV_PILLARS[1]; // learn
  }

  if (
    pathname.startsWith("/play") ||
    pathname.startsWith("/live-helper") ||
    pathname.startsWith("/simulate") ||
    pathname.startsWith("/workbench") ||
    pathname.startsWith("/preflop")
  ) {
    return NAV_PILLARS[2]; // play
  }

  if (
    pathname.startsWith("/progress") ||
    pathname.startsWith("/performance") ||
    pathname.startsWith("/review") ||
    pathname.startsWith("/retention") ||
    pathname.startsWith("/learner") ||
    pathname.startsWith("/skill-map")
  ) {
    return NAV_PILLARS[3]; // progress
  }

  return NAV_PILLARS[0];
}
