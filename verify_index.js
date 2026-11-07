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
const briefJs = ['org_struct.js','brief_doc.js'].map(n =>
  fs.readFileSync(path.join(__dirname, n), 'utf-8')).join('\n');
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
  const ok = secs===12 && cards===4 && frag.length>14000 && text.length>8500 &&
             frag.indexOf('行内参考 请勿外传')>=0 && frag.indexOf('附录 A')>=0 &&
             frag.indexOf('附录 B')>=0 && frag.indexOf('单位治理与组织画像')>=0 &&
             frag.indexOf('主要及相关负责人')>=0 && frag.indexOf('上级主管与业务指导单位')>=0 &&
             frag.indexOf('下属及归口管理单位')>=0 &&
             frag.indexOf('内设机构及职责分工')>=0 &&
             frag.indexOf('（七）官方核验直达入口')>=0 && frag.indexOf('site%3Agov.cn')>=0 &&
             frag.indexOf('gsxt.gov.cn')>=0 && frag.indexOf('creditchina.gov.cn')>=0 &&
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

// 5) 现场补录实跑：补录值须同步进入 HTML 预览与复制全文 / 下载同源内容
console.log('\n现场补录与全屏要素：');
let extraOk = true;
try {
  vm.runInContext('resetBriefFields()', bx);
  bx.lastQuery = {name:'福建省财政厅', mode:'precise', region:{province:'福建省',city:'福州市',district:'鼓楼区'},
    geo:{title:'福建省财政厅',address:'福州市鼓楼区示例路1号',lat:26.09,lng:119.29}, items:demoItems};
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


// 6) 两阶段编制：进度层要素、真实在线复核函数、在线复核结果写入材料实跑
console.log('\n两阶段编制与进度层：');
let stageOk = true;
const stageChecks = {
  '进度层弹窗': html.indexOf('id="progMask"') >= 0 && html.indexOf('class="mask mask--prog"') >= 0,
  '进度条与百分比': html.indexOf('id="progFill"') >= 0 && html.indexOf('id="progPct"') >= 0,
  '阶段清单容器': html.indexOf('id="progStages"') >= 0,
  '五个真实阶段': html.indexOf('var BRIEF_STAGES=') >= 0 &&
                  (html.match(/\{t:"[^"]+", d:"[^"]+", pct:/g)||[]).length === 5,
  '在线复核函数': html.indexOf('function placeVerify(') >= 0 &&
                  html.indexOf('apis.map.qq.com/ws/place/v1/suggestion') >= 0,
  '流水线与取消': html.indexOf('function runBriefPipeline(') >= 0 &&
                  html.indexOf('function cancelBriefPipeline(') >= 0 &&
                  html.indexOf('id="cancelProg"') >= 0,
  '两阶段按钮': html.indexOf('编制并查看参阅材料') >= 0 && html.indexOf('编制并下载材料') >= 0 &&
                html.indexOf('id="briefPill"') >= 0,
  '查询阶段不预生成全文': html.indexOf('briefPreview.innerHTML="";   // 两阶段') >= 0,
  '完成后弹出全文': html.indexOf('briefMask.classList.add("show")') >= 0,
  '如实边界声明': html.indexOf('不由页面在线核验') >= 0 &&
                  html.indexOf('不预置负责人姓名') >= 0,
  '旧一键生成已移除': html.indexOf('briefPreview.innerHTML=briefFragment(lastQuery);\n      briefPreview.scrollTop=0;\n      briefMask.classList.add("show")') < 0
};
Object.keys(stageChecks).forEach(k => {
  console.log('  ' + k + ':', stageChecks[k] ? '通过' : '失败');
  if(!stageChecks[k]) stageOk = false;
});

try {
  bx.lastQuery = {name:'福州市民族与宗教事务局', mode:'precise',
    region:{province:'福建省',city:'福州市',district:'鼓楼区'},
    geo:{title:'福州市民族与宗教事务局',address:'福州市鼓楼区福飞路井尾5号',lat:26.116998,lng:119.296707},
    items:demoItems,
    verify:{ok:true, time:'2026-11-07 17:30', d:{title:'福州市民族与宗教事务局',
      address:'福建省福州市鼓楼区福飞路井尾5号', province:'福建省', city:'福州市', district:'鼓楼区',
      adcode:350102, category:'机构团体:政府机关'}}};
  const vf = vm.runInContext('briefFragment(lastQuery)', bx);
  const vt = vm.runInContext('briefText(lastQuery)', bx);
  const vChecks = {
    '在线复核状态写入': vf.indexOf('页面在线复核（编制时）') >= 0,
    '行政区划代码写入': vf.indexOf('350102') >= 0,
    'POI 类别写入': vf.indexOf('机构团体:政府机关') >= 0,
    '复核来源标注': vf.indexOf('腾讯位置服务地点建议接口') >= 0,
    '纯文本同步': vt.indexOf('在线复核规范名称') >= 0 && vt.indexOf('350102') >= 0
  };
  Object.keys(vChecks).forEach(k => {
    console.log('  ' + k + ':', vChecks[k] ? '通过' : '失败');
    if(!vChecks[k]) stageOk = false;
  });
  // 降级路径：接口未返回结果时不得阻塞、不得虚构
  bx.lastQuery.verify = {ok:false, d:null, time:'2026-11-07 17:31'};
  const df = vm.runInContext('briefFragment(lastQuery)', bx);
  const downgrade = df.indexOf('未取得结果（接口未返回或超时）') >= 0 &&
                    df.indexOf('350102') < 0 && df.indexOf('undefined') < 0;
  console.log('  在线失败降级:', downgrade ? '通过' : '失败');
  if(!downgrade) stageOk = false;
} catch(e){ console.log('  在线复核实跑异常:', e.message); stageOk = false; }

console.log('  两阶段校验:', stageOk ? '通过' : '失败');
if(!stageOk) process.exitCode = 1;
