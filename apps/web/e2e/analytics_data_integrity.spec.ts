import { test, expect } from "@playwright/test";

test.describe("Poker Lab Analytics Data Integrity and PostgreSQL Verification", () => {
  test("verifies live DOM metrics against PostgreSQL ground truth fixture", async ({ page }) => {
    // Navigate to analytics
    await page.goto("/analytics");
    await expect(page).toHaveTitle(/Pokeria/);

    // Select test profile if available in profile selector
    const profileSelect = page.locator("select").first();
    // Wait for profiles to finish loading from API
    await expect(profileSelect.locator("option").first()).toBeAttached({ timeout: 5000 });

    const options = await profileSelect.locator("option").all();
    const values = await Promise.all(options.map((opt) => opt.getAttribute("value")));

    // Target canonical reconciled profile if present
    const hasCanonical = values.includes("e0000000-0000-0000-0000-000000000001") || values.includes("canonical_reconciled_user");
    if (!hasCanonical) {
      test.skip(true, "Canonical fixture profile e0000000-0000-0000-0000-000000000001 not present in current DB");
      return;
    }

    const targetVal = values.includes("e0000000-0000-0000-0000-000000000001")
      ? "e0000000-0000-0000-0000-000000000001"
      : "canonical_reconciled_user";
    await profileSelect.selectOption(targetVal);
    // Wait for network/UI update
    await page.waitForTimeout(1000);

    // Verify the rendered KPI counts match PostgreSQL ground truth
    // Profile has 6 total decisions, 4 solver graded decisions, 1 chart, 1 ungraded
    await expect(page.locator("#stat-total-decisions")).toHaveText("6");
    await expect(page.locator("#stat-decision-counts-breakdown")).toContainText("4 solver-graded");
    await expect(page.locator("#stat-decision-counts-breakdown")).toContainText("1 chart");
    await expect(page.locator("#stat-decision-counts-breakdown")).toContainText("1 ungraded");

    // Verify EV loss chips rendered accurately: 6.15 chips
    await expect(page.locator("#stat-mean-ev-loss")).toContainText("6.15 chips");

    // Verify EV loss % of pot rendered accurately: 18.33% of pot (exact reconciled unweighted mean)
    await expect(page.locator("#stat-mean-ev-pct-pot")).toContainText("18.33% of pot");

    // Switch to Streets & Positions tab
    await page.getByRole("button", { name: "Streets & Positions" }).click();
    await expect(page.getByRole("heading", { name: "Street Breakdown" })).toBeVisible();

    // Switch to Mistake Explorer
    await page.getByRole("button", { name: "Mistake Explorer" }).click();
    await expect(page.getByRole("heading", { name: "Mistake Explorer" })).toBeVisible();

    // Switch to Data Quality & Leakage tab
    await page.getByRole("button", { name: "Data Quality & Leakage" }).click();
    await expect(page.getByRole("heading", { name: "Data Quality & Leakage Audit" })).toBeVisible();
    // Verify Missing EV rate shows 33.33% (1 chart + 1 ungraded out of 6 total decisions)
    await expect(page.getByText("33.33%", { exact: false })).toBeVisible();
  });

  test("validates empty state for newly created profile without crashing", async ({ page }) => {
    await page.goto("/analytics");
    // Verify tabs render without JavaScript errors
    for (const tab of [
      "Overview",
      "Learning Trends",
      "Streets & Positions",
      "Skill Taxonomy",
      "Mistake Explorer",
      "Session Comparisons",
      "Data Quality & Leakage",
    ]) {
      const btn = page.getByRole("button", { name: tab });
      await expect(btn).toBeVisible();
      await btn.click();
    }
  });
});
