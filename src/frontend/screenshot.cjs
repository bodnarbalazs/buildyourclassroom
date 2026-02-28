const { chromium } = require("playwright");

const FAKE_USER = { id: "test-1", email: "test@test.com", username: "testuser" };

async function capture() {
  const browser = await chromium.launch({ channel: "chrome" });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(FAKE_USER) })
  );

  await page.addInitScript((user) => {
    localStorage.setItem("auth_user", JSON.stringify(user));
  }, FAKE_USER);

  await page.goto("http://localhost:3000/classroom-builder", { waitUntil: "networkidle" });
  await page.waitForTimeout(500);

  await page.screenshot({ path: "classroom-idle.png", fullPage: true });
  console.log("Saved: classroom-idle.png");

  // Fill lesson plan and run simulation
  const textarea = page.locator("textarea");
  if (await textarea.isVisible()) {
    await textarea.fill("Introduction to fractions for 4th graders");
    const structureBtn = page.getByRole("button", { name: /structure/i });
    if (await structureBtn.isVisible()) {
      await structureBtn.click();
      await page.waitForTimeout(1200);
    }
    const runBtn = page.getByRole("button", { name: /run simulation/i });
    if (await runBtn.isVisible()) {
      await runBtn.click();
      await page.waitForTimeout(500);
    }
  }

  await page.screenshot({ path: "classroom-running.png", fullPage: true });
  console.log("Saved: classroom-running.png");

  // Tablet viewport
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.waitForTimeout(300);
  await page.screenshot({ path: "classroom-tablet.png", fullPage: true });
  console.log("Saved: classroom-tablet.png");

  await browser.close();
}

capture().catch((e) => {
  console.error(e);
  process.exit(1);
});
