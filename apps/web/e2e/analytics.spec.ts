import { test, expect } from "@playwright/test";

test.describe("Poker Lab Learning Analytics Dashboard", () => {
  test("loads analytics dashboard and verifies core layout and tabs", async ({ page }) => {
    await page.goto("/analytics");
    await expect(page).toHaveTitle(/Pokeria/);
    await expect(page.getByRole("heading", { name: "Decision Performance & Integrity" })).toBeVisible();

    // Verify statistical integrity notice
    await expect(page.getByText("Statistical Integrity Notice:")).toBeVisible();

    // Verify all 7 tabs are visible
    await expect(page.getByRole("button", { name: "Overview" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Learning Trends" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Streets & Positions" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Skill Taxonomy" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Mistake Explorer" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Session Comparisons" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Data Quality & Leakage" })).toBeVisible();
  });

  test("interacts with tabs and explores sections", async ({ page }) => {
    await page.goto("/analytics");

    // 1. Learning Trends tab
    await page.getByRole("button", { name: "Learning Trends" }).click();
    await expect(page.getByRole("heading", { name: "Performance Over Time" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Week" })).toBeVisible();

    // 2. Streets & Positions tab
    await page.getByRole("button", { name: "Streets & Positions" }).click();
    await expect(page.getByRole("heading", { name: "Street Breakdown" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Positional Breakdown" })).toBeVisible();

    // 3. Skill Taxonomy tab
    await page.getByRole("button", { name: "Skill Taxonomy" }).click();
    await expect(page.getByRole("heading", { name: "Skill Taxonomy Breakdown" })).toBeVisible();

    // 4. Mistake Explorer tab
    await page.getByRole("button", { name: "Mistake Explorer" }).click();
    await expect(page.getByRole("heading", { name: "Mistake Explorer" })).toBeVisible();

    // 5. Session Comparisons tab
    await page.getByRole("button", { name: "Session Comparisons" }).click();
    await expect(page.getByRole("heading", { name: "Historical Session Comparison" })).toBeVisible();

    // 6. Data Quality & Leakage tab
    await page.getByRole("button", { name: "Data Quality & Leakage" }).click();
    await expect(page.getByRole("heading", { name: /Data Quality/ })).toBeVisible();
  });
});
