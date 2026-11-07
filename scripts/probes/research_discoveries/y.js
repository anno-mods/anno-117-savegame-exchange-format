const fs=require('fs');global.window={};eval(fs.readFileSync('C:/dev/anno-117-calculator/js/params.js','utf8'));const P=window.params;
for(const id of [155627,182638,157020,145097,151268,144988,145106,145107]) console.log(id, JSON.stringify(P.effects.find(x=>x.guid===id)||'noeffect').slice(0,200));
const pat=P.patrons.map(p=>[p.guid,p.locaText.english,p.wonder,(p.localEffects||[]).map(l=>l.effect)]);console.log(JSON.stringify(pat));
