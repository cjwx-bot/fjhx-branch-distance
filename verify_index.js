// 校验生成的 index.html：内联脚本语法 / 最近网点复算 / 参阅材料实跑 /
// 技能全网检索资料库命中与未命中双路径 / 零 API 授权 / 公开级信息分级
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
if (!syntaxOk) process.exitCode = 1;

// 2) 在沙箱中加载数据（window.REGION_DATA / PROVINCE_OF_CITY / BRANCH_DATA / ORG_INTEL）
const sandbox = { window: {}, localStorage: { getItem(){return null;}, setItem(){}, removeItem(){} } };
vm.createContext(sandbox);
sandbox.window = sandbox;
vm.runInContext(scripts[0], sandbox);
const REGIONS = sandbox.window.REGION_DATA || sandbox.REGION_DATA;
const PROV = sandbox.window.PROVINCE_OF_CITY || sandbox.PROVINCE_OF_CITY;
const B = sandbox.window.BRANCH_DATA || sandbox.BRANCH_DATA;
const INTEL = sandbox.window.ORG_INTEL || {orgs:[]};
console.log('BRANCH_DATA 网点数:', B && B.branches ? B.branches.length : '缺失');
console.log('REGION_DATA 地市数:', Object.keys(REGIONS||{}).length);
console.log('ORG_INTEL 核验机构数:', (INTEL.orgs||[]).length);

// 3) 复算核心逻辑（parseAddress + haversine）
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
console.log('\n逻辑复算（行政区划近似路径）：');
for(const [txt,expect] of cases){
  const p=parse(txt);
  if(!p){ console.log(`  [${txt}] => 未识别  (期望:${expect})`); continue; }
  const n=nearest(p.center);
  console.log(`  [${txt}]\n    识别:${p.province}/${p.city}/${p.district} (${p.precision})\n    最近:${n.b.name}  ${(n.d/1000).toFixed(2)}km  (期望:${expect})`);
}

// 3b) 资料库真实坐标路径：按命中机构坐标复算最近网点
console.log('\n资料库真实坐标测距复算（零 API 授权）：');
let geoOk = true;
for (const o of (INTEL.orgs||[])) {
  const n = nearest({lat:o.geo.lat, lng:o.geo.lng});
  const ok = n.b && isFinite(n.d) && n.d >= 0;
  if(!ok) geoOk = false;
  console.log(`  [${o.name}] ${o.geo.lat},${o.geo.lng} → ${n.b.name} ${(n.d/1000).toFixed(2)}km ${ok?'通过':'失败'}`);
}
if(!geoOk) process.exitCode = 1;

// 4) 参阅材料生成逻辑实跑（注入最小 DOM/依赖桩 + 资料库片段）
console.log('\n参阅材料生成实跑：');
const briefJs = ['org_struct.js','brief_doc.js','intel_brief.js'].map(n =>
  fs.readFileSync(path.join(__dirname, n), 'utf-8')).join('\n');
const stubEl = () => ({ style:{}, textContent:'', innerHTML:'', value:'',
  addEventListener(){}, classList:{ add(){}, remove(){}, toggle(){} } });
const bx = {
  window:{ ORG_INTEL: INTEL }, document:{}, $: stubEl,
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
  bx.lastQuery = {name:nm, mode:'approx', region:{province:'福建省',city:'福州市',district:'鼓楼区'},
    geo:null, intel:null, items:demoItems};
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
  const ok = secs===12 && cards===4 && frag.length>14000 && text.length>8500 &&
             frag.indexOf('行内参考 请勿外传')>=0 && frag.indexOf('附录 A')>=0 &&
             frag.indexOf('附录 B')>=0 && frag.indexOf('单位治理与组织画像')>=0 &&
             frag.indexOf('主要及相关负责人')>=0 && frag.indexOf('上级主管与业务指导单位')>=0 &&
             frag.indexOf('下属及归口管理单位')>=0 &&
             frag.indexOf('内设机构及职责分工')>=0 &&
             frag.indexOf('（七）官方核验直达入口')>=0 && frag.indexOf('site%3Agov.cn')>=0 &&
             frag.indexOf('gsxt.gov.cn')>=0 && frag.indexOf('creditchina.gov.cn')>=0 &&
             frag.indexOf('资料库收录状态与补齐路径')>=0 &&
             text.indexOf('官方核验直达入口')>=0 &&
             bad.length===0 && outline.length===12;
  if(!ok) briefOk=false;
  console.log(`  [${nm}] 章节${secs} 方向卡片${cards} HTML ${frag.length}字 文本 ${text.length}字 异常值[${bad.join(',')||'无'}] => ${ok?'通过':'失败'}`);
}
const distinct = new Set(Object.values(frags).map(f=>f.slice(
  f.indexOf('<h2 class="sec">四、业务场景'), f.indexOf('<h2 class="sec">五、机构业务'))));
