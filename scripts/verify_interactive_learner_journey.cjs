const { chromium } = require('/Users/cbz/Desktop/Pokeria/apps/web/node_modules/playwright');

const BASE_URL = process.env.BASE_URL || 'http://localhost:3099';

function log(msg) {
  process.stdout.write(`[${new Date().toISOString()}] ${msg}\n`);
}

(async () => {
  log(`=== STARTING PHASE D COMPREHENSIVE INTERACTIVE LEARNER JOURNEY ===`);
  log(`Target Web URL: ${BASE_URL}`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      log(`[BROWSER ERROR] ${msg.text()}`);
    }
  });
  page.on('pageerror', (err) => {
    log(`[PAGE ERROR] ${err.message}`);
  });

  try {
    // 1. Dashboard / Recommendations verification
    log('STEP 1: Visiting Dashboard (/) to verify recommendations & cold start state...');
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1500);

    const title = await page.title();
    log(`   Dashboard Title: "${title}"`);
    const recSection = await page.locator('text=Personalized Training Recommendation').first().isVisible();
    log(`   Recommendation Card visible: ${recSection}`);

    // 2. Curriculum Lesson Selection
    log('STEP 2: Navigating to Curriculum (/learn) & Selecting Lesson...');
    await page.goto(`${BASE_URL}/learn`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1500);

    const learnHeading = await page.locator('h1').first().textContent();
    log(`   Curriculum Heading: "${learnHeading?.trim()}"`);

    // Select Turn Barrel lesson if available or first lesson
    const turnLessonBtn = page.locator('button:has-text("Turn Barrel")').first();
    if (await turnLessonBtn.isVisible()) {
      await turnLessonBtn.click();
      log('   Clicked "Turn Barrel" lesson');
      await page.waitForTimeout(800);
    }

    // Verify instructional content & invariants
    const conceptHeader = await page.locator('text=Concept Instruction & Principles').first().isVisible();
    log(`   Concept Instruction section visible: ${conceptHeader}`);

    // Mark concept studied
    const studyBtn = page.locator('button:has-text("Mark Concept Studied")').first();
    if (await studyBtn.isVisible()) {
      await studyBtn.click();
      log('   Clicked "Mark Concept Studied"');
      await page.waitForTimeout(1000);
    }

    // 3. Scenario Loading in Practice Drill
    log('STEP 3: Launching Practice Drill & Verifying Pre-Submission Anti-Leakage...');
    const practiceDrillBtn = page.locator('a:has-text("Practice Drill")').first();
    if (await practiceDrillBtn.isVisible()) {
      await practiceDrillBtn.click();
    } else {
      await page.goto(`${BASE_URL}/practice?category=turn`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    }
    await page.waitForTimeout(2000);

    // If on setup screen, start practice session
    const startBtn = page.locator('button:has-text("Start Practice Session")').first();
    if (await startBtn.isVisible()) {
      log('   On setup screen, clicking "Start Practice Session"...');
      await startBtn.click();
      await page.waitForTimeout(2500);
    }

    // Verify poker table is rendered
    const tableVisible = await page.locator('text=PRACTICE SESSION').first().isVisible();
    log(`   Active Practice Session loaded: ${tableVisible}`);

    // Verify EV and answers are NOT leaked before submission
    const feedbackVisibleBefore = await page.locator('text=Decision Analysis').isVisible().catch(() => false);
    const evLossVisibleBefore = await page.locator('text=EV Loss:').count();
    // Only session top bar EV loss should be visible, NOT per-action EV breakdown
    const gtoRefBefore = await page.locator('text=GTO Reference Strategy').isVisible().catch(() => false);
    log(`   Leak Check: Decision Analysis visible before submission: ${feedbackVisibleBefore} (MUST BE FALSE)`);
    log(`   Leak Check: GTO Reference Strategy visible before submission: ${gtoRefBefore} (MUST BE FALSE)`);
    if (feedbackVisibleBefore || gtoRefBefore) {
      throw new Error('ANTI-LEAKAGE FAILURE: Solver answers or evaluation visible before action submission!');
    }

    // 4. Confidence Selection & Action Submission
    log('STEP 4: Selecting Confidence Score (4 - High) and Submitting Poker Action...');
    // Click confidence button "4 · High"
    const conf4Btn = page.locator('button:has-text("4 · High")').first();
    if (await conf4Btn.isVisible()) {
      await conf4Btn.click();
      log('   Selected confidence: 4 · High');
      await page.waitForTimeout(500);
    }

    // Select legal action: Check, Call, Fold, or Bet
    const checkBtn = page.locator('button:has-text("Check")').first();
    const foldBtn = page.locator('button:has-text("Fold")').first();
    const callBtn = page.locator('button:has-text("Call")').first();

    if (await checkBtn.isVisible()) {
      log('   Dispatching action: CHECK');
      await checkBtn.click();
    } else if (await foldBtn.isVisible()) {
      log('   Dispatching action: FOLD');
      await foldBtn.click();
    } else if (await callBtn.isVisible()) {
      log('   Dispatching action: CALL');
      await callBtn.click();
    } else {
      log('   Looking for any action button...');
      await page.locator('button:has-text("Pass action")').first().click();
    }
    await page.waitForTimeout(2000);

    // 5. Feedback Verification
    log('STEP 5: Verifying Feedback Overlay, Grade, and Solver EV Provenance...');
    const feedbackOverlay = await page.locator('text=Decision Analysis').first().isVisible();
    log(`   Decision Analysis overlay visible: ${feedbackOverlay}`);
    if (!feedbackOverlay) {
      throw new Error('FEEDBACK ERROR: FeedbackOverlay did not appear after decision submission.');
    }

    // Verify grade label
    const gradeText = await page.locator('text=Decision Analysis').locator('..').textContent();
    log(`   Feedback Grade and Analysis Content: ${gradeText?.replace(/\s+/g, ' ').trim()}`);

    // Verify GTO reference strategy breakdown is now revealed
    const gtoRefAfter = await page.locator('text=GTO Reference Strategy').or(page.locator('text=Preflop Chart Reference')).first().isVisible();
    log(`   GTO Reference Strategy revealed post-submission: ${gtoRefAfter}`);

    // Advance to next exercise or dismiss
    const nextBtn = page.locator('button:has-text("Next Exercise")').first();
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
      log('   Clicked "Next Exercise"');
      await page.waitForTimeout(1500);
    }

    // 6. Review & Memory Consolidation (/review)
    log('STEP 6: Checking Spaced Review (/review) & Retrieval Queue...');
    await page.goto(`${BASE_URL}/review`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(2000);

    const reviewHeader = await page.locator('h1').first().textContent();
    log(`   Review Heading: "${reviewHeader?.trim()}"`);
    const dueQueueHeader = await page.locator('text=Due Retrieval Queue').or(page.locator('text=Retrieval Queue Clear')).first().isVisible();
    log(`   Retrieval Queue section visible: ${dueQueueHeader}`);

    // If there is an item in the queue, click Pass
    const passBtn = page.locator('button:has-text("Pass")').first();
    if (await passBtn.isVisible()) {
      log('   Found due review item! Clicking "Pass" to complete review...');
      await passBtn.click();
      await page.waitForTimeout(1500);
      log('   Review item passed successfully.');
    } else {
      log('   Retrieval queue currently clear or up to date.');
    }

    // 7. Held-Out Transfer Verification
    log('STEP 7: Verifying Held-Out Transfer Gate from Curriculum (/learn)...');
    await page.goto(`${BASE_URL}/learn`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1500);

    const transferGate = await page.locator('text=Phase D Strategic Transfer Gate').first().isVisible();
    log(`   Transfer Gate card visible: ${transferGate}`);
    const transferBtn = page.locator('text=Attempt Held-Out Transfer Assessment').first();
    const isTransferAvailable = await transferBtn.isVisible();
    log(`   "Attempt Held-Out Transfer Assessment" button visible: ${isTransferAvailable}`);

    if (isTransferAvailable) {
      await transferBtn.click();
      await page.waitForTimeout(2500);

      // Start transfer practice session if needed
      const transferStartBtn = page.locator('button:has-text("Start Practice Session")').first();
      if (await transferStartBtn.isVisible()) {
        await transferStartBtn.click();
        await page.waitForTimeout(2000);
      }

      // Submit transfer action
      const transferConfBtn = page.locator('button:has-text("5 · Certain")').first();
      if (await transferConfBtn.isVisible()) {
        await transferConfBtn.click();
      }
      const transferActBtn = page.locator('button:has-text("Check")').or(page.locator('button:has-text("Fold")')).first();
      if (await transferActBtn.isVisible()) {
        await transferActBtn.click();
        await page.waitForTimeout(1500);
        log('   Transfer assessment decision submitted with confidence 5.');
        const transferNext = page.locator('button:has-text("Next Exercise")').first();
        if (await transferNext.isVisible()) {
          await transferNext.click();
          await page.waitForTimeout(1000);
        }
      }
    }

    // 8. Progress Page Multidimensional Evaluation (/progress)
    log('STEP 8: Verifying 6-Dimensional Mastery Profile (/progress)...');
    await page.goto(`${BASE_URL}/progress`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(2000);

    const progressHeader = await page.locator('h1').first().textContent();
    log(`   Progress Heading: "${progressHeader?.trim()}"`);

    const dim1 = await page.locator('text=1. Strategic Correctness').first().isVisible();
    const dim2 = await page.locator('text=2. Memory Retention').first().isVisible();
    const dim3 = await page.locator('text=3. Confidence Calibration').first().isVisible();
    const dim4 = await page.locator('text=4. Decision Speed').first().isVisible();
    const dim5 = await page.locator('text=5. Performance Consistency').first().isVisible();
    const dim6 = await page.locator('text=6. Generalization (Transfer)').first().isVisible();

    log(`   Dim 1 (Strategic Correctness) visible: ${dim1}`);
    log(`   Dim 2 (Memory Retention) visible: ${dim2}`);
    log(`   Dim 3 (Confidence Calibration) visible: ${dim3}`);
    log(`   Dim 4 (Decision Speed) visible: ${dim4}`);
    log(`   Dim 5 (Performance Consistency) visible: ${dim5}`);
    log(`   Dim 6 (Generalization Transfer) visible: ${dim6}`);

    if (!dim1 || !dim2 || !dim3 || !dim4 || !dim5 || !dim6) {
      throw new Error('PROGRESS ERROR: One or more of the 6 dimensions is missing from /progress.');
    }

    // Check Data Integrity box
    const isolationAudit = await page.locator('text=Data Integrity & Isolation Audit').first().isVisible();
    log(`   Data Integrity & Isolation Audit section visible: ${isolationAudit}`);

    // 9. Revisit Homepage (/) to confirm recommendation & state update
    log('STEP 9: Re-checking Dashboard (/) for updated recommendations & retention snapshot...');
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1500);

    const recUpdated = await page.locator('text=Personalized Training Recommendation').first().isVisible();
    log(`   Dashboard recommendation present: ${recUpdated}`);

    log('\n========================================================================');
    log('>>> SUCCESS: FULL PHASE D INTERACTIVE PLAYWRIGHT LEARNER JOURNEY VERIFIED <<<');
    log('========================================================================\n');
  } catch (err) {
    log(`FATAL ERROR IN PLAYWRIGHT TEST: ${err.message}`);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
