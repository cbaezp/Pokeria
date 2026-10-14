import { test, expect } from "@playwright/test";

test.describe("Pokeria — Guided Learning Path Transformation", () => {
  test.beforeEach(async ({ page }) => {
    // Increase timeout for comprehensive multi-step flow
    test.setTimeout(90000);
  });

  test("full beginner learner journey: onboarding -> path -> rules -> positions -> ranges", async ({ page }) => {
    page.on("console", (msg) => console.log("BROWSER LOG:", msg.text()));
    page.on("pageerror", (err) => console.log("BROWSER ERROR:", err.message));
    // 1. Create a fresh profile via API and set as active profile
    const testId = Date.now().toString().slice(-6);
    const username = `learner_${testId}`;
    const profileRes = await page.request.post("http://localhost:8011/api/v1/profiles", {
      data: {
        username,
        display_name: `Learner ${testId}`,
        email: `${username}@pokeria.test`,
        preferences: { theme: "dark", sound: true },
      },
    });
    const profile = await profileRes.json();

    // 2. Navigate to Home Page (Learning Path) with profile active in localStorage
    await page.addInitScript((profileId) => {
      window.localStorage.setItem("pokerlab_active_profile_id", profileId);
    }, profile.id);

    await page.goto("/");
    await expect(page.getByRole("heading", { name: /Welcome/i })).toBeVisible();
    await expect(page.getByRole("button", { name: "Guided Learning Path" })).toBeVisible();

    // Capture screenshot of learning path overview
    await page.screenshot({ path: "learning_path_overview.png", fullPage: true });

    // 3. Select "NEW TO POKER" Onboarding
    const newToPokerBtn = page.getByRole("button", { name: /NEW TO POKER/i });
    if (await newToPokerBtn.isVisible()) {
      await newToPokerBtn.click();
    }

    // 4. Continue Learning CTA is visible and points to How Texas Hold'em Works
    await expect(page.getByRole("button", { name: /CONTINUE LEARNING/i })).toBeVisible();
    await expect(page.getByText("How Texas Hold'em Works", { exact: false }).first()).toBeVisible();

    // 5. Click "CONTINUE LEARNING" to launch interactive lesson modal
    await page.getByRole("button", { name: /CONTINUE LEARNING/i }).click();

    // 6. Verify Lesson Modal is open
    await expect(page.getByText("How Texas Hold'em Works", { exact: false }).first()).toBeVisible();
    await expect(page.getByText(/Step 1 of/i)).toBeVisible();

    // Advance through Step 1 (Hole cards vs community cards)
    await page.getByRole("button", { name: "Continue", exact: true }).click();

    // Step 2: The Five Rounds
    await expect(page.getByText(/Step 2 of/i)).toBeVisible();
    await page.getByRole("button", { name: "Continue", exact: true }).click();

    // Step 3: Knowledge Check (How many community cards on the flop?)
    await expect(page.getByText(/How many community cards are dealt face up on the Flop/i)).toBeVisible();

    // Select "3 cards" option
    await page.getByRole("button", { name: /3 cards/i }).click();
    await page.getByRole("button", { name: "Verify Answer" }).click();
    await expect(page.getByText("Correct!", { exact: true })).toBeVisible();

    // Advance past check
    await page.getByRole("button", { name: "Continue", exact: true }).click();

    // Step 4: How a hand is won
    await expect(page.getByText("How a Hand Is Won")).toBeVisible();
    await page.getByRole("button", { name: "Continue", exact: true }).click();

    // Step 5: Recap & complete lesson
    await expect(page.getByRole("button", { name: "Complete Lesson" })).toBeVisible();
    await page.getByRole("button", { name: "Complete Lesson" }).click();

    // Modal closes; verify back on path
    await expect(page.getByRole("heading", { name: /Welcome/i })).toBeVisible();

    // 7. Test Table Positions Interactive Lesson
    const positionsNode = page.getByRole("button", { name: /Table Positions & Action Order/i }).first();
    await positionsNode.scrollIntoViewIfNeeded();
    await positionsNode.click();

    // Verify Poker Table Explorer is rendered inside lesson
    await expect(page.getByText("Pokeria 6-Max Table")).toBeVisible();
    await expect(page.getByRole("button", { name: "Preflop (UTG First)" })).toBeVisible();

    // Test toggle to Postflop
    await page.getByRole("button", { name: "Postflop (BTN Last)" }).click();
    await expect(page.getByText(/Postflop \(BTN Last\)/i)).toBeVisible();

    // Take screenshot of interactive table position lesson
    await page.screenshot({ path: "table_positions_interactive.png" });

    // Close lesson modal
    await page.getByTitle("Exit Lesson").click();

    // 8. Test Gold-Standard Lesson: Chapter 2, Unit 2: "How to Read a Poker Range"
    const rangeLessonNode = page.getByRole("button", { name: /How to Read a Poker Range/i }).first();
    await rangeLessonNode.scrollIntoViewIfNeeded();
    await rangeLessonNode.click();

    // Step 1: Range concept
    await expect(page.getByText("The Purpose of a Range")).toBeVisible();
    await page.getByRole("button", { name: "Continue", exact: true }).click();

    // Step 2: 13x13 Range Matrix Explorer
    await expect(page.getByText("The 13x13 Starting Hand Matrix")).toBeVisible();
    // Verify matrix buttons exist
    await expect(page.getByRole("button", { name: "AA", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "AKs", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "AKo", exact: true })).toBeVisible();

    // Take screenshot of range matrix explorer
    await page.screenshot({ path: "range_matrix_explorer.png" });

    await page.getByRole("button", { name: "Continue", exact: true }).click();

    // Step 3: Understanding Notation (AKs vs AKo vs AA)
    await expect(page.getByText(/Understanding Notation: AKs vs AKo vs AA/i)).toBeVisible();
    await page.getByRole("button", { name: "Continue", exact: true }).click();

    // Step 4: Knowledge Check (Where are suited hands located?)
    await expect(page.getByText(/In the standard 13x13 poker range matrix, where are suited hands/i)).toBeVisible();
    await page.getByRole("button", { name: /Above and to the right of the pair diagonal/i }).click();
    await page.getByRole("button", { name: "Verify Answer" }).click();
    await expect(page.getByText("Correct!", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Continue", exact: true }).click();

    // Step 5: Combination math (6, 4, 12)
    await expect(page.getByText(/Combinations Math: 6, 4, and 12/i)).toBeVisible();
    await page.getByRole("button", { name: "Continue", exact: true }).click();

    // Step 6: Knowledge Check (Combination counting for offsuit hands)
    await expect(page.getByText(/How many total starting card combinations make up any unpaired offsuit hand/i)).toBeVisible();
    await page.getByRole("button", { name: /12 combinations/i }).click();
    await page.getByRole("button", { name: "Verify Answer" }).click();
    await expect(page.getByText(/Spot on!/i)).toBeVisible();
    await page.getByRole("button", { name: "Continue", exact: true }).click();

    // Step 7: Positional expansion (UTG vs BTN)
    await expect(page.getByText(/Why Position Shapes Range Composition/i)).toBeVisible();
    await page.getByRole("button", { name: "Continue", exact: true }).click();

    // Step 8: Lesson completion summary
    await expect(page.getByText(/Congratulations!/i)).toBeVisible();
    await page.getByRole("button", { name: "Complete Lesson" }).click();

    // 9. Verify Exit and Resume State
    await page.goto("/settings");
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /Welcome/i })).toBeVisible();

    // 10. Verify Practice page shows Theory advisory banner for unprepared users
    await page.goto("/practice");
    await expect(page.getByText(/Foundational Theory Recommended Before Simulation/i)).toBeVisible();
    await expect(page.getByRole("link", { name: /Open Learning Path/i })).toBeVisible();
  });
});