console.log('  按机构差异化场景版本数:', distinct.size, '（应 >1）');
if(distinct.size<2) briefOk=false;
console.log('  参阅材料实跑:', briefOk?'通过':'失败');
if(!briefOk) process.exitCode=1;

// 5) 现场补录实跑：补录值须同步进入 HTML 预览与复制全文
console.log('\n现场补录与全屏要素：');
let extraOk = true;
try {
  vm.runInContext('resetBriefFields()', bx);
  bx.lastQuery = {name:'福建省财政厅', mode:'approx', region:{province:'福建省',city:'福州市',district:'鼓楼区'},
    geo:null, intel:null, items:demoItems};
  const before = vm.runInContext('briefFragment(lastQuery)', bx);
  vm.runInContext('setBriefField("leader","补录校验姓名")', bx);
  vm.runInContext('setBriefField("superior","补录校验上级单位")', bx);
  vm.runInContext('setBriefField("subordinate","补录校验下属单位")', bx);
  const after = vm.runInContext('briefFragment(lastQuery)', bx);
  const txtAfter = vm.runInContext('briefText(lastQuery)', bx);
  const checks = {
    '补录前为待核实': before.indexOf('待核实（现场补录）') >= 0,
    '姓名写入预览': after.indexOf('补录校验姓名') >= 0,
    '上级单位写入预览': after.indexOf('补录校验上级单位') >= 0,
    '下属单位写入预览': after.indexOf('补录校验下属单位') >= 0,
    '姓名同步到复制全文': txtAfter.indexOf('补录校验姓名') >= 0,
    '状态变为已补录': after.indexOf('已补录（待复核）') >= 0
  };
  Object.keys(checks).forEach(k => { console.log('  ' + k + ':', checks[k] ? '通过' : '失败'); if(!checks[k]) extraOk = false; });
  vm.runInContext('resetBriefFields()', bx);
} catch(e){ console.log('  补录实跑异常:', e.message); extraOk = false; }

const pageChecks = {
  '全屏按钮': html.indexOf('id="fullscreenBrief"') >= 0,
  '全屏样式': html.indexOf('.sheet--doc.fs .doc') >= 0,
  '全屏切换逻辑': html.indexOf('function enterBriefFs()') >= 0 && html.indexOf('function exitBriefFs()') >= 0,
  '补录输入区': html.indexOf('id="briefFill"') >= 0,
  '补录字段映射': (html.match(/fill[A-Za-z]+:/g)||[]).length >= 7,
  '组织画像知识库': html.indexOf('var ORG_STRUCT=') >= 0,
  '章节标题': html.indexOf('三、单位治理与组织画像') >= 0 && html.indexOf('十、合规与风险提示') >= 0
};
Object.keys(pageChecks).forEach(k => { console.log('  ' + k + ':', pageChecks[k] ? '通过' : '失败'); if(!pageChecks[k]) extraOk = false; });
console.log('  补充校验:', extraOk ? '通过' : '失败');
if(!extraOk) process.exitCode = 1;

