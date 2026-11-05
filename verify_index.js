// 校验生成的 index.html：内联脚本语法 + 核心逻辑复算
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf-8');

// 1) 抽取两段 <script> 做语法检查
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
console.log('内联 script 段数:', scripts.length);
let syntaxOk = true;
scripts.forEach((s, i) => {
  try { new vm.Script(s); } catch (e) { syntaxOk = false; console.log(`  第${i+1}段语法错误:`, e.message); }
});
console.log('语法检查:', syntaxOk ? '通过' : '失败');

// 2) 在沙箱中加载数据（前两段定义 window.*）
const sandbox = { window: {}, localStorage: { getItem(){return null;}, setItem(){}, removeItem(){} } };
vm.createContext(sandbox);
sandbox.window = sandbox; // window 即全局
vm.runInContext(scripts[0], sandbox); // 数据段
const REGIONS = sandbox.window.REGION_DATA || sandbox.REGION_DATA;
const PROV = sandbox.window.PROVINCE_OF_CITY || sandbox.PROVINCE_OF_CITY;
const B = sandbox.window.BRANCH_DATA || sandbox.BRANCH_DATA;
console.log('BRANCH_DATA 网点数:', B && B.branches ? B.branches.length : '缺失');
console.log('REGION_DATA 地市数:', Object.keys(REGIONS||{}).length);

// 3) 复算核心逻辑（移植 parseAddress + haversine）
function buildIndex(){
  const idx=[];
  Object.keys(REGIONS).forEach(c=>{ const prov=PROV[c]||'福建省';
    Object.keys(REGIONS[c]).forEach(d=>idx.push({name:d,city:c,province:prov,center:REGIONS[c][d]})); });
  idx.sort((a,b)=>b.name.length-a.name.length); return idx;
}
const DI=buildIndex();
const GOV=['人民政府','财政厅','教育厅','卫健委','公安厅','民政厅'];
function parse(t){
  if(!t||!t.trim()) return null; t=t.trim(); let m=null;
  for(const x of DI){ if(t.indexOf(x.name)!==-1){m=x;break;} }
  if(m) return {province:m.province,city:m.city,district:m.name,center:{lat:m.center[0],lng:m.center[1]},precision:'district'};
  const cities=Object.keys(REGIONS).sort((a,b)=>b.length-a.length); let ch=null;
  for(const c of cities){ if(t.indexOf(c)!==-1){ch=c;break;} }
  if(ch){ const ds=REGIONS[ch],ks=Object.keys(ds); let la=0,lo=0; ks.forEach(k=>{la+=ds[k][0];lo+=ds[k][1];});
    return {province:PROV[ch]||'福建省',city:ch,district:'',center:{lat:la/ks.length,lng:lo/ks.length},precision:'city'}; }
  for(const g of GOV){ if(t.indexOf(g)!==-1){ const f=REGIONS['福州市']['鼓楼区']; return {province:'福建省',city:'福州市',district:'鼓楼区',center:{lat:f[0],lng:f[1]},precision:'govhint'}; } }
  return null;
}
function haversine(la1,lo1,la2,lo2){ const R=6371000,dLa=(la2-la1)*Math.PI/180,dLo=(lo2-lo1)*Math.PI/180;
  const a=Math.sin(dLa/2)**2+Math.cos(la1*Math.PI/180)*Math.cos(la2*Math.PI/180)*Math.sin(dLo/2)**2;
  return 2*R*Math.asin(Math.sqrt(a)); }
function nearest(center){ let best=null,bd=Infinity;
  for(const b of B.branches){ const d=haversine(center.lat,center.lng,b.lat,b.lng); if(d<bd){bd=d;best=b;} }
  return {b:best,d:bd}; }

const cases=[
  ['福建省财政厅','govhint→鼓楼区'],
  ['福建省福州市鼓楼区华林路123号','district→鼓楼区'],
  ['厦门思明区','district→厦门'],
  ['温州市鹿城区车站大道','district→温州'],
  ['上海市浦东新区','未识别'],
];
console.log('\n逻辑复算：');
for(const [txt,expect] of cases){
  const p=parse(txt);
  if(!p){ console.log(`  [${txt}] => 未识别  (期望:${expect})`); continue; }
  const n=nearest(p.center);
  console.log(`  [${txt}]\n    识别:${p.province}/${p.city}/${p.district} (${p.precision})\n    最近:${n.b.name}  ${(n.d/1000).toFixed(2)}km  (期望:${expect})`);
}
