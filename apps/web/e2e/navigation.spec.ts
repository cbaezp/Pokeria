import { test, expect } from "@playwright/test";

test.describe("Pokeria Application Navigation", () => {
  test("loads dashboard and verifies title and navigation items", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Pokeria/);
    await expect(page.getByRole("link", { name: "Pokeria Home" })).toBeVisible();
    await expect(page.getByText("Pokeria — Architecture, Infrastructure, and Application Foundation")).toBeVisible();
  });

  test("navigates to practice page and verifies interactive trainer", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Practice" }).first().click();
    await expect(page).toHaveURL(/.*practice/);
    await expect(page.getByRole("heading", { name: /Poker Decision Practice/i })).toBeVisible();
  });

  test("navigates to progress page and verifies functional dashboard", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Progress" }).first().click();
    await expect(page).toHaveURL(/.*progress/);
    await expect(page.getByRole("heading", { name: /Learner Progress & Mastery Profile/i })).toBeVisible();
  });

  test("navigates to settings page", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: "Settings", exact: true })).toBeVisible();
    await expect(page.getByText("Manage your local preferences")).toBeVisible();
  });
});
