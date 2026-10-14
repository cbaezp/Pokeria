export type Position = "UTG" | "UTG+1" | "UTG+2" | "LJ" | "HJ" | "CO" | "BTN" | "SB";

export interface RangeProvenanceMetadata {
  referenceId: string;
  referenceVersion: string;
  gameFormat: string;
  tableSize: string;
  effectiveStackBb: number;
  blindsBb: { sb: number; bb: number; ante: number };
  rakeStructure: string;
  openSizingBb: Record<Position, number>;
  provenanceType: "INSTRUCTIONAL_HEURISTIC";
  provenanceLabel: string;
  isVerifiedSolverProof: boolean;
  disclaimer: string;
}

export const PREFLOP_PROVENANCE_METADATA: RangeProvenanceMetadata = {
  referenceId: "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX",
  referenceVersion: "v1.1-curated",
  gameFormat: "6-Max No-Limit Texas Hold'em Cash",
  tableSize: "6-Max (UTG, HJ, CO, BTN, SB, BB)",
  effectiveStackBb: 100,
  blindsBb: { sb: 0.5, bb: 1.0, ante: 0.0 },
  rakeStructure: "5.0% with 3.0 BB Cap (No Flop, No Drop)",
  openSizingBb: {
    UTG: 2.5,
    "UTG+1": 2.5,
    "UTG+2": 2.5,
    LJ: 2.5,
    HJ: 2.5,
    CO: 2.5,
    BTN: 2.5,
    SB: 3.0,
  },
  provenanceType: "INSTRUCTIONAL_HEURISTIC",
  provenanceLabel: "Instructional Preflop Benchmark (Curated Heuristic)",
  isVerifiedSolverProof: false,
  disclaimer:
    "This preflop reference is a curated pedagogical heuristic reflecting standard 100bb 6-max cash game theory. It is NOT an authenticated raw GTO solver convergence proof (Pokeria's embedded Discounted CFR solver runs postflop solutions). Action frequencies illustrate standard raise/fold mixing under raked cash conditions. Note: In unconstrained equilibrium play, Small Blind strategy incorporates significant open-limping (completing the blind); this pedagogical chart focuses on the pure Raise-First-In vs Fold drill model.",
};

export interface PositionRangeData {
  position: Position;
  name: string;
  fullName: string;
  openSizingBb: number;
  strategicStyle: string;
  color: string;
  badgeBg: string;
  badgeBorder: string;
  badgeText: string;
  // Frequencies for all non-zero opened hand classes
  frequencies: Record<string, number>;
  // Weighted frequency combos (actual solver expectation)
  weightedCombos: number;
  weightedOpenPct: string;
  // Simplified strategy combos (hands with freq >= 0.50)
  simplifiedCombos: number;
  simplifiedOpenPct: string;
  // Unweighted total combos (any hand with non-zero raise)
  unweightedCombos: number;
  unweightedOpenPct: string;
  // Default displayed statistics
  combos: number;
  openPct: string;
  // Hand sets
  hands: Set<string>; // non-zero raise hands
  simplifiedHands: Set<string>; // freq >= 0.5
  pureHands: Set<string>; // freq === 1.0
  mixedHands: Set<string>; // 0 < freq < 1.0
}

export const getCombosForCode = (code: string): number => {
  if (code.length === 2) return 6;
  if (code.endsWith("s")) return 4;
  return 12;
};

// 1. UTG Benchmark (34 classes, 155.0 weighted combos, 196 unweighted, 162 simplified)
const UTG_FREQUENCIES: Record<string, number> = {
  AA: 1.0,
  KK: 1.0,
  QQ: 1.0,
  JJ: 1.0,
  TT: 1.0,
  "99": 1.0,
  "88": 1.0,
  "77": 1.0,
  "66": 0.5,
  "55": 0.2,
  AKs: 1.0,
  AQs: 1.0,
  AJs: 1.0,
  ATs: 1.0,
  A5s: 0.6,
  A4s: 0.5,
  A3s: 0.3,
  A2s: 0.2,
  AKo: 1.0,
  AQo: 1.0,
  AJo: 0.8,
  ATo: 0.2,
  KQs: 1.0,
  KJs: 1.0,
  KTs: 1.0,
  QJs: 1.0,
  QTs: 1.0,
  JTs: 1.0,
  KQo: 0.8,
  T9s: 0.9,
  "98s": 0.8,
  "87s": 0.5,
  "76s": 0.3,
  "65s": 0.2,
};

