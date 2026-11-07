const fs=require('fs');global.window={};eval(fs.readFileSync('C:/dev/anno-117-calculator/js/params.js','utf8'));const P=window.params;
const ids=[145095,148043,145099,155616,43620,50262,82017,183157];
const bmap=new Map(P.buildingBuffs.map(b=>[b.guid,b]));
for(const id of ids){const e=P.effects.find(x=>x.guid===id);console.log(id,JSON.stringify({...e,locaText:e.locaText?.english}).slice(0,600));
 for(const b of e.buffs){const bb=bmap.get(b);console.log('   buff',b,JSON.stringify(bb).slice(0,400));}}
console.log(JSON.stringify(P.techs.map(t=>[t.guid,t.locaText.english,t.isRepeatable,t.effects])));
console.log(JSON.stringify(P.sessions[1]).slice(0,800));
console.log(P.constants?JSON.stringify(P.constants).slice(0,500):'');
