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

// 4) 参阅材料生成逻辑实跑（不依赖浏览器，注入最小 DOM/依赖桩）
console.log('\n参阅材料生成实跑：');
const briefJs = fs.readFileSync(path.join(__dirname, 'brief_doc.js'), 'utf-8');
const stubEl = () => ({ style:{}, textContent:'', innerHTML:'', value:'',
  addEventListener(){}, classList:{ add(){}, remove(){}, toggle(){} } });
const bx = {
  window:{}, document:{}, $: stubEl,
  esc: s => String(s==null?'':s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
  fmtDist: m => m<1000 ? Math.round(m)+' 米' : (m/1000).toFixed(1)+' 公里',
  BRANCHES: {length:91}, DOC_CSS:'', toast(){},
  briefBar:stubEl(), briefDesc:stubEl(), briefActions:stubEl(), briefPreview:stubEl(), briefMask:stubEl(),
  lastQuery:null
};
vm.createContext(bx);
try { vm.runInContext(briefJs, bx); } catch(e){ console.log('  片段执行失败:', e.message); process.exitCode=1; }
const demoItems = [
  {branch:{name:'福建海峡银行(福州杨桥支行)',address:'福州市鼓楼区某路1号',phone:'0591-88888888'},dist:330},
  {branch:{name:'福建海峡银行(总行营业部)',address:'福州市台江区江滨中大道356号',phone:'400-893-9999'},dist:2100}
];
const demoNames = ['福建省财政厅','人民银行福建省分行','福州大学','福建省总工会','福州市中级人民法院','福建省人民医院','福州市行政服务中心'];
const frags = {};
let briefOk = true;
for (const nm of demoNames){
  bx.lastQuery = {name:nm, mode:'precise', region:{province:'福建省',city:'福州市',district:'鼓楼区'},
    geo:{title:nm,address:'福州市鼓楼区示例路1号',lat:26.09,lng:119.29}, items:demoItems};
  let frag, text, outline;
  try {
    frag = vm.runInContext('briefFragment(lastQuery)', bx);
    text = vm.runInContext('briefText(lastQuery)', bx);
    outline = vm.runInContext('briefOutline(lastQuery)', bx);
  } catch(e){ console.log(`  [${nm}] 运行异常:`, e.message); briefOk=false; continue; }
  frags[nm]=frag;
  const secs=(frag.match(/<h2 class="sec">/g)||[]).length;
  const cards=(frag.match(/class="coop-card"/g)||[]).length;
  const bad=['undefined','NaN','[object Object]'].filter(k=>frag.indexOf(k)>=0);
  const ok = secs===11 && cards===4 && frag.length>9000 && text.length>6000 &&
             frag.indexOf('行内参考 请勿外传')>=0 && frag.indexOf('附录 A')>=0 &&
             frag.indexOf('附录 B')>=0 && bad.length===0 && outline.length===11;
  if(!ok) briefOk=false;
  console.log(`  [${nm}] 章节${secs} 方向卡片${cards} HTML ${frag.length}字 文本 ${text.length}字 异常值[${bad.join(',')||'无'}] => ${ok?'通过':'失败'}`);
}
const distinct = new Set(Object.values(frags).map(f=>f.slice(
  f.indexOf('<h2 class="sec">三、业务场景'), f.indexOf('<h2 class="sec">四、机构业务'))));
console.log('  按机构差异化场景版本数:', distinct.size, '（应 >1）');
if(distinct.size<2) briefOk=false;
console.log('  参阅材料实跑:', briefOk?'通过':'失败');
if(!briefOk) process.exitCode=1;