// 1b. UTG+1 Benchmark (39 classes, ~175.2 weighted combos)
const UTG1_FREQUENCIES: Record<string, number> = {
  ...UTG_FREQUENCIES,
  "66": 0.8,
  "55": 0.4,
  A5s: 0.8,
  A4s: 0.7,
  A3s: 0.4,
  AJo: 1.0,
  ATo: 0.4,
  KQo: 1.0,
  KJo: 0.3,
  K9s: 0.4,
  Q9s: 0.3,
  J9s: 0.3,
  T9s: 1.0,
  "98s": 1.0,
  "87s": 0.7,
  "76s": 0.5,
  "65s": 0.3,
};

// 1c. UTG+2 Benchmark (44 classes, ~198.8 weighted combos)
const UTG2_FREQUENCIES: Record<string, number> = {
  ...UTG1_FREQUENCIES,
  "66": 1.0,
  "55": 0.6,
  "44": 0.3,
  A9s: 0.8,
  A8s: 0.4,
  A5s: 1.0,
  A4s: 0.9,
  A3s: 0.5,
  A2s: 0.3,
  ATo: 0.6,
  A9o: 0.1,
  K9s: 0.6,
  Q9s: 0.5,
  J9s: 0.5,
  T8s: 0.3,
  KJo: 0.5,
  QJo: 0.3,
  "87s": 0.9,
  "76s": 0.6,
  "65s": 0.5,
  "54s": 0.2,
};

// 1d. LJ Benchmark (47 classes, ~216.4 weighted combos)
const LJ_FREQUENCIES: Record<string, number> = {
  ...UTG2_FREQUENCIES,
  "55": 0.8,
  "44": 0.4,
  "33": 0.2,
  A9s: 1.0,
  A8s: 0.6,
  A7s: 0.3,
  A6s: 0.2,
  A4s: 1.0,
  A3s: 0.6,
  A2s: 0.4,
  ATo: 0.7,
  K9s: 0.7,
  Q9s: 0.6,
  J9s: 0.7,
  T8s: 0.5,
  KJo: 0.6,
  QJo: 0.4,
  "87s": 1.0,
  "76s": 0.7,
  "65s": 0.6,
  "54s": 0.3,
};

// 2. HJ / Middle Position Benchmark (49 classes, 230.8 weighted combos, 286 unweighted, 254 simplified)
const HJ_FREQUENCIES: Record<string, number> = {
  ...UTG_FREQUENCIES,
  "66": 1.0,
  "55": 0.8,
  "44": 0.5,
  "33": 0.3,
  "22": 0.2,
  A9s: 1.0,
  A8s: 0.8,
  A7s: 0.5,
  A6s: 0.4,
  A5s: 1.0,
  A4s: 1.0,
  A3s: 0.6,
  A2s: 0.5,
  AJo: 1.0,
  ATo: 0.7,
  A9o: 0.2,
  K9s: 0.8,
  Q9s: 0.7,
  J9s: 0.8,
  T8s: 0.6,
  KQo: 1.0,
  KJo: 0.7,
  QJo: 0.5,
  "87s": 1.0,
  "76s": 0.8,
  "65s": 0.6,
  "54s": 0.4,
};

// 3. CO Benchmark (66 classes, 336.8 weighted combos, 394 unweighted, 370 simplified)
const CO_FREQUENCIES: Record<string, number> = {
  ...HJ_FREQUENCIES,
  "55": 1.0,
  "44": 1.0,
  "33": 0.8,
  "22": 0.8,
  A8s: 1.0,
  A7s: 1.0,
  A6s: 1.0,
  A3s: 1.0,
  A2s: 1.0,
  ATo: 1.0,
  A9o: 0.7,
  A8o: 0.5,
  A7o: 0.2,
  K8s: 1.0,
  K7s: 0.8,
  K6s: 0.6,
  K5s: 0.5,
  K4s: 0.4,
  Q8s: 0.9,
  Q7s: 0.5,
  Q6s: 0.3,
  J8s: 0.8,
  T8s: 1.0,
  "97s": 0.8,
  "86s": 0.6,
  "75s": 0.5,
  KJo: 1.0,
  KTo: 0.8,
  QJo: 1.0,
  QTo: 0.7,
  JTo: 0.7,
};

