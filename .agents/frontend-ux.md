# Frontend Architecture, UX & Component Guide

> **Target Directory**: `apps/web/`
> **Universal Directive**: [AGENTS.md](../AGENTS.md)

---

## 1. Tech Stack & Styling Principles

- **Framework**: Next.js 15 (App Router) + React 19 + TypeScript 5.7.
- **Styling**: Tailwind CSS with sleek dark-mode slate theme.
- **Icons**: Lucide React (`lucide-react`).
- **Formatting & Linting**: Biome (configured via root [`biome.json`](../biome.json)).
- **Unit Testing**: Vitest + React Testing Library + JSDOM (`apps/web/vitest.config.ts`).

---

## 2. Design System & Aesthetics

1. **Color Palette**:
   - Backgrounds: Dark slate tones (`bg-slate-950`, `bg-slate-900`, `bg-slate-800`).
   - Primary Strategic Accents:
     - Fold: Soft rose / red (`text-rose-400`, `bg-rose-500/10`).
     - Check / Call: Emerald green (`text-emerald-400`, `bg-emerald-500/10`).
     - Raise / Bet: Amber orange (`text-amber-400`, `bg-amber-500/10`).
     - All-In: Purple / violet (`text-purple-400`, `bg-purple-500/10`).
2. **Four-Color Card Deck**:
   - Spades ($\spades$): Dark slate / black.
   - Hearts ($\heartsuit$): Bright red (`text-red-500`).
   - Diamonds ($\diamondsuit$): Cyan blue (`text-blue-400`).
   - Clubs ($\clubsuit$): Forest green (`text-emerald-500`).
3. **Typography**: Inter / Sans font stack with high-contrast tabular figures (`font-mono`) for pot sizes, stack depths, and EV numbers.

---

## 3. Keyboard-First Hotkeys

All interactive poker decision screens must support keyboard shortcuts:
- `F`: Fold
- `C`: Check / Call
- `R`: Raise / Bet
- `A`: All-In
- `1`, `2`, `3`: Preset bet sizing shortcuts (33%, 75%, Pot)
- `Space`: Advance to next hand or continue drill

Always display subtle keyboard hint badges next to action buttons (e.g. `[F]`, `[C]`, `[R]`).

---

## 4. Code Quality & Pre-Commit

Before submitting frontend code:
```bash
# Run Biome fast format and check (<100ms)
npm --prefix apps/web run check
npm --prefix apps/web run format

# Run TypeScript type check
npm --prefix apps/web exec tsc -- --noEmit
```
Never leave unused imports or broken component interfaces.
