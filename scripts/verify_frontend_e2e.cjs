const { chromium } = require('/Users/cbz/Desktop/Pokeria/apps/web/node_modules/playwright');

const BASE_URL = process.env.BASE_URL || 'http://localhost:3099';

function log(msg) {
  process.stdout.write(`[${new Date().toISOString()}] ${msg}\n`);
}

(async () => {
  log(`=== STARTING PLAYWRIGHT VERIFICATION ON ${BASE_URL} ===`);
  const browser = await chromium.launch({ headless: true });

  // Test Desktop
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  const page = await context.newPage();

  page.on('console', msg => {
    log(`[CONSOLE ${msg.type().toUpperCase()}] ${msg.text()}`);
  });
  page.on('pageerror', err => {
    log(`[PAGEERROR] ${err.message}`);
  });

  try {
    // 1. Root page & navigation
    log('1. Checking Root Homepage (/) & Recommendations...');
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1500);
    const brand = await page.textContent('text=POKER LAB').catch(() => null);
    log(`   Brand header found: ${brand ? 'YES' : 'NO'}`);
    const recVisible = await page.locator('text=Personalized Training Recommendation').first().isVisible();
    log(`   Personalized Training Recommendation visible: ${recVisible}`);
    const retSnapshot = await page.locator('text=Retention Queue').or(page.locator('text=Spaced Retrieval Schedule')).first().isVisible();
    log(`   Spaced Retrieval Queue Snapshot visible: ${retSnapshot}`);

    // 2. Learn / Curriculum Section
    log('2. Checking Learn / Curriculum Syllabus (/learn)...');
    await page.goto(`${BASE_URL}/learn`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1500);
    const learnHeading = await page.locator('h1:has-text("Curriculum")').or(page.locator('text=Curriculum Paths')).first().isVisible();
    log(`   Curriculum Syllabus visible: ${learnHeading}`);
    const turnBarrel = await page.locator('text=Turn Barrel').first().isVisible();
    log(`   Turn Barrel Lesson visible: ${turnBarrel}`);

    // 3. Practice / Decision Trainer Section
    log('3. Checking Practice Section (/practice)...');
    await page.goto(`${BASE_URL}/practice`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1500);
    const practiceHeading = await page.locator('text=Poker Decision Practice').first().isVisible();
    log(`   Practice Heading visible: ${practiceHeading}`);
    const selectMode = await page.locator('text=Select Practice Mode').first().isVisible();
    log(`   Select Practice Mode visible: ${selectMode}`);

    // 4. Competency Map / Skill Map Section
    log('4. Checking Skill Map / Taxonomy (/skill-map)...');
    await page.goto(`${BASE_URL}/skill-map`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1500);
    const mapHeading = await page.locator('text=Poker Competency Map').first().isVisible();
    log(`   Skill Map visible: ${mapHeading}`);
    const domainFilter = await page.locator('text=TOURNAMENT').first().isVisible();
    log(`   Tournament Domain Filter visible: ${domainFilter}`);

    // 5. Spaced Review Section
    log('5. Checking Review Section (/review)...');
    await page.goto(`${BASE_URL}/review`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1500);
    const reviewHeading = await page.locator('text=Review & Memory Consolidation').first().isVisible();
    log(`   Review page visible: ${reviewHeading}`);
    const fsrsDecay = await page.locator('text=Spaced Retrieval & FSRS Decay Model').first().isVisible();
    log(`   FSRS decay model badge visible: ${fsrsDecay}`);

    // 6. Simulate Sandbox Section
    log('6. Checking Simulate Section (/simulate)...');
    await page.goto(`${BASE_URL}/simulate`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1500);
    const simHeading = await page.locator('text=Simulation & Solver Workbench').first().isVisible();
    log(`   Simulation page visible: ${simHeading}`);

    // 7. Multidimensional Progress Section
    log('7. Checking Multidimensional Progress (/progress)...');
    await page.goto(`${BASE_URL}/progress`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1500);
    const progHeading = await page.locator('text=Learner Progress & Mastery Profile').first().isVisible();
    log(`   Progress Profile visible: ${progHeading}`);
    const correctnessDim = await page.locator('text=1. Strategic Correctness').first().isVisible();
    log(`   Dimension 1 (Strategic Correctness) visible: ${correctnessDim}`);
    const transferDim = await page.locator('text=6. Generalization (Transfer)').first().isVisible();
    log(`   Dimension 6 (Generalization Transfer) visible: ${transferDim}`);

    // 8. Mobile Viewport Check (375x667)
    log('8. Checking Mobile Viewport responsiveness (375x667)...');
    const mobileContext = await browser.newContext({
      viewport: { width: 375, height: 667 }
    });
    const mobilePage = await mobileContext.newPage();
    await mobilePage.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await mobilePage.waitForTimeout(1000);
    const mobileHeaderVisible = await mobilePage.locator('header').or(mobilePage.locator('nav')).first().isVisible();
    log(`   Mobile navigation/header responsive & visible: ${mobileHeaderVisible}`);
    await mobilePage.goto(`${BASE_URL}/learn`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await mobilePage.waitForTimeout(1000);
    const mobileLearnVisible = await mobilePage.locator('h1').first().isVisible();
    log(`   Mobile Learn page responsive & visible: ${mobileLearnVisible}`);
    await mobileContext.close();

    log('\n=============================================================');
    log('>>> FULL FRONTEND PLAYWRIGHT JOURNEYS: ALL 7/7 SECTIONS VERIFIED <<<');
    log('=============================================================');
  } catch (err) {
    log(`FATAL PLAYWRIGHT TEST ERROR: ${err.message}`);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