// 4. BTN Benchmark (100 classes, 558.4 weighted combos, 658 unweighted, 646 simplified)
const BTN_FREQUENCIES: Record<string, number> = {
  ...CO_FREQUENCIES,
  "33": 1.0,
  "22": 1.0,
  A9o: 1.0,
  A8o: 1.0,
  A7o: 1.0,
  A6o: 0.8,
  A5o: 0.8,
  A4o: 0.7,
  A3o: 0.6,
  A2o: 0.5,
  K5s: 1.0,
  K4s: 1.0,
  K3s: 0.9,
  K2s: 0.9,
  Q6s: 1.0,
  Q5s: 0.9,
  Q4s: 0.8,
  Q3s: 0.7,
  Q2s: 0.7,
  J7s: 1.0,
  J6s: 0.8,
  J5s: 0.7,
  J4s: 0.5,
  T7s: 0.9,
  T6s: 0.7,
  "96s": 0.7,
  "85s": 0.6,
  "74s": 0.5,
  "64s": 0.5,
  "53s": 0.4,
  "43s": 0.3,
  KTo: 1.0,
  K9o: 0.9,
  K8o: 0.7,
  K7o: 0.5,
  QTo: 1.0,
  Q9o: 0.9,
  Q8o: 0.7,
  JTo: 1.0,
  J9o: 0.8,
  J8o: 0.6,
  T9o: 0.8,
  T8o: 0.6,
  "98o": 0.7,
  "87o": 0.5,
};

// 5. SB Benchmark (86 classes, 466.8 weighted combos, 570 unweighted, 530 simplified)
const SB_FREQUENCIES: Record<string, number> = {
  ...CO_FREQUENCIES,
  "33": 1.0,
  "22": 1.0,
  A9o: 1.0,
  A8o: 0.8,
  A7o: 0.6,
  A6o: 0.5,
  A5o: 0.6,
  A4o: 0.5,
  A3o: 0.4,
  A2o: 0.3,
  K6s: 1.0,
  K5s: 1.0,
  K4s: 0.8,
  K3s: 0.7,
  K2s: 0.6,
  Q6s: 0.8,
  Q5s: 0.7,
  Q4s: 0.6,
  J7s: 0.8,
  T7s: 0.7,
  "96s": 0.6,
  "85s": 0.5,
  KTo: 1.0,
  K9o: 0.8,
  K8o: 0.5,
  QTo: 1.0,
  Q9o: 0.7,
  Q8o: 0.4,
  JTo: 1.0,
  J9o: 0.6,
  T9o: 0.7,
  "98o": 0.5,
};

const buildPositionData = (
  position: Position,
  name: string,
  fullName: string,
  openSizingBb: number,
  strategicStyle: string,
  color: string,
  badgeBg: string,
  badgeBorder: string,
  badgeText: string,
  frequencies: Record<string, number>,
): PositionRangeData => {
  const allHands = new Set(Object.keys(frequencies));
  const simplifiedHands = new Set(
    Object.entries(frequencies)
      .filter(([, f]) => f >= 0.5)
      .map(([h]) => h),
  );
  const pureHands = new Set(
    Object.entries(frequencies)
      .filter(([, f]) => f === 1.0)
      .map(([h]) => h),
  );
  const mixedHands = new Set(
    Object.entries(frequencies)
      .filter(([, f]) => f > 0 && f < 1.0)
      .map(([h]) => h),
  );

  let weightedCombos = 0;
  let unweightedCombos = 0;
  let simplifiedCombos = 0;

  for (const [hand, freq] of Object.entries(frequencies)) {
    const c = getCombosForCode(hand);
    weightedCombos += c * freq;
    unweightedCombos += c;
    if (freq >= 0.5) {
      simplifiedCombos += c;
    }
  }

  const weightedRound = Math.round(weightedCombos * 10) / 10;
  const weightedOpenPct = ((weightedRound / 1326) * 100).toFixed(1);
  const simplifiedOpenPct = ((simplifiedCombos / 1326) * 100).toFixed(1);
  const unweightedOpenPct = ((unweightedCombos / 1326) * 100).toFixed(1);

  return {
    position,
    name,
    fullName,
    openSizingBb,
    strategicStyle,
    color,
    badgeBg,
    badgeBorder,
    badgeText,
    frequencies,
    weightedCombos: weightedRound,
    weightedOpenPct,
    simplifiedCombos,
    simplifiedOpenPct,
    unweightedCombos,
    unweightedOpenPct,
    // Displayed statistics: frequency-weighted expectation
    combos: weightedRound,
    openPct: weightedOpenPct,
    hands: allHands,
    simplifiedHands,
    pureHands,
    mixedHands,
  };
};

