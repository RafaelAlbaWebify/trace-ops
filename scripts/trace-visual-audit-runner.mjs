import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const auditRoot = process.env.TRACE_UI_AUDIT_ROOT;
const baseUrl = process.env.TRACE_FRONTEND_URL || "http://127.0.0.1:5173";

if (!auditRoot) {
  throw new Error("TRACE_UI_AUDIT_ROOT is required.");
}

const screenshotsDir = path.join(auditRoot, "screenshots");
fs.mkdirSync(screenshotsDir, { recursive: true });

const result = {
  generatedAt: new Date().toISOString(),
  frontendUrl: baseUrl,
  screenshots: [],
  interactions: [],
  consoleMessages: [],
  pageErrors: [],
  failedRequests: [],
  badResponses: []
};

function safeName(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "step";
}

function targetLabel(label) {
  return label instanceof RegExp ? label.toString() : String(label);
}

async function collectPageState(page, name) {
  return await page.evaluate((snapshotName) => {
    const visibleText = (element) => {
      const style = window.getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
    };

    const textOf = (element) => (element.innerText || element.textContent || "").trim().replace(/\s+/g, " ");

    const buttons = Array.from(document.querySelectorAll("button")).filter(visibleText).map((button) => ({
      text: textOf(button),
      disabled: button.disabled,
      className: button.className || "",
      ariaLabel: button.getAttribute("aria-label") || null,
      moduleId: button.getAttribute("data-module-id") || null
    }));

    const inputs = Array.from(document.querySelectorAll("input, textarea, select")).filter(visibleText).map((input) => {
      const label = input.closest("label")?.querySelector("span")?.textContent?.trim() || input.getAttribute("aria-label") || input.getAttribute("name") || input.tagName.toLowerCase();
      return {
        label,
        tag: input.tagName.toLowerCase(),
        type: input.getAttribute("type") || null,
        valuePreview: (input.value || "").slice(0, 160),
        disabled: input.disabled,
        options: input.tagName.toLowerCase() === "select" ? Array.from(input.options).map((option) => ({ text: option.text, value: option.value, selected: option.selected })) : []
      };
    });

    const headings = Array.from(document.querySelectorAll("h1, h2, h3")).filter(visibleText).map((heading) => ({
      level: heading.tagName.toLowerCase(),
      text: textOf(heading)
    }));

    const navButtons = Array.from(document.querySelectorAll("nav button")).filter(visibleText).map((button) => ({
      text: textOf(button),
      active: button.className.includes("active"),
      disabled: button.disabled,
      moduleId: button.getAttribute("data-module-id") || null
    }));

    const resultPanel = document.querySelector('[aria-label="Diagnostic result panel"]');

    return {
      name: snapshotName,
      title: document.title,
      url: window.location.href,
      headings,
      navButtons,
      buttons,
      inputs,
      resultPanelText: resultPanel ? textOf(resultPanel).slice(0, 2000) : null,
      bodyTextPreview: textOf(document.body).slice(0, 2500)
    };
  }, name);
}

async function snapshot(page, name) {
  const fileName = `${String(result.screenshots.length).padStart(2, "0")}-${safeName(name)}.png`;
  const filePath = path.join(screenshotsDir, fileName);
  await page.screenshot({ path: filePath, fullPage: true });
  const state = await collectPageState(page, name);
  state.screenshot = path.relative(auditRoot, filePath).replaceAll("\\", "/");
  result.screenshots.push(state);
}

async function clickButton(page, label, options = {}) {
  const entry = { action: "click", target: targetLabel(label), ok: false, error: null };
  try {
    const locator = options.scope ? options.scope.getByRole("button", { name: label }) : page.getByRole("button", { name: label });
    await locator.click({ timeout: 5000 });
    entry.ok = true;
  } catch (error) {
    entry.error = error instanceof Error ? error.message : String(error);
  }
  result.interactions.push(entry);
  return entry.ok;
}

async function clickModule(page, moduleId) {
  const entry = { action: "nav", target: moduleId, ok: false, error: null };
  try {
    const locator = page.locator(`[data-module-id="${moduleId}"]`).first();
    await locator.scrollIntoViewIfNeeded({ timeout: 5000 });
    await locator.click({ timeout: 5000 });
    entry.ok = true;
  } catch (error) {
    entry.error = error instanceof Error ? error.message : String(error);
  }
  result.interactions.push(entry);
  return entry.ok;
}

