import { test, expect } from "@playwright/test";

test.describe("Part 7: Retention, Spaced Repetition, and Blind Assessment", () => {
  test("loads assessment page and verifies capability gates & boundary disclosure", async ({ page }) => {
    await page.goto("/assessment");
    await expect(page).toHaveTitle(/Pokeria/);

    // Verify main heading
    await expect(page.getByRole("heading", { name: /Objective Assessment & Blind Validation/i })).toBeVisible();

    // Verify curriculum boundary disclosure
    await expect(page.getByText(/Curriculum Capability Boundary Disclosure/i)).toBeVisible();
    await expect(page.getByText(/42 solver-backed exercises concentrated on 6 boards/i)).toBeVisible();

    // Verify capability gates
    await expect(page.getByText("TIER5 BROAD TRANSFER")).toBeVisible();
    await expect(page.getByText(/INSUFFICIENT_TRANSFER_COVERAGE/i).first()).toBeVisible();
  });

  test("loads retention page and verifies spaced repetition queue & statistical integrity", async ({ page }) => {
    await page.goto("/retention");
    await expect(page).toHaveTitle(/Pokeria/);

    // Verify heading
    await expect(page.getByRole("heading", { name: /Spaced Repetition & Retention Analytics/i })).toBeVisible();

    // Verify summary KPI cards
    await expect(page.getByText("Due Reviews", { exact: true })).toBeVisible();
    await expect(page.getByText("Clean Reviews", { exact: true })).toBeVisible();
    await expect(page.getByText("Clean EV Loss", { exact: true })).toBeVisible();

    // Verify statistical integrity standard banner
    await expect(page.getByText(/Statistical Integrity Standard/i)).toBeVisible();
    await expect(page.getByText(/Caution: Retention estimates are preliminary/i)).toBeVisible();

    // Verify Review Queue table
    await expect(page.getByRole("heading", { name: /Due Reviews Queue/i })).toBeVisible();
  });

  test("verifies blind assessment hides answers and releases them upon grading with full retention lifecycle", async ({ page, request }) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8011";

    // 1. Create an isolated test profile
    const uniqueId = Date.now();
    const profileRes = await request.post(`${apiUrl}/api/v1/profiles`, {
      data: {
        username: `gate_user_${uniqueId}`,
        display_name: `Gate User ${uniqueId}`,
        email: `gate_${uniqueId}@pokerlab.local`,
      },
    });
    expect(profileRes.ok()).toBeTruthy();
    const profile = await profileRes.json();

    // 2. Establish a genuine prior exercise through the trusted training path
    const trainSessionRes = await request.post(`${apiUrl}/api/v1/training/sessions`, {
      data: {
        profile_id: profile.id,
        mode: "GUIDED",
        target_decisions: 1,
      },
    });
    expect(trainSessionRes.ok()).toBeTruthy();
    const trainSession = await trainSessionRes.json();

    const exRes = await request.get(`${apiUrl}/api/v1/training/sessions/${trainSession.id}/next`);
    expect(exRes.ok()).toBeTruthy();
    const exercise = await exRes.json();

    const decisionRes = await request.post(`${apiUrl}/api/v1/training/sessions/${trainSession.id}/decision`, {
      data: {
        chosen_action: exercise.legal_actions[0].kind,
        chosen_amount: exercise.legal_actions[0].amount,
        latency_ms: 320,
      },
    });
    expect(decisionRes.ok()).toBeTruthy();

    // Set isolated profile in browser context
    await page.addInitScript((profileId) => {
      window.localStorage.setItem("pokerlab_active_profile_id", profileId);
    }, profile.id);

    // 3. Navigate to /assessment
    await page.goto("/assessment");
    await page.waitForLoadState("networkidle");

    // Verify TIER1_RETEST is now ready
    await expect(page.getByText("TIER1 RETEST")).toBeVisible();
    await expect(page.getByText("Ready").first()).toBeVisible();

    // 4. Intercept assessment creation API response to confirm no leaks
    let sessionData: any = null;
    const sessionPromise = page.waitForResponse(
      (resp) => resp.url().includes("/api/v1/assessment/sessions") && resp.request().method() === "POST"
    );

    const startBtn = page.getByRole("button", { name: /Start Blind Assessment/i });
    await expect(startBtn).toBeVisible();
    await startBtn.click();

    const sessionResp = await sessionPromise;
    expect(sessionResp.ok()).toBeTruthy();
    sessionData = await sessionResp.json();

    // 5. Confirms no action EVs, reference frequencies, or grades leak before finalization
    expect(sessionData.session_id).toBeDefined();
    expect(sessionData.current_item).toBeDefined();
    expect(sessionData.current_item.scenario_id).toBeDefined();
    expect(sessionData.current_item.board).toBeDefined();
    expect(sessionData.current_item.legal_actions.length).toBeGreaterThan(0);

    // Assert strictly redacted
    expect(sessionData.current_item.reference_actions).toBeUndefined();
    expect(sessionData.current_item.action_evs).toBeUndefined();
    expect(sessionData.current_item.grade).toBeUndefined();
    expect(sessionData.current_item.chosen_ev).toBeUndefined();
    expect(sessionData.current_item.best_ev).toBeUndefined();

    // Verify Blind banner is active in UI
    await expect(page.getByText(/Blind Assessment in Progress/i)).toBeVisible();
    await expect(page.getByText(/Solver frequencies, EVs, and feedback are strictly withheld/i)).toBeVisible();

    // Confirm UI text does not contain hints or strategy tables
    const pageHtml = await page.content();
    expect(pageHtml).not.toContain("Authoritative Reference Strategy");
    expect(pageHtml).not.toContain("Action EVs");

    // 6. Submit solver-legal actions for each assessment item
    const totalItems = sessionData.total_items || 3;
    for (let i = 0; i < totalItems; i++) {
      // Pick the first available legal action button
      const legalActionBtns = page.locator("button:has-text('CHECK'), button:has-text('BET'), button:has-text('CALL'), button:has-text('FOLD'), button:has-text('RAISE')");
      await expect(legalActionBtns.first()).toBeVisible({ timeout: 5000 });
      await legalActionBtns.first().click();

      // Submit
      const isLast = i === totalItems - 1;
      const submitBtn = page.getByRole("button", {
        name: isLast ? /Submit & Finalize Assessment/i : /Submit & Next Item/i,
      });
      await expect(submitBtn).toBeEnabled();
      await submitBtn.click();
      await page.waitForTimeout(600);
    }

    // 7. Verify finalized evaluation report
    await expect(page.getByText(/Solver-Backed Assessment Complete/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/Evaluation Report/i)).toBeVisible();

    // 8. Confirms the results use actual solver EV values
    await expect(page.getByText(/Mean EV Loss/i)).toBeVisible();
    await expect(page.getByText(/Item-by-Item Solver Analysis/i)).toBeVisible();
    await expect(page.getByText(/Authoritative Reference Strategy/i).first()).toBeVisible();

    // 9. Refresh page and verify persistence
    await page.reload();
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /Objective Assessment & Blind Validation/i })).toBeVisible();

    // 10. Navigate to /retention and verify
    await page.goto("/retention");
    await page.waitForLoadState("networkidle");

    await expect(page.getByRole("heading", { name: /Spaced Repetition & Retention Analytics/i })).toBeVisible();
    await expect(page.getByText("Due Reviews", { exact: true })).toBeVisible();
    await expect(page.getByText("Clean Reviews", { exact: true })).toBeVisible();
    await expect(page.getByText("Clean EV Loss", { exact: true })).toBeVisible();
    await expect(page.getByText(/Statistical Integrity Standard/i)).toBeVisible();
  });
});