export const POSITION_DATA: Record<Position, PositionRangeData> = {
  UTG: buildPositionData(
    "UTG",
    "UTG",
    "Under The Gun",
    2.5,
    "Tight & Linear Core",
    "emerald",
    "bg-emerald-500/20",
    "border-emerald-500/30",
    "text-emerald-400",
    UTG_FREQUENCIES,
  ),
  "UTG+1": buildPositionData(
    "UTG+1",
    "UTG+1",
    "Under The Gun +1",
    2.5,
    "Tight Linear Core Expansion",
    "teal",
    "bg-teal-500/20",
    "border-teal-500/30",
    "text-teal-400",
    UTG1_FREQUENCIES,
  ),
  "UTG+2": buildPositionData(
    "UTG+2",
    "UTG+2",
    "Under The Gun +2 (MP1)",
    2.5,
    "Early Middle Position Value",
    "cyan",
    "bg-cyan-500/20",
    "border-cyan-500/30",
    "text-cyan-400",
    UTG2_FREQUENCIES,
  ),
  LJ: buildPositionData(
    "LJ",
    "LJ",
    "Lojack (Middle Position 2)",
    2.5,
    "Linear Value Transition",
    "blue",
    "bg-blue-500/20",
    "border-blue-500/30",
    "text-blue-400",
    LJ_FREQUENCIES,
  ),
  HJ: buildPositionData(
    "HJ",
    "HJ",
    "Hijack (Middle Position)",
    2.5,
    "Linear Value Expansion",
    "indigo",
    "bg-indigo-500/20",
    "border-indigo-500/30",
    "text-indigo-400",
    HJ_FREQUENCIES,
  ),
  CO: buildPositionData(
    "CO",
    "CO",
    "Cutoff",
    2.5,
    "Expanded Value & Playability",
    "violet",
    "bg-violet-500/20",
    "border-violet-500/30",
    "text-violet-400",
    CO_FREQUENCIES,
  ),
  BTN: buildPositionData(
    "BTN",
    "BTN",
    "Button",
    2.5,
    "Wide Steal & Speculative",
    "sky",
    "bg-sky-500/20",
    "border-sky-500/30",
    "text-sky-400",
    BTN_FREQUENCIES,
  ),
  SB: buildPositionData(
    "SB",
    "SB",
    "Small Blind",
    3.0,
    "Polarized vs BB Defense",
    "purple",
    "bg-purple-500/20",
    "border-purple-500/30",
    "text-purple-400",
    SB_FREQUENCIES,
  ),
};

export const SIX_MAX_POSITIONS: Position[] = ["UTG", "HJ", "CO", "BTN", "SB"];
export const EIGHT_MAX_POSITIONS: Position[] = ["UTG", "UTG+1", "LJ", "HJ", "CO", "BTN", "SB"];
export const NINE_MAX_POSITIONS: Position[] = [
  "UTG",
  "UTG+1",
  "UTG+2",
  "LJ",
  "HJ",
  "CO",
  "BTN",
  "SB",
];
export const POSITION_ORDER: Position[] = NINE_MAX_POSITIONS;
export const POSITION_RANGES = POSITION_DATA;

// Export preset hands for backward compatibility (using all open hands)
export const UTG_PRESET_HANDS = POSITION_DATA.UTG.hands;
export const UTG1_PRESET_HANDS = POSITION_DATA["UTG+1"].hands;
export const UTG2_PRESET_HANDS = POSITION_DATA["UTG+2"].hands;
export const LJ_PRESET_HANDS = POSITION_DATA.LJ.hands;
export const HJ_PRESET_HANDS = POSITION_DATA.HJ.hands;
export const CO_PRESET_HANDS = POSITION_DATA.CO.hands;
export const BTN_PRESET_HANDS = POSITION_DATA.BTN.hands;
export const SB_PRESET_HANDS = POSITION_DATA.SB.hands;