// 6) 两阶段编制 + 零 API 授权 + 技能资料库命中/未命中双路径
console.log('\n两阶段编制与零 API 授权：');
let stageOk = true;
const stageChecks = {
  '进度层弹窗': html.indexOf('id="progMask"') >= 0 && html.indexOf('class="mask mask--prog"') >= 0,
  '进度条与百分比': html.indexOf('id="progFill"') >= 0 && html.indexOf('id="progPct"') >= 0,
  '阶段清单容器': html.indexOf('id="progStages"') >= 0,
  '五个真实阶段': html.indexOf('var BRIEF_STAGES=') >= 0 &&
                  (html.match(/\{t:"[^"]+", d:"[^"]+", pct:/g)||[]).length === 5,
  '阶段②为资料库匹配': html.indexOf('匹配技能全网检索核验资料库') >= 0,
  '资料库查找与渲染函数': ['function lookupIntel(', 'function intelProfileSection(',
                        'function intelEvidenceHtml(', 'function intelMissingHtml('].every(x => html.indexOf(x) >= 0),
  '流水线与取消': html.indexOf('function runBriefPipeline(') >= 0 &&
                  html.indexOf('function cancelBriefPipeline(') >= 0 &&
                  html.indexOf('id="cancelProg"') >= 0,
  '两阶段按钮': html.indexOf('编制并查看参阅材料') >= 0 && html.indexOf('编制并下载材料') >= 0 &&
                html.indexOf('id="briefPill"') >= 0,
  '查询阶段不预生成全文': html.indexOf('briefPreview.innerHTML="";   // 两阶段') >= 0,
  '完成后弹出全文': html.indexOf('briefMask.classList.add("show")') >= 0,
  '零 API 授权声明': html.indexOf('零 API 授权') >= 0 && html.indexOf('不发起外部网络请求') >= 0,
  '无地图接口残留': html.indexOf('apis.map.qq.com') < 0 &&
                    html.indexOf('function placeVerify(') < 0 &&
                    html.indexOf('String.fromCharCode') < 0 &&
                    html.indexOf('MAP_KEY') < 0 &&
                    html.indexOf('jsonp(') < 0,
  '无明文地图 Key': !/I7GBZ-[A-Z0-9-]{20,}/.test(html),
  '资料库已内联': html.indexOf('window.ORG_INTEL =') >= 0,
  '如实收录状态': html.indexOf('资料库未收录') >= 0 && html.indexOf('全网检索补齐') >= 0,
  '旧一键生成已移除': html.indexOf('briefPreview.innerHTML=briefFragment(lastQuery);\n      briefPreview.scrollTop=0;\n      briefMask.classList.add("show")') < 0
};
Object.keys(stageChecks).forEach(k => {
  console.log('  ' + k + ':', stageChecks[k] ? '通过' : '失败');
  if(!stageChecks[k]) stageOk = false;
});

// 6b) 命中资料库：第三章须为已核验事实 + 证据索引，且不得残留旧在线复核口径
try {
  const o = (INTEL.orgs||[]).find(x => x.id === 'fz-mzj');
  if(!o) throw new Error('资料库缺少 fz-mzj');
  bx.lastQuery = {name:'福州市民宗局', mode:'intel',
    region:{province:'福建省',city:'福州市',district:'鼓楼区'},
    geo:{title:o.name,address:'福州市鼓楼区福飞路井尾5号',lat:o.geo.lat,lng:o.geo.lng},
    intel:o, items:demoItems};
  const hf = vm.runInContext('briefFragment(lastQuery)', bx);
  const ht = vm.runInContext('briefText(lastQuery)', bx);
  const secs = (hf.match(/<h2 class="sec">/g)||[]).length;
  const hitChecks = {
    '章节数仍为 12': secs === 12,
    '命中资料库标注': hf.indexOf('技能全网检索核验资料库') >= 0 && hf.indexOf('已命中') >= 0,
    '规范全称与信用代码': hf.indexOf('113501007380396651') >= 0 && hf.indexOf(o.name) >= 0,
    '官方地址写入': hf.indexOf('福飞路井尾5号') >= 0,
    '内设机构真实名称': hf.indexOf('宗教事务三处') >= 0 && hf.indexOf('政策法规处') >= 0,
    '下属单位真实名称': hf.indexOf('福州市民族宗教事务服务中心') >= 0,
    '上级归口真实名称': hf.indexOf('中共福州市委统战部') >= 0,
    '证据索引与官方来源': hf.indexOf('（八）全网检索证据索引') >= 0 && hf.indexOf('fuzhou.gov.cn') >= 0,
    '核验状态可追溯': hf.indexOf('官方页面直接载明') >= 0 && hf.indexOf('未检索到公开可核验信息') >= 0,
    '纯文本同步证据': ht.indexOf('全网检索证据索引') >= 0 && ht.indexOf('fuzhou.gov.cn') >= 0,
    '无旧在线复核口径': hf.indexOf('腾讯位置服务地点建议接口') < 0 && hf.indexOf('页面在线复核（编制时）') < 0,
    '无异常值': ['undefined','NaN','[object Object]'].every(k => hf.indexOf(k) < 0),
    '密级标识': hf.indexOf('行内参考 请勿外传') >= 0
  };
  Object.keys(hitChecks).forEach(k => {
    console.log('  命中路径 · ' + k + ':', hitChecks[k] ? '通过' : '失败');
    if(!hitChecks[k]) stageOk = false;
  });
  // 未命中路径：不得串扰已核验事实，且如实标注补齐路径
  bx.lastQuery = {name:'某未收录单位', mode:'approx',
    region:{province:'福建省',city:'福州市',district:'鼓楼区'}, geo:null, intel:null, items:demoItems};
  const mf = vm.runInContext('briefFragment(lastQuery)', bx);
  const missChecks = {
    '如实标注未收录': mf.indexOf('资料库收录状态与补齐路径') >= 0 && mf.indexOf('尚未纳入技能全网检索核验资料库') >= 0,
    '不串扰他人事实': mf.indexOf('113501007380396651') < 0 && mf.indexOf('福州市民族宗教事务服务中心') < 0,
    '保留官方核验入口': mf.indexOf('（七）官方核验直达入口') >= 0
  };
  Object.keys(missChecks).forEach(k => {
    console.log('  未命中路径 · ' + k + ':', missChecks[k] ? '通过' : '失败');
    if(!missChecks[k]) stageOk = false;
  });
} catch(e){ console.log('  资料库路径实跑异常:', e.message); stageOk = false; }

console.log('  两阶段与资料库校验:', stageOk ? '通过' : '失败');
if(!stageOk) process.exitCode = 1;

// 7) 信息分级：公开级资料库不得含内部级资料库中的自然人姓名
console.log('\n信息分级与资料库完整性：');
let gradeOk = true;
try {
  const pubRaw = fs.readFileSync(path.join(__dirname, 'intel', 'org_intel.json'), 'utf-8');
  const localRaw = fs.readFileSync(path.join(__dirname, '..', 'intel', 'org_intel_local.json'), 'utf-8');
  const local = JSON.parse(localRaw);
  const names = [];
  (local.orgs||[]).forEach(o => (o.leaders||[]).forEach(l => { if(l.name) names.push(l.name); }));
  const leaked = names.filter(n => pubRaw.indexOf(n) >= 0);
  const gradeChecks = {
    '内部级资料库存在': (local.orgs||[]).length >= 4,
    '公开级不含领导姓名': leaked.length === 0,
    '公开级标注信息分级': pubRaw.indexOf('不含自然人姓名') >= 0 && html.indexOf('最小必要原则') >= 0,
    '公开级来源可追溯': (INTEL.orgs||[]).every(o => Object.keys(o.sources||{}).length >= 4),
    '公开级坐标齐备': (INTEL.orgs||[]).every(o => typeof o.geo.lat === 'number' && typeof o.geo.lng === 'number'),
    '公开级含未核验字段': (INTEL.orgs||[]).some(o => Object.keys(o.fields||{}).some(k => o.fields[k].s === 'unverified'))
  };
  Object.keys(gradeChecks).forEach(k => {
    console.log('  ' + k + ':', gradeChecks[k] ? '通过' : '失败');
    if(!gradeChecks[k]) gradeOk = false;
  });
  if(leaked.length) console.log('  泄漏姓名:', leaked.join('、'));
} catch(e){ console.log('  分级校验异常:', e.message); gradeOk = false; }
console.log('  分级校验:', gradeOk ? '通过' : '失败');
if(!gradeOk) process.exitCode = 1;
