const _path = require('path');
const CONFIG = _path.resolve(__dirname, '..', '..', '..', 'data', 'raw', 'calculator_configs', 'Marcia 69.json');
const fs=require('fs');global.window={};eval(fs.readFileSync('C:/dev/anno-117-calculator/js/params.js','utf8'));const P=window.params;
const j=JSON.parse(fs.readFileSync(CONFIG,'utf8'));
const ge=JSON.parse(j.globalEffects);
const fert=new Map(P.fertilities.map(f=>[f.guid,f.locaText?.english||f.name]));
console.log('keys',Object.keys(P.areaBuffs[0]));
for(const a of P.areaBuffs){console.log(JSON.stringify({guid:a.guid,name:a.locaText?.english||a.name,raw:a.name,fertilityPercent:a.fertilityPercent,addedFertility:a.addedFertility,fert:fert.get(a.addedFertility),icon:a.iconPath,rest:Object.fromEntries(Object.entries(a).filter(([k])=>!['guid','name','locaText','fertilityPercent','addedFertility','iconPath'].includes(k)))}),'MARCIA=',ge[a.guid+'.scaling']);}
console.log('fertilities',JSON.stringify(P.fertilities.map(f=>[f.guid,f.locaText?.english])));
// effects/buffs adding fertility
const bm=new Map(P.buildingBuffs.map(b=>[b.guid,b]));
for(const e of P.effects){for(const b of e.buffs){const bb=bm.get(b);if(bb&&bb.addedFertility)console.log('effect w/ addedFertility',e.guid,e.locaText?.english,e.source,e.effectScope,bb.addedFertility,bb.fertilityPercent)}}