async function selectSource(page, value) {
  const entry = { action: "select", target: "source type", value, ok: false, error: null };
  try {
    await page.locator("select").first().selectOption(value);
    entry.ok = true;
  } catch (error) {
    entry.error = error instanceof Error ? error.message : String(error);
  }
  result.interactions.push(entry);
  return entry.ok;
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
const page = await context.newPage();

page.on("console", (message) => {
  result.consoleMessages.push({ type: message.type(), text: message.text() });
});
page.on("pageerror", (error) => {
  result.pageErrors.push(error.message);
});
page.on("requestfailed", (request) => {
  result.failedRequests.push({ url: request.url(), method: request.method(), failure: request.failure()?.errorText || null });
});
page.on("response", (response) => {
  const status = response.status();
  const url = response.url();
  if (status >= 400 && !url.includes("/@vite") && !url.includes("react-devtools")) {
    result.badResponses.push({ url, method: response.request().method(), status, statusText: response.statusText() });
  }
});

try {
  await page.goto(baseUrl, { waitUntil: "networkidle", timeout: 30000 });
  await snapshot(page, "initial access evidence page");

  await clickButton(page, /Analyze evidence/i);
  await page.waitForTimeout(1500);
  await snapshot(page, "after generic access evidence analysis");

  await selectSource(page, "entra_signin_csv");
  await page.waitForTimeout(300);
  await snapshot(page, "entra csv example selected");
  await clickButton(page, /Analyze evidence/i);
  await page.waitForTimeout(1500);
  await snapshot(page, "after entra csv analysis");

  await selectSource(page, "resource_assignment_json");
  await page.waitForTimeout(300);
  await snapshot(page, "resource assignment guided form selected");
  await clickButton(page, /Analyze evidence/i);
  await page.waitForTimeout(1500);
  await snapshot(page, "after resource assignment analysis");

  const preview = page.locator('[aria-label="Structured evidence preview"]');
  await clickButton(page, /Copy JSON|Copy evidence/i, { scope: preview });
  await page.waitForTimeout(300);
  await snapshot(page, "after copy analyzer input click");

  await clickModule(page, "history");
  await page.waitForTimeout(1000);
  await snapshot(page, "history page");

  await clickModule(page, "overview");
  await page.waitForTimeout(800);
  await snapshot(page, "overview page");

  const failedInteractions = result.interactions.filter((interaction) => !interaction.ok).length;
  if (result.pageErrors.length > 0 || result.failedRequests.length > 0 || result.badResponses.length > 0 || failedInteractions > 0) {
    result.status = "completed_with_findings";
  } else {
    result.status = "completed";
  }
} catch (error) {
  result.status = "failed";
  result.fatalError = error instanceof Error ? error.message : String(error);
  try {
    await snapshot(page, "fatal error state");
  } catch {
    // Avoid masking the original failure.
  }
} finally {
  await browser.close();
}

fs.writeFileSync(path.join(auditRoot, "visual-audit-summary.json"), JSON.stringify(result, null, 2), "utf8");

const markdown = [];
markdown.push("# TRACE Visual UI Audit");
markdown.push("");
markdown.push(`- Generated: ${result.generatedAt}`);
markdown.push(`- Frontend URL: ${result.frontendUrl}`);
markdown.push(`- Status: ${result.status}`);
markdown.push(`- Screenshots: ${result.screenshots.length}`);
markdown.push(`- Console messages: ${result.consoleMessages.length}`);
markdown.push(`- Page errors: ${result.pageErrors.length}`);
markdown.push(`- Failed requests: ${result.failedRequests.length}`);
markdown.push(`- Bad HTTP responses: ${result.badResponses.length}`);
markdown.push("");
markdown.push("## Screenshots");
for (const shot of result.screenshots) {
  markdown.push("");
  markdown.push(`### ${shot.name}`);
  markdown.push(`- File: \`${shot.screenshot}\``);
  markdown.push(`- Headings: ${shot.headings.map((item) => item.text).join(" | ") || "none"}`);
  markdown.push(`- Buttons: ${shot.buttons.map((item) => `${item.text}${item.disabled ? " (disabled)" : ""}`).join(" | ") || "none"}`);
  markdown.push(`- Inputs: ${shot.inputs.map((item) => `${item.label} [${item.tag}]`).join(" | ") || "none"}`);
}
markdown.push("");
markdown.push("## Interactions");
for (const interaction of result.interactions) {
  markdown.push(`- ${interaction.ok ? "PASS" : "FAIL"} ${interaction.action}: ${interaction.target}${interaction.value ? ` = ${interaction.value}` : ""}${interaction.error ? ` — ${interaction.error}` : ""}`);
}

if (result.badResponses.length > 0) {
  markdown.push("");
  markdown.push("## Bad HTTP responses");
  for (const response of result.badResponses) {
    markdown.push(`- ${response.status} ${response.method} ${response.url}`);
  }
}

fs.writeFileSync(path.join(auditRoot, "visual-audit-report.md"), markdown.join("\n"), "utf8");

if (result.status === "failed" || result.status === "completed_with_findings") {
  process.exit(1);
}
process.exit(0);
