// Loads a calculator config dump into the calculator (static copy of the repo) in headless Chromium and prints computed values.
// Usage: node run_calc.js <old-config.json> <new-config.json> <result.json>
// Environment: ANNO_CALC_REPO = calculator checkout (static files are served from it, Playwright is loaded from its
//              node_modules; default ../../../anno-117-calculator), ANNO_CALC_PORT (default 8217).
const fs = require('fs');
const path = require('path');
const http = require('http');

const ROOT = process.env.ANNO_CALC_REPO || path.resolve(__dirname, '..', '..', '..', 'anno-117-calculator');
const { chromium } = require(path.join(ROOT, 'node_modules', 'playwright'));
const PORT = parseInt(process.env.ANNO_CALC_PORT || '8217', 10);
const types = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp', '.json': 'application/json', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.svg': 'image/svg+xml', '.ico': 'image/x-icon' };

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      let p = decodeURIComponent(req.url.split('?')[0]);
      if (p === '/') p = '/index.html';
      const f = path.join(ROOT, p);
      if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end(); return; }
      res.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      fs.createReadStream(f).pipe(res);
    }).listen(PORT, () => resolve(srv));
  });
}

async function ready(page) { for (let i = 0; i < 60; i++) { const ok = await page.evaluate(() => !!(window.view && window.view.island && window.view.island())).catch(() => false); if (ok) return; await new Promise(r => setTimeout(r, 1000)); } throw new Error('not ready'); }
async function run(browser, label, cfgPath) {
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  const page = await browser.newPage(); const ctx = page;
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text().slice(0, 300)); });
  page.on('pageerror', (e) => errors.push('pageerror: ' + String(e).slice(0, 300)));
  await page.goto(`http://localhost:${PORT}/`, { waitUntil: 'domcontentloaded' });
  await ready(page);
  await page.evaluate((c) => { localStorage.clear(); for (const k of Object.keys(c)) localStorage.setItem(k, c[k]); }, cfg);
  await page.reload({ waitUntil: 'domcontentloaded' });
  try {
    await ready(page);
  } catch (e) {
    return { label, fatal: 'init after config load timed out', errors, state: await page.evaluate(() => ({ view: typeof window.view, ls: localStorage.length })) };
  }
  await page.waitForTimeout(3000);
  const result = await page.evaluate(() => {
    const out = { islands: {}, routes: 0, defaultTrade: 0 };
    const v = window.view;
    out.routes = v.tradeManager.routes().length;
    out.defaultTrade = v.tradeManager.routes().filter((r) => r.isDefaultSupplier()).length;
    for (const isl of v.islands()) {
      try {
        const name = isl.name();
        const o = { session: isl.session && isl.session.guid };
        o.patron = isl.selectedPatron() ? isl.selectedPatron().guid : null;
        o.devotion = isl.devotion();
        o.constructedFactories = isl.factories.reduce((s, f) => s + (f.buildings.constructed() || 0), 0);
        o.requiredFactories = +isl.factories.reduce((s, f) => s + (f.buildings.required() || 0), 0).toFixed(3);
        o.constructedResidences = isl.residenceBuildings.reduce((s, b) => s + (b.buildings.constructed() || 0), 0);
        o.residents = isl.populationLevels.reduce((s, l) => s + (l.residents() || 0), 0);
        o.workforce = +isl.workforce.reduce((s, w) => s + (w.required ? (w.required() || 0) : 0), 0).toFixed(2);
        o.itemsOn = isl.items.reduce((s, it) => { let n = 0; for (const [f, st] of it.slotStates) if (st() > 0) n++; return s + n; }, 0);
        o.aqueductOn = isl.factories.filter((f) => f.aqueductBuff && f.aqueductBuff.scaling() > 0).length;
        o.modulesOn = isl.factories.reduce((s, f) => s + f.modules.filter((m) => m.checked()).length, 0);
        o.fertilityOff = [...isl.islandFertilities.values()].filter((x) => !x.checked()).length;
        o.needsOff = isl.populationLevels.reduce((s, l) => s + l.needs.filter((n) => n.available() && !n.checked()).length, 0);
        o.tradeIn = isl.products.reduce((s, p) => s + p.tradeList.routes().filter((r) => !r.isExport(p.tradeList)).length, 0);
        o.tradeOut = isl.products.reduce((s, p) => s + p.tradeList.routes().filter((r) => r.isExport(p.tradeList)).length, 0);
        out.islands[name] = o;
      } catch (e) { out.islands['ERR ' + String(e).slice(0, 80)] = {}; }
    }
    return out;
  });
  const stored = await page.evaluate(() => ({ n: localStorage.length, tr: JSON.parse(localStorage.getItem('tradeRoutes') || '[]').length }));
  await page.close();
  return { label, errors, result, stored };
}

(async () => {
  const srv = await serve();
  const browser = await chromium.launch({ headless: true });
  const outs = [];
  for (const [label, p] of [['old', process.argv[2]], ['new', process.argv[3]]]) {
    try { outs.push(await run(browser, label, p)); } catch (e) { outs.push({ label, fatal: String(e) }); }
  }
  await browser.close();
  srv.close();
  fs.writeFileSync(process.argv[4], JSON.stringify(outs, null, 1));
  for (const o of outs) console.log(o.label, o.fatal || '', 'errors:', (o.errors || []).length, o.errors ? o.errors.slice(0, 5) : '', 'routes loaded', o.result && o.result.routes, 'default', o.result && o.result.defaultTrade, 'stored', JSON.stringify(o.stored));
})();



