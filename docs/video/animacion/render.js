// Render the animation frame by frame with headless Chrome.
//   node render.js <puppeteer-core dir> <frames dir> [workers] [t1,t2,...]
// With a list of times it only writes those frames (for checking); otherwise every frame of the timeline.
const path = require('path');
const fs = require('fs');
const puppeteer = require(path.join(process.argv[2], 'node_modules', 'puppeteer-core'));
const out = process.argv[3];
const workers = parseInt(process.argv[4] || '6', 10);
const only = process.argv[5] ? process.argv[5].split(',').map(Number) : null;
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const page = 'file://' + path.join(__dirname, 'index.html');

(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true,
    args: ['--no-first-run', '--allow-file-access-from-files', '--hide-scrollbars', '--force-device-scale-factor=1'],
    defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 1 } });
  const first = await browser.newPage();
  await first.goto(page, { waitUntil: 'load' });
  const tl = await first.evaluate(() => window.TL);
  const frames = only ? only.map(t => ({ t, name: `t_${t.toFixed(2)}.png` }))
    : Array.from({ length: Math.round(tl.total * tl.fps) }, (_, i) => ({ t: i / tl.fps, name: `f_${String(i).padStart(5, '0')}.jpg` }));
  const pages = [first];
  for (let i = 1; i < Math.min(workers, frames.length); i++) { const p = await browser.newPage(); await p.goto(page, { waitUntil: 'load' }); pages.push(p); }
  let next = 0, done = 0;
  await Promise.all(pages.map(async p => {
    await p.evaluate(() => Promise.all([...document.images].map(img => img.decode().catch(() => null))));
    for (;;) {
      const i = next++; if (i >= frames.length) break;
      const f = frames[i];
      await p.evaluate(async t => { await window.seek(t); }, f.t);
      await p.screenshot(only ? { path: path.join(out, f.name) } : { path: path.join(out, f.name), type: 'jpeg', quality: 93 });
      if (++done % 300 === 0) console.log(`${done}/${frames.length}`);
    }
  }));
  console.log(`frames: ${frames.length}, total ${tl.total}s`);
  await browser.close();
})().catch(e => { console.error('ERR', e); process.exit(1); });
