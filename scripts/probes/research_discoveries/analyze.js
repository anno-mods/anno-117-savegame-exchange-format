const _path = require('path');
const CONFIG = _path.resolve(__dirname, '..', '..', '..', 'data', 'raw', 'calculator_configs', 'Marcia 69.json');
const fs = require('fs');
global.window = {};
const src = fs.readFileSync('C:/dev/anno-117-calculator/js/params.js', 'utf8');
eval(src);
const params = window.params;
const effects = new Map(params.effects.map(e => [e.guid, e]));
const techs = params.techs || [];
const techByEffect = new Map();
for (const t of techs) for (const e of t.effects) techByEffect.set(e, t);
const patrons = params.patrons || [];
const patronByEffect = new Map();
for (const p of patrons) for (const le of (p.localEffects || [])) patronByEffect.set(le.effect, p);
const nm = o => o ? (o.locaText?.english || o.name) : '?';
const p = CONFIG;
const j = JSON.parse(fs.readFileSync(p, 'utf8'));
const ids = new Set();
function add(k, ctx) { const m = k.match(/effect\.(\d+)\.scaling|^(\d+)\.scaling$/); if (m) { const id = +(m[1] || m[2]); ids.add(id + '|' + ctx); } }
for (const k of Object.keys(JSON.parse(j.globalEffects))) add(k, 'global');
for (const k of Object.keys(JSON.parse(j.sessionSettings))) add(k, 'session');
for (const n of JSON.parse(j.islandNames).concat(['All Islands'])) for (const k of Object.keys(JSON.parse(j[n]))) add(k, 'island');
const byId = {};
for (const s of ids) { const [id, ctx] = s.split('|'); (byId[id] ||= new Set()).add(ctx); }
const out = [];
for (const id of Object.keys(byId).map(Number).sort((a, b) => a - b)) {
  const e = effects.get(id); const t = techByEffect.get(id); const pa = patronByEffect.get(id);
  const gv = JSON.parse(j.globalEffects)[id + '.scaling'];
  out.push([id, [...byId[id]].join(','), nm(e), e?.effectScope, e?.source, e?.effectDuration, t ? 'TECH ' + t.guid + ' ' + nm(t) + ' rep=' + t.isRepeatable : '', pa ? 'PATRON ' + nm(pa) : '', 'dlc=' + JSON.stringify(e?.dlcUnlocks || '')].join(' | '));
}
console.log(out.join('\n'));
console.log('techs:', techs.length, 'keys', Object.keys(techs[0]));
console.log('param top keys', Object.keys(params).join(','));
// all sessions
console.log(JSON.stringify(params.sessions.map(s => [s.guid, s.locaText?.english || s.name, s.region])));
