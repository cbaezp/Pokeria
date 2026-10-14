import { test, expect } from "@playwright/test";

test.describe("Pokeria Personalized Learner & Weakness Detection", () => {
  test("navigates to learner page and verifies overview and scientific limitations", async ({ page }) => {
    await page.goto("/learner");
    await expect(page.getByRole("heading", { name: "Personalized Learner" })).toBeVisible();

    // Verify curriculum limitation disclosure
    await expect(
      page.getByText("Curriculum Coverage Boundary & Scientific Integrity Disclosure:")
    ).toBeVisible();
    await expect(
      page.getByText("spans 3 river boards across 3 reference strategy packs")
    ).toBeVisible();

    // Verify baseline recommendation mode
    await expect(page.getByText("RULE-BASED BASELINE")).toBeVisible();
  });

  test("can switch between learner tabs without errors", async ({ page }) => {
    await page.goto("/learner");

    // Click Weaknesses tab
    await page.getByRole("button", { name: "Weaknesses" }).click();
    await expect(
      page.getByRole("heading", { name: "Empirical Weakness Detection" })
    ).toBeVisible();

    // Click Recommendations tab
    await page.getByRole("button", { name: "Recommendations" }).click();
    await expect(page.getByText("Current Strategy Policy")).toBeVisible();
    await expect(page.getByText("Solver Authoritative Only")).toBeVisible();

    // Click Model & Evaluation tab
    await page.getByRole("button", { name: "Model & Evaluation" }).click();
    await expect(
      page.getByRole("heading", { name: "Offline Evaluation Harness & Promotion Gate" })
    ).toBeVisible();
  });

  test("can navigate from recommendations Practice Now to interactive training", async ({ page }) => {
    await page.goto("/learner");

    // Click Recommendations tab
    await page.getByRole("button", { name: "Recommendations" }).click();
    await expect(page.getByText("Practice Recommendations")).toBeVisible();

    // Find and click the first "Practice Now" link
    const practiceLink = page.getByRole("link", { name: "Practice Now" }).first();
    await expect(practiceLink).toBeVisible();
    await practiceLink.click();

    // Verify redirected to /training?scenario=
    await expect(page).toHaveURL(/\/training\?scenario=/);

    // Verify targeted recommendation banner is rendered
    await expect(page.getByText("Targeted Recommendation Practice Active")).toBeVisible();

    // Click Start Training Session
    const startBtn = page.getByRole("button", { name: "Start Training Session" });
    await expect(startBtn).toBeVisible();
    await startBtn.click();

    // Verify interactive poker table loads
    await expect(page.getByText("Session EV Loss")).toBeVisible();
  });
});
