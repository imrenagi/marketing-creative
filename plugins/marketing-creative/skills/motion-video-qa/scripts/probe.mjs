#!/usr/bin/env node
// Visual construction probe only. HyperFrames owns production visibility/media.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
const root = fs.realpathSync(path.resolve(process.argv[2] || '.'));
const safeOutput = relative => {
  const output = path.resolve(root, relative);
  if (!output.startsWith(root + path.sep)) throw new Error('Output path escapes project');
  let current = root;
  for (const part of path.relative(root, output).split(path.sep)) {
    current = path.join(current, part);
    let info;
    try { info = fs.lstatSync(current); } catch (error) { if (error.code !== 'ENOENT') throw error; }
    if (info?.isSymbolicLink()) throw new Error('Symlink probe output refused');
  }
  return output;
};
const timing = JSON.parse(fs.readFileSync(path.join(root, 'timing.resolved.json'), 'utf8'));
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({ headless: true,
  ...(process.env.PLAYWRIGHT_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_EXECUTABLE } : {}) });
const report = { schemaVersion: 1, inputHashes: timing.inputHashes, scope: 'visual construction probe; no framework/media validation', variants: [] };
try {
  for (const variant of timing.variants) {
    const dir = path.join(root, 'variants', variant.id);
    const build = JSON.parse(fs.readFileSync(path.join(dir, 'build.json'), 'utf8'));
    if (!build.localRuntime) throw new Error('Probe needs --gsap local runtime to avoid network-dependent frames');
    const page = await browser.newPage({ viewport: { width: variant.width, height: variant.height }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(() => { window.__timelines = {}; });
    await page.goto(pathToFileURL(path.join(dir, 'index.html')).href, { waitUntil: 'load' });
    await page.waitForFunction(() => !!window.__timelines.main);
    await page.evaluate(() => document.fonts.ready);
    const out = safeOutput(path.join('qa/frames', variant.id));
    fs.mkdirSync(out, { recursive: true });
    const samples = new Set([.01, Math.max(0, variant.duration - .02)]);
    for (const beat of variant.beats) {
      samples.add(Math.min(beat.end - .001, beat.start + .05));
      samples.add((beat.start + beat.end) / 2);
      samples.add(Math.max(beat.start, beat.end - .03));
    }
    const seek = async time => page.evaluate(async t => {
      window.__timelines.main.seek(t, false);
      for (const el of document.querySelectorAll('.clip[data-start]')) {
        const start = Number(el.dataset.start), end = start + Number(el.dataset.duration);
        el.style.visibility = t >= start && t < end ? 'visible' : 'hidden';
      }
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    }, time);
    const frames = [];
    for (const t of [...samples].sort((a, b) => a-b)) {
      await seek(t);
      const boxes = await page.evaluate(({ safe, W, H }) => {
        const visible = el => {
          for (let parent = el; parent; parent = parent.parentElement) {
            const css = getComputedStyle(parent);
            if (css.visibility === 'hidden' || css.display === 'none' || Number(css.opacity) < .05) return false;
          }
          return true;
        };
        return [...document.querySelectorAll('[data-qa-important]')].filter(visible).map(el => {
          const box = el.getBoundingClientRect();
          return { tag: el.tagName, text: (el.textContent || '').trim().slice(0, 100),
            x: box.x, y: box.y, width: box.width, height: box.height,
            fits: box.left >= safe.left*W-1 && box.right <= W*(1-safe.right)+1 && box.top >= safe.top*H-1 && box.bottom <= H*(1-safe.bottom)+1,
            textFits: !(el instanceof HTMLElement) || (el.scrollWidth <= el.clientWidth+2 &&
              (getComputedStyle(el).overflowY === 'visible' || el.scrollHeight <= el.clientHeight+2)) };
        });
      }, { safe: variant.safeArea, W: variant.width, H: variant.height });
      const blank = variant.beats.some(b => b.intentionalBlank && t >= b.start && t < b.end);
      if (!blank && !boxes.length) errors.push(`No important visual visible at ${t.toFixed(3)}`);
      if (boxes.some(b => !b.fits || !b.textFits)) errors.push(`Important element outside safe area/overflow at ${t.toFixed(3)}`);
      const name = `t${t.toFixed(3)}.png`;
      await page.screenshot({ path: safeOutput(path.join('qa/frames', variant.id, name)) });
      frames.push({ time: t, path: path.relative(root, path.join(out, name)), boxes });
    }
    const t = variant.duration * .43;
    await seek(t);
    const first = hash(await page.screenshot());
    await seek(variant.duration * .91);
    await seek(.01);
    await seek(t);
    const repeated = hash(await page.screenshot());
    if (first !== repeated) errors.push('Out-of-order seek produced different pixels');
    report.variants.push({ id: variant.id, width: variant.width, height: variant.height,
      buildSha256: hash(fs.readFileSync(path.join(dir, 'build.json'))), frames, errors, reviewed: false });
    await page.close();
  }
} finally {
  await browser.close();
}
fs.mkdirSync(safeOutput('qa'), { recursive: true });
fs.writeFileSync(safeOutput('qa/probe.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report.variants.map(v => ({ id: v.id, frames: v.frames.length, errors: v.errors })), null, 2));
if (report.variants.some(v => v.errors.length)) process.exitCode = 1;
