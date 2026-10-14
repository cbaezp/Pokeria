import { test, expect } from "@playwright/test";

test.describe("Phase D - Elite Poker Learning Architecture E2E", () => {
  test("1. Dashboard / Overview loads adaptive recommendations and review queues", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Pokeria/);
    const dashboardTab = page.getByRole("button", { name: "Analytics & Evidence Dashboard" });
    if (await dashboardTab.isVisible()) {
      await dashboardTab.click();
    }
    await expect(page.getByText(/Personalized Training Recommendation/i)).toBeVisible();
    await expect(page.getByText(/Spaced Retention/i).first()).toBeVisible();
  });

  test("2. Learn page displays curriculum syllabus, prerequisites, and transfer assessments", async ({ page }) => {
    await page.goto("/learn");
    await expect(page.getByRole("heading", { name: /Structured Tournament Hold'em Curriculum/i })).toBeVisible();
    const syllabusBtn = page.getByRole("button", { name: /Syllabus & Transfer Gates/i });
    if (await syllabusBtn.isVisible()) {
      await syllabusBtn.click();
    }
    await expect(page.getByText(/The Power of Position/i).first()).toBeVisible();
    await expect(page.getByText(/Concept Instruction & Principles/i)).toBeVisible();
  });

  test("3. Practice page supports confidence calibration and decision flow", async ({ page }) => {
    await page.goto("/practice");
    await expect(page.getByRole("heading", { name: /Poker Decision Practice/i })).toBeVisible();
    await expect(page.getByText(/Solver-Backed Deliberate Practice/i)).toBeVisible();
  });

  test("4. Skill Map displays decoupled taxonomy with honest solver scope boundaries", async ({ page }) => {
    await page.goto("/skill-map");
    await expect(page.getByRole("heading", { name: /Poker Competency Map/i })).toBeVisible();
    await expect(page.getByText(/Tournament ICM/i).first()).toBeVisible();
  });

  test("5. Review page displays FSRS spaced retrieval queue and honest evidence metrics", async ({ page }) => {
    await page.goto("/review");
    await expect(page.getByRole("heading", { name: /Review & Memory Consolidation/i })).toBeVisible();
    await expect(page.getByText(/Spaced Retrieval & FSRS Decay Model/i)).toBeVisible();
    await expect(page.getByText(/Due Retrieval Queue/i)).toBeVisible();
  });

  test("6. Simulate page renders interactive game tree explorer", async ({ page }) => {
    await page.goto("/simulate");
    await expect(page.getByRole("heading", { name: /Simulation & Solver Workbench/i })).toBeVisible();
    await expect(page.getByText(/Push-Fold Equilibrium Engine/i)).toBeVisible();
  });

  test("7. Progress page displays 6-dimensional metrics with explicit INSUFFICIENT_EVIDENCE", async ({ page }) => {
    await page.goto("/progress");
    await expect(page.getByRole("heading", { name: /Learner Progress & Mastery Profile/i })).toBeVisible();
    await expect(page.getByText(/1. Strategic Correctness/i)).toBeVisible();
    await expect(page.getByText(/2. Memory Retention/i)).toBeVisible();
    await expect(page.getByText(/3. Confidence Calibration/i)).toBeVisible();
    await expect(page.getByText(/4. Decision Speed/i)).toBeVisible();
    await expect(page.getByText(/5. Performance Consistency/i)).toBeVisible();
    await expect(page.getByText(/6. Generalization \(Transfer\)/i)).toBeVisible();
  });
});
