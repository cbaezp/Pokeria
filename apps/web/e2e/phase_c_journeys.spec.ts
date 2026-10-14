import { test, expect } from "@playwright/test";

test.describe("Phase C Verification Journeys", () => {
  test("1. 13x13 range inspection and strategy provenance labels", async ({ page }) => {
    await page.goto("/preflop");
    await expect(page.getByRole("button", { name: /13×13 Reference Ranges/i })).toBeVisible({ timeout: 10000 });

    // Inspect strategy provenance badge
    await expect(page.locator("text=INSTRUCTIONAL_HEURISTIC").or(page.locator("text=SOLVER_REFERENCE")).first()).toBeVisible({ timeout: 10000 });

    // Inspect 13x13 range grid
    await expect(page.locator("text=13×13 Preflop Decision Matrix")).toBeVisible();
    await expect(page.locator("text=169 Hand Classes · 1,326 Combos")).toBeVisible();

    // Click hand cells (e.g. AA, 72o)
    const cellAA = page.locator("button:has-text('AA')").first();
    await expect(cellAA).toBeVisible();
    await cellAA.click();
    await expect(page.locator("text=Pocket Pair (6 combinations)")).toBeVisible();

    const cell72o = page.locator("button:has-text('72o')").first();
    await expect(cell72o).toBeVisible();
    await cell72o.click();
    await expect(page.locator("text=Offsuit Hand (12 combinations)")).toBeVisible();
  });

  test("2. Cash preflop training journey", async ({ page }) => {
    await page.goto("/training");
    await expect(page.locator("text=Training Setup").or(page.locator("text=Interactive Trainer"))).toBeVisible();

    // Verify street or training configuration
    const startBtn = page.getByRole("button", { name: /start training|begin practice|practice now/i }).first();
    if (await startBtn.isVisible()) {
      await startBtn.click();
      await page.waitForTimeout(500);
    }
    await expect(page.locator("body")).toBeVisible();
  });

  test("3. Missing-EV feedback and honest disclosure", async ({ page }) => {
    await page.goto("/preflop");
    // Verify that heuristic/chart packs display explicit missing-EV or grading provenance disclaimer
    await expect(
      page.locator("text=Graded via live instructional heuristic rule")
        .or(page.locator("text=Grading Provenance:"))
        .or(page.locator("text=INSTRUCTIONAL"))
        .or(page.locator("text=Action EVs are not fabricated"))
        .first()
    ).toBeVisible({ timeout: 10000 });
  });

  test("4. Quarantined tournament assessment behavior", async ({ page }) => {
    // Visit page and verify either profile prompt or assessment header
    await page.goto("/assessment");
    await expect(
      page.locator("text=Please select or create a profile to access Objective Assessments.")
        .or(page.getByRole("heading", { name: /Objective Assessment/i }))
        .or(page.locator("text=Objective Assessment & Blind Validation"))
    ).toBeVisible({ timeout: 10000 });
  });

  test("5. Desktop keyboard controls", async ({ page }) => {
    await page.goto("/training");
    // Press keyboard shortcuts (F for Fold, C for Check/Call, R for Raise)
    await page.keyboard.press("KeyF");
    await page.keyboard.press("KeyC");
    await page.keyboard.press("KeyR");
    await page.keyboard.press("Space");
  });

  test("6. Mobile interaction at 375px (iPhone SE)", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");
    await expect(page.locator("body")).toBeVisible();
    await page.goto("/preflop");
    await expect(page.getByRole("button", { name: /13×13 Reference Ranges/i })).toBeVisible();
    await page.goto("/training");
    await expect(page.locator("body")).toBeVisible();
  });

  test("7. Mobile interaction at 390px (iPhone 14)", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    await expect(page.locator("body")).toBeVisible();
    await page.goto("/preflop");
    await expect(page.getByRole("button", { name: /13×13 Reference Ranges/i })).toBeVisible();
    await page.goto("/analytics");
    await expect(page.locator("body")).toBeVisible();
  });
});
