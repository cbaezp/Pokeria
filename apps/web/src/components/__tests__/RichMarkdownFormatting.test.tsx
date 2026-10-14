import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { RichMarkdown } from "@/components/curriculum/RichMarkdown";

describe("RichMarkdown Dynamic UI Formatting & Table Parsing", () => {
  it("dynamically parses and renders markdown tables into semantic HTML tables", () => {
    const rawOutsMarkdown = `
An out is any unseen card remaining in the deck that will improve your hand to a winning holding if dealt.

Standard out counts every poker player must memorize:

| Draw Type | Example | Total Outs | Key Cards |
| :--- | :--- | :---: | ---: |
| **Flush Draw** | Four cards to a suit | **9 outs** | 13 cards of suit - 4 known = 9 remaining |
| **Open-Ended Straight Draw (OESD)** | 8-7 on 6-5-2 | **8 outs** | 4 nines + 4 fours = 8 remaining |
| **Gutshot (Inside Straight)** | 9-7 on 6-5-2 | **4 outs** | 4 eights needed |
| **Two Overcards** | A-K on 9-5-2 | **6 outs** | 3 aces + 3 kings |
| **Set to Full House/Quads** | 3-3 on 9-3-2 | **7 outs on turn** | 1 three + 3 nines + 3 twos |
`;

    const { container } = render(<RichMarkdown content={rawOutsMarkdown} />);

    // Must render a real HTML table
    const table = container.querySelector("table");
    expect(table).not.toBeNull();

    // Verify headers
    const headers = container.querySelectorAll("th");
    expect(headers.length).toBe(4);
    expect(headers[0].textContent).toContain("Draw Type");
    expect(headers[1].textContent).toContain("Example");
    expect(headers[2].textContent).toContain("Total Outs");
    expect(headers[3].textContent).toContain("Key Cards");

    // Verify alignment classes
    expect(headers[0].className).toContain("text-left");
    expect(headers[2].className).toContain("text-center");
    expect(headers[3].className).toContain("text-right");

    // Verify rows
    const rows = container.querySelectorAll("tbody tr");
    expect(rows.length).toBe(5);

    // Verify cell content
    expect(rows[0].textContent).toContain("Flush Draw");
    expect(rows[0].textContent).toContain("9 outs");
    expect(rows[1].textContent).toContain("Open-Ended Straight Draw");

    // CRITICAL: Ensure raw table delimiters like :--- NEVER leak into plain text
    expect(container.textContent).not.toContain(":---");
    expect(container.textContent).not.toContain("| :--- |");
  });

  it("dynamically formats poker card suits with semantic color tokens", () => {
    const content = "Board: A♠ K♥ Q♦ J♣ on the flop";
    const { container } = render(<RichMarkdown content={content} />);

    // Red suits
    const roseSuits = container.querySelectorAll(".text-rose-600");
    expect(roseSuits.length).toBeGreaterThanOrEqual(2); // ♥ and ♦

    // Slate suits
    const slateSuits = container.querySelectorAll(".text-slate-900");
    expect(slateSuits.length).toBeGreaterThanOrEqual(2); // ♠ and ♣
  });

  it("dynamically renders LaTeX formulas and fraction cards without raw syntax leaking", () => {
    const fractionFormula =
      "$$\\text{Pot Odds} = \\frac{\\text{Call Amount}}{\\text{Total Pot After Call}}$$";
    const { container } = render(<RichMarkdown content={fractionFormula} />);

    expect(container.textContent).toContain("Pot Odds =");
    expect(container.textContent).toContain("Call Amount");
    expect(container.textContent).toContain("Total Pot After Call");
    expect(container.textContent).not.toContain("\\frac");
    expect(container.textContent).not.toContain("$$");
  });

  it("dynamically renders code blocks inside styled pre/code containers", () => {
    const codeBlock = "```\nconst odds = call / (pot + call);\nconsole.log(odds);\n```";
    const { container } = render(<RichMarkdown content={codeBlock} />);

    const pre = container.querySelector("pre");
    expect(pre).not.toBeNull();
    const code = container.querySelector("code");
    expect(code).not.toBeNull();
    expect(code?.textContent).toContain("const odds = call / (pot + call);");
  });

  it("dynamically renders blockquotes with distinct callout styling", () => {
    const quote = "> **The Rule of 4:** Multiply your outs by 4 to estimate flop-to-river equity.";
    const { container } = render(<RichMarkdown content={quote} />);

    const bq = container.querySelector("blockquote");
    expect(bq).not.toBeNull();
    expect(bq?.textContent).toContain("The Rule of 4:");
  });

  it("dynamically renders numbered and bulleted lists correctly", () => {
    const listContent = `
1. First step in position
2. Second step calculate pot odds
3. Third step evaluate EV

- Point A
- Point B
`;
    const { container } = render(<RichMarkdown content={listContent} />);

    const ol = container.querySelector("ol");
    expect(ol).not.toBeNull();
    expect(ol?.querySelectorAll("li").length).toBe(3);

    const ul = container.querySelector("ul");
    expect(ul).not.toBeNull();
    expect(ul?.querySelectorAll("li").length).toBe(2);
  });

  it("renders poker math lab odds and probabilities without malformation", () => {
    const text = `In poker, odds and probabilities express the exact same mathematical reality in two different languages.

• **Probability (Percentage)**: The fraction of times an event occurs out of *all possible outcomes*. For example, a 25% chance means the event happens 1 out of 4 times total.
• **Odds Against**: The ratio of *unfavorable outcomes* to *favorable outcomes*. If an event happens 1 time and fails 3 times, the odds against are **3 to 1 (3:1)**.

Poker players frequently switch between odds and percentages when comparing pot sizes to card probabilities.`;

    const { container } = render(<RichMarkdown content={text} />);

    // 1. Must render paragraphs for intro and conclusion
    const paragraphs = container.querySelectorAll("p");
    expect(paragraphs.length).toBe(2);
    expect(paragraphs[0].textContent).toBe(
      "In poker, odds and probabilities express the exact same mathematical reality in two different languages.",
    );
    expect(paragraphs[1].textContent).toBe(
      "Poker players frequently switch between odds and percentages when comparing pot sizes to card probabilities.",
    );

    // 2. Must render a real unordered list with 2 items
    const ul = container.querySelector("ul");
    expect(ul).not.toBeNull();
    const listItems = container.querySelectorAll("li");
    expect(listItems.length).toBe(2);

    // 3. Bold text elements must be rendered with <strong> tags, not raw asterisks
    const strongs = Array.from(container.querySelectorAll("strong")).map((s) => s.textContent);
    expect(strongs).toContain("Probability (Percentage)");
    expect(strongs).toContain("Odds Against");
    expect(strongs).toContain("3 to 1 (3:1)");

    // 4. Italic text elements must be rendered with <em> tags, not raw asterisks
    const italics = Array.from(container.querySelectorAll("em")).map((e) => e.textContent);
    expect(italics).toContain("all possible outcomes");
    expect(italics).toContain("unfavorable outcomes");
    expect(italics).toContain("favorable outcomes");

    // 5. CRITICAL: Container text must NEVER contain raw unparsed asterisks
    expect(container.textContent).not.toContain("**Probability");
    expect(container.textContent).not.toContain("**Odds");
    expect(container.textContent).not.toContain("*all possible");
  });
});
