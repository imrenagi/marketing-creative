#!/usr/bin/env node
// Original construction examples: adapt their visual grammar to the actual brief.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const ownFile = fileURLToPath(import.meta.url);
const ownDir = path.dirname(ownFile);
const args = process.argv.slice(2);
const root = fs.realpathSync(path.resolve(args[0] || '.'));
const force = args.includes('--force');
const gsapAt = args.indexOf('--gsap');
const gsapFile = gsapAt < 0 ? null : args[gsapAt + 1];
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const json = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const esc = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const js = value => JSON.stringify(value).replaceAll('<', '\\u003c');
const local = relative => {
  if (path.isAbsolute(relative)) throw new Error('Expected project-relative asset');
  const result = fs.realpathSync(path.resolve(root, relative));
  if (!result.startsWith(root + path.sep)) throw new Error('Asset escapes project');
  return result;
};
const safeOutput = relative => {
  const result = path.resolve(root, relative);
  if (!result.startsWith(root + path.sep)) throw new Error('Output path escapes project');
  let current = root;
  for (const component of path.relative(root, result).split(path.sep)) {
    current = path.join(current, component);
    let info;
    try { info = fs.lstatSync(current); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
    if (info?.isSymbolicLink()) throw new Error('Symlink output path refused');
  }
  return result;
};

function art(visual, id, assets) {
  switch (visual.mode) {
    case 'type':
      return `<div id="${id}-shape" class="type-shape" data-qa-important><span aria-hidden="true">Aa</span></div>`;
    case 'ui-tour':
      return `<div id="${id}-panel" class="panel" data-qa-important><div class="panel-title">Illustrative task</div><div class="row"><i></i><span>Draft</span></div><div class="row"><i></i><span>Review</span></div><div class="button">Complete</div><div id="${id}-result" class="result">Done</div><div id="${id}-pointer" class="pointer"></div></div>`;
    case 'counter':
      return `<div class="number" id="${id}-number" data-qa-important>0</div>`;
    case 'collage': {
      const image = visual.asset ? assets.find(a => a.id === visual.asset) : null;
      return `<div class="collage">${[0, 1, 2].map((n) => `<div id="${id}-card-${n}" class="cutout cutout-${n}" data-qa-important>${image ? `<img src="${esc(image.path)}" alt="${esc(visual.text)}">` : `<svg viewBox="0 0 160 160" aria-hidden="true"><${n === 0 ? 'circle cx="80" cy="80" r="55"' : n === 1 ? 'rect x="25" y="25" width="110" height="110" rx="20"' : 'path d="M80 20L140 135H20Z"'} fill="currentColor"/></svg>`}</div>`).join('')}</div>`;
    }
    case 'stage':
      return `<svg class="stage-art" viewBox="0 0 600 400" data-qa-important role="img" aria-label="Illustrative character moves a prop"><path d="M30 340H570" stroke="currentColor" stroke-width="5"/><g id="${id}-actor"><circle cx="190" cy="115" r="35" fill="currentColor"/><path d="M190 155V255M190 180L250 220M190 185L140 220M190 255L150 335M190 255L225 335" stroke="currentColor" stroke-width="20" stroke-linecap="round" fill="none"/></g><rect id="${id}-prop" x="330" y="235" width="95" height="95" rx="18" fill="var(--accent)"/></svg>`;
    case 'image': {
      const image = assets.find(a => a.id === visual.asset);
      return `<img class="capture" src="${esc(image.path)}" alt="${esc(visual.alt || visual.text || 'Supplied image')}" data-qa-important>`;
    }
    case 'footage': return ''; // Placed at the root: no timed video inside a timed scene.
    default: throw new Error(`Unsupported visual mode ${visual.mode}`);
  }
}

function documentFor(project, variant, assets, voice, hasLocalGsap) {
  const { width: W, height: H, duration: D, safeArea: safe } = variant;
  const style = project.style || {};
  for (const value of Object.values(style)) {
    if (!/^#[0-9A-Fa-f]{6}$/.test(value)) throw new Error('Example style values must be six-digit hex colors');
  }
  const wide = W / H > 1.2;
  const square = W === H;
  const unit = Math.min(W, H);
  const targets = [], timeline = [], footage = [];
  const scenes = variant.beats.map((beat, i) => {
    const id = `b${i}`, start = beat.start, end = beat.end, hold = end - start;
    if (beat.intentionalBlank) return '';
    const visual = beat.visual;
    if (visual.mode.startsWith('custom:')) throw new Error('Run the project custom generator for custom visual modes');
    const entrance = Math.min(.38, hold * .22);
    targets.push(`${id}-art`);
    if (visual.text || visual.label) {
      targets.push(`${id}-copy`);
      timeline.push(`tl.fromTo("#${id}-copy",{opacity:0,y:22},{opacity:1,y:0,duration:${entrance},ease:"power3.out"},${start});`);
    }
    timeline.push(`tl.fromTo("#${id}-art",{opacity:0,scale:.94},{opacity:1,scale:1,duration:${entrance},ease:"power3.out"},${start});`);
    if (visual.mode === 'ui-tour') {
      targets.push(`${id}-pointer`, `${id}-result`);
      timeline.push(`tl.fromTo("#${id}-pointer",{x:0,y:0},{x:-90,y:45,duration:${hold * .3},ease:"power2.inOut"},${start + hold * .2});`);
      timeline.push(`tl.fromTo("#${id}-result",{opacity:0,y:12},{opacity:1,y:0,duration:${hold * .18},ease:"power3.out"},${start + hold * .53});`);
    }
    if (visual.mode === 'counter') {
      targets.push(`${id}-number`);
      timeline.push(`const count${i}={value:0};tl.fromTo(count${i},{value:0},{value:${visual.value},duration:${hold * .55},ease:"power2.out",onUpdate:()=>{document.getElementById("${id}-number").textContent=Math.round(count${i}.value).toLocaleString(${js(project.language)});}},${start});`);
    }
    if (visual.mode === 'collage') {
      for (let n = 0; n < 3; n++) {
        targets.push(`${id}-card-${n}`);
        timeline.push(`tl.fromTo("#${id}-card-${n}",{y:35,rotation:${(n-1)*-10},opacity:0},{y:0,rotation:${(n-1)*6},opacity:1,duration:${entrance},ease:"power3.out"},${start + n * hold * .1});`);
      }
    }
    if (visual.mode === 'stage') {
      targets.push(`${id}-actor`, `${id}-prop`);
      timeline.push(`tl.fromTo("#${id}-actor",{x:0},{x:80,duration:${hold * .5},ease:"power2.inOut"},${start});`);
      timeline.push(`tl.fromTo("#${id}-prop",{x:0},{x:60,duration:${hold * .25},ease:"power3.out"},${start + hold * .5});`);
    }
    if (visual.mode === 'footage') {
      const media = assets.find(a => a.id === visual.asset);
      const overlay = !!(visual.text || visual.label);
      const x = overlay && wide ? (safe.left + (1-safe.left-safe.right)*.52)*W : safe.left*W;
      const y = overlay && !wide ? (safe.top + (1-safe.top-safe.bottom)*.45)*H : safe.top*H;
      const width = W*(1-safe.right)-x;
      const height = H*(1-safe.bottom)-y;
      footage.push(`<video id="${id}-video" class="clip footage" src="${esc(media.path)}" ${visual.hasAudio ? 'data-has-audio="true"' : 'muted'} playsinline data-start="${start}" data-duration="${hold}" data-media-start="${visual.sourceStart || 0}" data-track-index="1" style="left:${x}px;top:${y}px;width:${width}px;height:${height}px" data-qa-important></video>`);
    }
    // Opacity on the inner scene is seekable; the framework owns timed parent visibility.
    const copy = visual.text || visual.label ? `<div class="copy" id="${id}-copy">${visual.text ? `<h1 data-qa-important>${esc(visual.text)}</h1>` : ''}${visual.label ? `<p data-qa-important>${esc(visual.label)}</p>` : ''}</div>` : '';
    return `<section id="${id}" class="clip" data-start="${start}" data-duration="${hold}" data-track-index="2"><div class="scene ${copy ? '' : 'media-only'}">${copy}<div class="art" id="${id}-art">${art(visual, id, assets)}</div></div></section>`;
  }).join('\n');
  const audio = voice ? `<audio id="narration" src="${esc(voice.audio)}" data-start="${voice.start || 0}" data-duration="${voice.duration}" data-track-index="10" data-volume="1"></audio>` : '';
  return `<!doctype html>
<html lang="${esc(project.language)}"><head><meta charset="utf-8"><meta name="viewport" content="width=${W},height=${H}"><title>${esc(project.id)} ${esc(variant.ratio)}</title>
<script src="${hasLocalGsap ? 'assets/runtime/gsap.min.js' : 'https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js'}"></script>
<style>
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:${style.background || '#101923'}}
#root{position:relative;width:100%;height:100%;overflow:hidden;--accent:${style.accent || '#FFBC69'};color:${style.foreground || '#F7F5EF'};font-family:system-ui,sans-serif}
.clip{position:absolute;inset:0}.scene{position:absolute;inset:${safe.top*100}% ${safe.right*100}% ${safe.bottom*100}% ${safe.left*100}%;display:grid;grid-template-${wide ? 'columns:1fr 1fr' : 'rows: minmax(0,.42fr) minmax(0,.58fr)'};gap:${unit*.035}px;align-items:center}
.copy{min-width:0;${wide ? '' : 'text-align:center;'} }h1{margin:0;font-size:${unit*(wide ? .07 : square ? .061 : .073)}px;line-height:1.07;letter-spacing:-.035em;overflow-wrap:anywhere}p{margin:${unit*.024}px 0 0;font-size:${unit*.03}px;line-height:1.25;opacity:.8;overflow-wrap:anywhere}
.art{display:flex;align-items:center;justify-content:center;min-height:0;min-width:0;height:100%;color:var(--accent)}
.media-only{grid-template-columns:1fr;grid-template-rows:1fr}.capture{display:block;max-width:100%;max-height:100%;object-fit:contain}.footage{position:absolute;object-fit:contain}
.type-shape{display:grid;place-items:center;width:${unit*.31}px;height:${unit*.31}px;border-radius:28%;background:var(--accent);color:${style.background || '#101923'};font-size:${unit*.14}px;font-weight:750}
.panel{position:relative;width:95%;max-width:${wide ? unit*.58 : unit*.66}px;height:${unit*.35}px;padding:${unit*.027}px;border:2px solid currentColor;border-radius:${unit*.02}px;font-size:${unit*.025}px;overflow:hidden}
.panel-title{font-weight:700;margin-bottom:${unit*.016}px}.row{display:flex;align-items:center;gap:12px;margin:12px 0}.row i{display:block;width:15px;height:15px;border:2px solid currentColor;border-radius:3px}.button{display:inline-block;padding:10px 25px;border-radius:9px;background:var(--accent);color:${style.background || '#101923'};margin-top:8px}.result{position:absolute;right:8%;top:32%;font-size:${unit*.043}px;font-weight:800}.pointer{position:absolute;left:66%;top:60%;width:20px;height:20px;background:currentColor;clip-path:polygon(0 0,100% 65%,55% 65%,40% 100%)}
.number{font-size:${unit*.24}px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1}
.collage{display:flex;align-items:center;justify-content:center;width:100%;gap:${unit*.012}px}.cutout{width:29%;max-width:${unit*.18}px;aspect-ratio:1;border:2px solid currentColor;border-radius:12px;padding:10px}.cutout svg,.cutout img{display:block;width:100%;height:100%;object-fit:contain}.stage-art{width:100%;max-width:${unit*.65}px;max-height:100%}
</style></head><body><div id="root" data-composition-id="main" data-start="0" data-width="${W}" data-height="${H}" data-duration="${D}">${footage.join('\n')}${scenes}${audio}</div>
<script>
const tl=gsap.timeline({paused:true});
${timeline.join('\n')}
window.__motionTargets=${js(targets)};
window.__motionBeats=${js(variant.beats.map(b => ({id:b.id,start:b.start,end:b.end,intentionalBlank:!!b.intentionalBlank})))};
window.__timelines["main"]=tl;
</script></body></html>\n`;
}

try {
  execFileSync('python3', [path.resolve(ownDir, '../../motion-video-producer/scripts/project.py'), 'validate', root], { stdio: 'pipe' });
  const project = json(path.join(root, 'project.json'));
  const timing = json(path.join(root, 'timing.resolved.json'));
  const manifest = json(path.join(root, 'assets/manifest.json'));
  const voice = project.voice ? { ...project.voice, duration: json(local(project.voice.alignment)).duration } : null;
  if (gsapAt >= 0 && (!gsapFile || !fs.statSync(gsapFile).isFile())) throw new Error('--gsap needs a local file');
  // Preflight all variants before writing any, including manually edited copied assets.
  for (const variant of timing.variants) {
    const dest = safeOutput(path.join('variants', variant.id));
    if (!fs.existsSync(dest)) continue;
    const prior = fs.existsSync(path.join(dest, 'build.json')) ? json(path.join(dest, 'build.json')) : null;
    if (!force && !prior && fs.existsSync(path.join(dest, 'index.html'))) throw new Error(`Untracked existing output ${variant.id}; preserve edits before --force`);
    for (const [relative, expected] of Object.entries(prior?.generatedHashes || {})) {
      const file = safeOutput(path.join('variants', variant.id, relative));
      if (!file.startsWith(dest + path.sep)) throw new Error('Invalid prior build path');
      if (!force && fs.existsSync(file) && hash(fs.readFileSync(file)) !== expected) throw new Error(`Edited output ${variant.id}/${relative}; reconcile before --force`);
    }
  }
  for (const variant of timing.variants) {
    const dest = safeOutput(path.join('variants', variant.id));
    fs.mkdirSync(dest, { recursive: true });
    const generated = [];
    const copyFile = (source, relative) => {
      const output = safeOutput(path.join('variants', variant.id, relative));
      if (!output.startsWith(dest + path.sep)) throw new Error('Output path escape');
      fs.mkdirSync(path.dirname(output), { recursive: true });
      fs.copyFileSync(source, output);
      generated.push(relative);
    };
    for (const asset of manifest.assets) copyFile(local(asset.path), asset.path);
    if (voice) copyFile(local(voice.audio), voice.audio);
    if (gsapFile) copyFile(path.resolve(gsapFile), 'assets/runtime/gsap.min.js');
    fs.writeFileSync(safeOutput(path.join('variants', variant.id, 'index.html')), documentFor(project, variant, manifest.assets, voice, !!gsapFile));
    generated.push('index.html');
    fs.writeFileSync(safeOutput(path.join('variants', variant.id, 'build.json')), JSON.stringify({ schemaVersion: 1, variant: variant.id,
      inputHashes: timing.inputHashes, timingSha256: hash(fs.readFileSync(path.join(root, 'timing.resolved.json'))),
      generatorSha256: hash(fs.readFileSync(ownFile)), generator: 'bundled-compose-v1', localRuntime: !!gsapFile,
      generatedHashes: Object.fromEntries(generated.map(file => [file, hash(fs.readFileSync(path.join(dest, file)))])) }, null, 2) + '\n');
    console.log(`Built ${variant.id}: ${variant.width}x${variant.height}, ${variant.duration}s`);
  }
} catch (error) {
  process.stderr.write(`compose: ${error.stderr?.toString().trim() || error.message}\n`);
  process.exitCode = 1;
}
