"use client";

import React from "react";

export interface RichMarkdownProps {
  content: string;
  className?: string;
}

/**
 * Highlights card suits (♥, ♦ in rose and ♠, ♣ in slate) for poker clarity.
 */
function renderTextWithSuits(text: string): React.ReactNode[] {
  const suitRegex = /([♥♦♣♠])/g;
  const parts = text.split(suitRegex);

  return parts.map((part, idx) => {
    if (part === "♥" || part === "♦") {
      return (
        <span key={idx} className="text-rose-600 dark:text-rose-400 font-semibold inline-block">
          {part}
        </span>
      );
    }
    if (part === "♠" || part === "♣") {
      return (
        <span key={idx} className="text-slate-900 dark:text-slate-200 font-semibold inline-block">
          {part}
        </span>
      );
    }
    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

/**
 * Cleans raw LaTeX math tokens into human-readable notation.
 */
export function cleanLatexMath(latex: string): string {
  let cleaned = latex.trim();
  // Strip bounding $$ or $
  if (cleaned.startsWith("$$") && cleaned.endsWith("$$")) {
    cleaned = cleaned.slice(2, -2).trim();
  } else if (cleaned.startsWith("$") && cleaned.endsWith("$")) {
    cleaned = cleaned.slice(1, -1).trim();
  }

  // Combinations \binom{52}{2} -> C(52, 2)
  cleaned = cleaned.replace(/\\binom\{([^}]+)\}\{([^}]+)\}/g, "C($1, $2)");
  // Fractions \frac{A}{B} -> A ÷ B (if inside text)
  cleaned = cleaned.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, "($1) ÷ ($2)");
  // \text{...} -> unwrap
  cleaned = cleaned.replace(/\\text\{([^}]+)\}/g, "$1");
  // LaTeX operators & symbols
  cleaned = cleaned.replace(/\\times/g, "×");
  cleaned = cleaned.replace(/\\cdot/g, "·");
  cleaned = cleaned.replace(/\\sim/g, "≈");
  cleaned = cleaned.replace(/\\%/g, "%");
  cleaned = cleaned.replace(/\\approx/g, "≈");
  cleaned = cleaned.replace(/\\le/g, "≤");
  cleaned = cleaned.replace(/\\leq/g, "≤");
  cleaned = cleaned.replace(/\\ge/g, "≥");
  cleaned = cleaned.replace(/\\geq/g, "≥");
  cleaned = cleaned.replace(/\\to/g, "→");
  cleaned = cleaned.replace(/\\rightarrow/g, "→");
  cleaned = cleaned.replace(/\\pm/g, "±");
  cleaned = cleaned.replace(/\\neq/g, "≠");
  cleaned = cleaned.replace(/\\infty/g, "∞");
  // Clean backslashes
  cleaned = cleaned.replace(/\\/g, "");
  return cleaned.trim();
}

/**
 * Parses fraction formula: e.g. \text{Stack in BB} = \frac{\text{Total Chips}}{\text{Current Big Blind}}
 */
function parseFractionFormula(formula: string): {
  prefix?: string;
  numerator?: string;
  denominator?: string;
  suffix?: string;
} | null {
  let clean = formula.trim();
  if (clean.startsWith("$$") && clean.endsWith("$$")) {
    clean = clean.slice(2, -2).trim();
  }
  const fracMatch = clean.match(/^(.*?)\\frac\{([^}]+)\}\{([^}]+)\}(.*)$/);
  if (!fracMatch) return null;

  return {
    prefix: cleanLatexMath(fracMatch[1]),
    numerator: cleanLatexMath(fracMatch[2]),
    denominator: cleanLatexMath(fracMatch[3]),
    suffix: cleanLatexMath(fracMatch[4]),
  };
}

/**
 * Parses inline formatting:
 * - **bold**
 * - *italic*
 * - `code`
 * - $math$ (LaTeX math formulas)
 * - Card suits (♥, ♦ in red; ♠, ♣ in slate/emerald)
 */
