const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const { pathToFileURL } = require('node:url');
const path = require('node:path');
const assert = require('node:assert/strict');
const fs = require('node:fs');

(async () => {
 const browser = await chromium.launch({ headless: true, ...(process.env.BROWSER_PATH ? { executablePath: process.env.BROWSER_PATH } : {}) });
 try {
  const context = await browser.newContext({ offline: true, viewport: { width: 1480, height: 1050 } });
  const page = await context.newPage(); const errors = [], external = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', r => { if (/^https?:/.test(r.url())) external.push(r.url()); });
  await page.goto(pathToFileURL(path.resolve(__dirname, '..', 'index.html')).href);
  await page.waitForFunction(() => document.getElementById('status').textContent.includes('显示网格'));
  assert.match(await page.locator('#scope').textContent(), /合成示例/);
  await page.locator('#file').setInputFiles(path.join(__dirname, 'fixtures', 'synthetic-dem.tif'));
  await page.waitForFunction(() => document.getElementById('status').textContent.includes('synthetic-dem.tif ·'));
  await page.waitForTimeout(200);
  const grid = await page.evaluate(() => ({ z: document.getElementById('flat').data[0].z, y: document.getElementById('flat').data[0].y }));
  assert.equal(grid.z.length, 48); assert.equal(grid.z[0].length, 64);
  assert.equal(grid.z[0][0], null); assert.equal(grid.z[20][30], 90);
  assert.ok(grid.y[0] > grid.y.at(-1));
  await page.evaluate(() => Plotly.relayout('flat', { 'xaxis.range': [360040, 360060], 'yaxis.range': [3999950, 3999970] }));
  await page.waitForFunction(() => document.getElementById('flat').data[0].z.length < 48);
  assert.equal(await page.locator('#error').textContent(), '');
  await page.click('#reset');
  await page.waitForFunction(() => document.getElementById('flat').data[0].z.length === 48);
  await page.waitForTimeout(200);
  fs.mkdirSync(path.resolve(__dirname, '../test-results'), { recursive: true });
  await page.screenshot({ path: path.resolve(__dirname, '../test-results/local-geotiff.png'), fullPage: true });
  assert.deepEqual(errors, []); assert.deepEqual(external, []);
  console.log('PASS: offline example, local GeoTIFF, exact height/nodata/orientation, native zoom, reset, no uploads or external requests');
 } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
