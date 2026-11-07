// Dumps the calculator game data (js/params.js, assigns window.params) to <ANNO_OUT>/params.json.
// Usage: node dump_params.js [calculator-repo] [out-dir]
//   defaults: env ANNO_CALC_REPO (else ../../../anno-117-calculator), env ANNO_OUT (else ../../outputs)
const fs = require('fs');
const path = require('path');

const calc = process.argv[2] || process.env.ANNO_CALC_REPO || path.resolve(__dirname, '..', '..', '..', 'anno-117-calculator');
const out = process.argv[3] || process.env.ANNO_OUT || path.resolve(__dirname, '..', '..', 'outputs');

global.window = {};
const src = fs.readFileSync(path.join(calc, 'js', 'params.js'), 'utf8');
new Function('window', src)(global.window);
const p = global.window.params;
fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, 'params.json'), JSON.stringify(p));
for (const k of Object.keys(p)) console.log(k, Array.isArray(p[k]) ? p[k].length : typeof p[k]);