function parseInline(text: string): React.ReactNode[] {
  // Regex to match **bold**, *italic*, `code`, $math$, and plain text
  const regex = /(\*\*(?:[^*]|\*(?!\*))+\*\*|\*[^*]+\*|`[^`]+`|\$[^$]+\$)/g;
  const parts = text.split(regex);

  return parts.map((part, index) => {
    if (!part) return null;
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-bold text-slate-900 dark:text-white">
          {renderTextWithSuits(part.slice(2, -2))}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return (
        <em key={index} className="italic text-slate-600 dark:text-slate-300">
          {renderTextWithSuits(part.slice(1, -1))}
        </em>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={index}
          className="font-mono text-slate-800 dark:text-slate-200 bg-slate-100 dark:bg-slate-800/90 px-1.5 py-0.5 rounded text-[11px] border border-slate-300/80 dark:border-slate-700/60"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    // Inline math $...$
    if (part.startsWith("$") && part.endsWith("$") && part.length > 2) {
      const mathClean = cleanLatexMath(part);
      return (
        <strong key={index} className="font-mono font-bold text-slate-900 dark:text-white">
          {mathClean}
        </strong>
      );
    }
    return <span key={index}>{renderTextWithSuits(part)}</span>;
  });
}

/**
 * Clean semantic Markdown & Formula renderer for Pokeria lessons:
 * Supports headings, ordered lists, bullet lists, blockquotes, math formula cards,
 * GFM-compliant responsive tables, code blocks, horizontal rules, paragraphs, bold/italic/code.
 * Full light mode and dark mode theme compatibility.
 */

function parseTableCells(line: string): string[] {
  let content = line.trim();
  if (content.startsWith("|")) content = content.slice(1);
  if (content.endsWith("|")) content = content.slice(0, -1);
  return content.split("|").map((cell) => cell.trim());
}

function isTableDelimiter(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed.includes("|") && !trimmed.includes("-")) return false;
  const cells = parseTableCells(trimmed);
  if (cells.length === 0) return false;
  return cells.every((cell) => {
    const compact = cell.replace(/\s+/g, "");
    return /^:?-+:?$/.test(compact);
  });
}

function getTableAlignments(delimiterLine: string): ("left" | "center" | "right")[] {
  const cells = parseTableCells(delimiterLine);
  return cells.map((cell) => {
    const compact = cell.replace(/\s+/g, "");
    const left = compact.startsWith(":");
    const right = compact.endsWith(":");
    if (left && right) return "center";
    if (right) return "right";
    return "left";
  });
}

export { parseInline, renderTextWithSuits };

export const RichMarkdown: React.FC<RichMarkdownProps> = ({ content, className = "" }) => {
  if (!content) return null;

  const lines = content.split("\n");
  const blocks: React.ReactNode[] = [];

  let currentList: { type: "ol" | "ul"; items: string[] } | null = null;
  let currentParagraphLines: string[] = [];
  let currentQuoteLines: string[] = [];

  const flushParagraph = () => {
    if (currentParagraphLines.length > 0) {
      const text = currentParagraphLines.join(" ").trim();
      if (text) {
        blocks.push(
          <p
            key={`p-${blocks.length}`}
            className="leading-relaxed text-slate-700 dark:text-slate-200 text-xs sm:text-sm"
          >
            {parseInline(text)}
          </p>,
        );
      }
      currentParagraphLines = [];
    }
  };

  const flushQuote = () => {
    if (currentQuoteLines.length > 0) {
      blocks.push(
        <blockquote
          key={`quote-${blocks.length}`}
          className="my-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/90 border-l-4 border-emerald-500 dark:border-emerald-400 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1 text-xs sm:text-sm text-slate-800 dark:text-slate-200"
        >
          {currentQuoteLines.map((line, qIdx) => (
            <div key={qIdx} className="leading-relaxed">
              {parseInline(line)}
            </div>
          ))}
        </blockquote>,
      );
      currentQuoteLines = [];
    }
  };

  const flushList = () => {
    if (currentList) {
      if (currentList.type === "ol") {
        blocks.push(
          <ol
            key={`ol-${blocks.length}`}
            className="space-y-2.5 my-2.5 text-xs sm:text-sm text-slate-700 dark:text-slate-200"
          >
            {currentList.items.map((item, i) => (
              <li key={i} className="flex items-start gap-2.5">
                <span className="flex-shrink-0 flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-mono text-[11px] font-bold mt-0.5 border border-emerald-500/30 shadow-sm">
                  {i + 1}
                </span>
                <span className="flex-1 leading-relaxed">{parseInline(item)}</span>
              </li>
            ))}
          </ol>,
        );
      } else {
        blocks.push(
          <ul
            key={`ul-${blocks.length}`}
            className="space-y-2.5 my-2.5 text-xs sm:text-sm text-slate-700 dark:text-slate-200"
          >
            {currentList.items.map((item, i) => (
              <li key={i} className="flex items-start gap-2.5">
                <span className="flex-shrink-0 text-emerald-500 dark:text-emerald-400 font-bold select-none text-base leading-tight mt-0.5">
                  •
                </span>
                <span className="flex-1 leading-relaxed">{parseInline(item)}</span>
              </li>
            ))}
          </ul>,
        );
      }
      currentList = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      flushParagraph();
      flushQuote();
      flushList();
      continue;
    }

    // Code block: ``` ... ```
    if (trimmed.startsWith("```")) {
      flushParagraph();
      flushQuote();
      flushList();

      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }

      blocks.push(
        <div
          key={`code-${blocks.length}`}
          className="my-3 overflow-x-auto rounded-xl bg-slate-900 border border-slate-800 text-slate-100 p-3.5 font-mono text-xs shadow-sm"
        >
          <pre>
            <code>{codeLines.join("\n")}</code>
          </pre>
        </div>,
      );
      continue;
    }

    // Horizontal rule: ---, ***, ___
    if (trimmed === "---" || trimmed === "***" || trimmed === "___") {
      flushParagraph();
      flushQuote();
      flushList();
      blocks.push(
        <hr
          key={`hr-${blocks.length}`}
          className="my-4 border-t border-slate-200 dark:border-slate-800"
        />,
      );
      continue;
    }

    // GFM Markdown Table:
    // Header row followed by a delimiter row (:--- | :--- | ...)
    if (trimmed.includes("|") && i + 1 < lines.length && isTableDelimiter(lines[i + 1])) {
      flushParagraph();
      flushQuote();
      flushList();

      const headers = parseTableCells(trimmed);
      const delimiterLine = lines[i + 1];
      const alignments = getTableAlignments(delimiterLine);
      const rows: string[][] = [];

      i += 2; // Advance past header and delimiter lines
      while (i < lines.length) {
        const rowLine = lines[i].trim();
        if (!rowLine || !rowLine.includes("|")) {
          i--; // Let the outer loop process this non-table line
          break;
        }
        rows.push(parseTableCells(rowLine));
        i++;
      }

      blocks.push(
        <div
          key={`table-${blocks.length}`}
          className="my-3 overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm"
        >
          <table className="w-full text-left border-collapse text-xs sm:text-sm">
            <thead>
              <tr className="bg-slate-100/90 dark:bg-slate-800/90 border-b border-slate-200 dark:border-slate-700/80">
                {headers.map((h, colIdx) => {
                  const align = alignments[colIdx] || "left";
                  const alignClass =
                    align === "center"
                      ? "text-center"
                      : align === "right"
                        ? "text-right"
                        : "text-left";
                  return (
                    <th
                      key={colIdx}
                      className={`py-2.5 px-3 sm:px-4 font-bold text-slate-900 dark:text-slate-100 ${alignClass}`}
                    >
                      {parseInline(h)}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200/70 dark:divide-slate-800/70">
              {rows.map((row, rIdx) => (
                <tr
                  key={rIdx}
                  className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors"
                >
                  {row.map((cell, cIdx) => {
                    const align = alignments[cIdx] || "left";
                    const alignClass =
                      align === "center"
                        ? "text-center"
                        : align === "right"
                          ? "text-right"
                          : "text-left";
                    return (
                      <td
                        key={cIdx}
                        className={`py-2.5 px-3 sm:px-4 text-slate-700 dark:text-slate-300 align-top ${alignClass}`}
                      >
                        {parseInline(cell)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    // Mathematical formula block: $$...$$
    if (trimmed.startsWith("$$") && trimmed.endsWith("$$") && trimmed.length > 2) {
      flushParagraph();
      flushQuote();
      flushList();

      const frac = parseFractionFormula(trimmed);
      if (frac) {
        blocks.push(
          <div
            key={`formula-${blocks.length}`}
            className="my-3 p-3.5 sm:p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-center justify-center gap-3 font-mono text-xs sm:text-sm text-slate-900 dark:text-white"
          >
            {frac.prefix && <span className="font-bold">{frac.prefix}</span>}
            <div className="inline-flex flex-col items-center">
              <span className="font-bold border-b-2 border-slate-700 dark:border-slate-300 pb-0.5 px-3 text-center">
                {frac.numerator}
              </span>
              <span className="pt-0.5 px-3 text-center text-slate-700 dark:text-slate-300">
                {frac.denominator}
              </span>
            </div>
            {frac.suffix && <span className="font-bold">{frac.suffix}</span>}
          </div>,
        );
      } else {
        const clean = cleanLatexMath(trimmed);
        blocks.push(
          <div
            key={`formula-${blocks.length}`}
            className="my-3 p-3 sm:p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm text-center font-mono font-bold text-xs sm:text-sm text-slate-900 dark:text-white"
          >
            {clean}
          </div>,
        );
      }
      continue;
    }

    // Blockquote: > ...
    if (trimmed.startsWith("> ")) {
      flushParagraph();
      flushList();
      currentQuoteLines.push(trimmed.slice(2).trim());
      continue;
    } else {
      flushQuote();
    }

    // Headings: ###, ##, #
    if (trimmed.startsWith("### ")) {
      flushParagraph();
      flushList();
      blocks.push(
        <h4
          key={`h4-${blocks.length}`}
          className="text-base font-bold text-slate-900 dark:text-white mt-3 mb-1"
        >
          {parseInline(trimmed.slice(4))}
        </h4>,
      );
      continue;
    }
    if (trimmed.startsWith("## ")) {
      flushParagraph();
      flushList();
      blocks.push(
        <h3
          key={`h3-${blocks.length}`}
          className="text-lg font-bold text-slate-900 dark:text-white mt-4 mb-2"
        >
          {parseInline(trimmed.slice(3))}
        </h3>,
      );
      continue;
    }
    if (trimmed.startsWith("# ")) {
      flushParagraph();
      flushList();
      blocks.push(
        <h2
          key={`h2-${blocks.length}`}
          className="text-xl font-black text-slate-900 dark:text-white mt-4 mb-2"
        >
          {parseInline(trimmed.slice(2))}
        </h2>,
      );
      continue;
    }

    // Numbered list item: e.g. "1. ..." or "2. ..."
    const olMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (olMatch) {
      flushParagraph();
      if (!currentList || currentList.type !== "ol") {
        flushList();
        currentList = { type: "ol", items: [] };
      }
      currentList.items.push(olMatch[2]);
      continue;
    }

    // Bullet list item: e.g. "- ..." or "* ..." or "• ..." or "· ..."
    const ulMatch = trimmed.match(/^[-*•·]\s*(.*)$/);
    if (ulMatch) {
      flushParagraph();
      if (!currentList || currentList.type !== "ul") {
        flushList();
        currentList = { type: "ul", items: [] };
      }
      currentList.items.push(ulMatch[1].trim());
      continue;
    }

    // Regular line in a paragraph
    flushList();
    currentParagraphLines.push(trimmed);
  }

  flushParagraph();
  flushQuote();
  flushList();

  return <div className={`space-y-3 ${className}`}>{blocks}</div>;
};
