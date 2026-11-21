/**
 * 高德地图开放平台 Web服务 API 定位通道（地图数据源白名单 / GCJ-02）
 *
 * 合规要点：
 * - Key 仅从服务端环境变量读取，绝不写入前端产物、绝不回传响应、绝不写入日志；
 * - 页面只调同源 /api/geo，不直连任何地图域名、不携带任何凭据；
 * - 未配置 Key、密钥无效、限流、超时、无 POI、坐标超出福建/温州包围盒时，
 *   一律如实返回 found:false 并附 reason，由前端降级到行政区划中心近似，绝不伪造坐标。
 *
 * 接口（官方文档）：
 *   /v3/place/text        关键词 POI 检索，location 为 "lng,lat"
 *   /v3/assistant/inputtips 输入提示，作为 POI 检索未命中时的第二级
 *   /v3/geocode/geo       地理编码兜底，且拒绝只解析到省市/区县粗粒度的结果
 */
const CACHE_TTL = 24 * 60 * 60 * 1000;   // 24h 缓存，降低配额消耗
const cache = new Map();

// 福建全省 + 浙江温州的业务覆盖包围盒，过滤同名异地 POI
const BBOX = { minLat: 23.0, maxLat: 28.9, minLng: 115.4, maxLng: 121.3 };
// 个人开发者 Key 存在 QPS 限流（实测 CUQPS_HAS_EXCEEDED_THE_LIMIT），串行节流
const MIN_GAP = 420;
const MIN_SCORE = 40;

let chain = Promise.resolve();
let lastAt = 0;
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

function inScope(lat, lng) {
  return lat >= BBOX.minLat && lat <= BBOX.maxLat && lng >= BBOX.minLng && lng <= BBOX.maxLng;
}

function normName(name) {
  return String(name == null ? "" : name).trim().slice(0, 60);
}

/** 串行节流：保证相邻上游请求至少间隔 MIN_GAP 毫秒 */
function throttle() {
  const job = chain.then(() => {
    const wait = MIN_GAP - (Date.now() - lastAt);
    return wait > 0 ? sleep(wait) : null;
  }).then(() => { lastAt = Date.now(); });
  chain = job.catch(() => {});
  return job;
}

async function fetchJSON(url, timeoutMs, fetchImpl) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const r = await (fetchImpl || fetch)(url, { signal: ctrl.signal });
    if (!r || !r.ok) return { __http: r ? r.status : 0 };
    return await r.json();
  } finally {
    clearTimeout(timer);
  }
}

/** 高德 location 字段为 "lng,lat"，与腾讯/前端的 {lat,lng} 顺序相反 */
function parseLocation(s) {
  const p = String(s == null ? "" : s).split(",");
  if (p.length !== 2) return null;
  const lng = Number(p[0]), lat = Number(p[1]);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  return { lat, lng };
}

/** 一次上游请求：密钥错误直接判定，QPS 限流退避一次 */
async function request(path, params, key, timeout, fetchImpl, skipThrottle) {
  const qs = Object.keys(params).map(k =>
    encodeURIComponent(k) + "=" + encodeURIComponent(params[k])).join("&");
  const url = "https://restapi.amap.com" + path + "?" + qs +
    "&output=json&key=" + encodeURIComponent(key);
  for (let attempt = 0; attempt < 2; attempt++) {
    if (!skipThrottle) await throttle();
    let j;
    try { j = await fetchJSON(url, timeout, fetchImpl); }
    catch (e) { return { __net: true }; }
    const info = String((j && j.info) || "");
    if (/INVALID_USER_KEY|USERKEY_PLAT_NOMATCH|INVALID_USER_SIGNATURE|INVALID_PARAMS/i.test(info)) {
      return { __badkey: true };
    }
    if (/CUQPS_HAS_EXCEEDED|DAILY_QUERY_OVER_LIMIT|ACCESS_TOO_FREQUENT|USER_DAILY_QUERY_OVER_LIMIT/i.test(info)) {
      if (attempt === 0) {
        if (!skipThrottle) await sleep(700);
        continue;
      }
      return { __limited: true };
    }
    return j;
  }
  return { __limited: true };
}

const clean = (s) => String(s == null ? "" : s).replace(/[\s()（）·\-、,，.。]/g, "");
const GOOD = /政府机构及社会团体|政府机关|事业单位|科教文化服务|学校|高等院校|科研机构|社会团体|公检法/;
const BAD = /医疗保健|医院|诊所|停车|住宅|宿舍|楼宇|写字楼|出入口|门$|地铁|公交|房产小区|酒店|宾馆|购物|餐饮|风景名胜|附属设施|生活服务|公司企业|地名地址|营业厅|ATM|收费站|加油站/;

/** 名称相似度：无关联（0 分）一律不采信，避免把无关 POI 当成目标机构 */
function sim(title, query) {
  const t = clean(title), q = clean(query);
  if (!t || !q) return 0;
  if (t === q) return 100;
  if (t.indexOf(q) === 0) return 80 - Math.min(30, t.length - q.length);
  if (q.indexOf(t) === 0 && t.length >= 4) return 60;
  if (t.indexOf(q) > 0) return 45 - Math.min(25, t.length - q.length);
  if (q.indexOf(t) > 0 && t.length >= 4) return 55 - Math.min(25, q.length - t.length);
  return 0;
}

/** 名称结构加权：校区本体优先，附属楼宇/学院/医院/交通设施降权 */
function titleBonus(title) {
  const t = clean(title);
  if (/附属医院|医院|卫生所|诊所/.test(t)) return -80;
  if (/楼|馆|园|学院|系|中心|食堂|宿舍|地铁站|停车场|车站|大门|西门|东门|南门|北门|出入口|服务部|营业部|支行/.test(t)) return -35;
  if (/校区/.test(t)) return 15;
  return 0;
}

function score(title, query, category, categoryBonus) {
  const s = sim(title, query);
  if (s <= 0) return null;
  const cat = String(category || "");
  const catScore = categoryBonus == null
    ? (GOOD.test(cat) ? 40 : 0) - (BAD.test(cat) ? 60 : 0)
    : categoryBonus;
  return s + catScore + titleBonus(title);
}

/** inputtips 的 typecode 为数字编码：13xxxx 政府机关 / 14xxxx 科教文化加分，其余降权 */
function tipBonus(code) {
  const c = String(code || "");
  if (/^13|^14/.test(c)) return 40;
  if (/^12|^15|^99|^09|^10|^11/.test(c)) return -60;
  return 0;
}

function splitAdname(s) {
  const t = String(s || "");
  const pm = t.match(/^(.{2,4}?省)/);
  const province = pm ? pm[1] : "";
  const rest = province ? t.slice(province.length) : t;
  const cm = rest.match(/^(.{2,6}?市)/);
  const city = cm ? cm[1] : "";
  return { province, city, district: city ? rest.slice(city.length) : rest };
}

function geoOf(loc, x, source) {
  return {
    lat: loc.lat, lng: loc.lng,
    title: String(x.name || x.title || ""),
    address: String(x.address || x.formatted_address || ""),
    province: String(x.pname || ""),
    city: String(x.cityname || ""),
    district: String(x.adname || x.district || ""),
    category: String(x.type || x.typecode || ""),
    source
  };
}

/** /v3/place/text：按机构名称取 POI 真实坐标 */
function pickPlaceText(j, query) {
  if (!j || String(j.status) !== "1" || !Array.isArray(j.pois)) return null;
  const arr = [];
  j.pois.forEach(x => {
    if (!x) return;
    const loc = parseLocation(x.location);
    if (!loc || !inScope(loc.lat, loc.lng)) return;
    const s = score(x.name, query, x.type);
    if (s === null) return;
    arr.push({ x, loc, s });
  });
  if (!arr.length) return null;
  arr.sort((a, b) => b.s - a.s);
  if (arr[0].s < MIN_SCORE) return null;
  const g = geoOf(arr[0].loc, arr[0].x, "amap-place-text");
  return g;
}

/** /v3/assistant/inputtips：POI 检索未命中时的第二级 */
function pickInputtips(j, query) {
  if (!j || String(j.status) !== "1" || !Array.isArray(j.tips)) return null;
  const arr = [];
  j.tips.forEach(x => {
    if (!x) return;
    const loc = parseLocation(x.location);
    if (!loc || !inScope(loc.lat, loc.lng)) return;
    const code = x.typecode || x.type || "";
    const s = score(x.name, query, "", tipBonus(code));
    if (s === null) return;
    arr.push({ x, loc, s, cat: String(code) });
  });
  if (!arr.length) return null;
  arr.sort((a, b) => b.s - a.s);
  if (arr[0].s < MIN_SCORE) return null;
  const g = geoOf(arr[0].loc, arr[0].x, "amap-inputtips");
  const ad = splitAdname(arr[0].x.adname);
  g.province = ad.province; g.city = ad.city; g.district = ad.district;
  g.category = arr[0].cat;
  return g;
}

/** /v3/geocode/geo：地址兜底；拒绝只解析到省/市/区县等粗粒度的结果，且编码地址必须与查询词相关 */
function pickGeocode(j, q) {
  if (!j || String(j.status) !== "1" || !Array.isArray(j.geocodes)) return null;
  const qc = clean(q || "");
  for (const x of j.geocodes) {
    if (!x) continue;
    const loc = parseLocation(x.location);
    if (!loc || !inScope(loc.lat, loc.lng)) continue;
    if (!/兴趣点|门牌号|楼宇|单元|房屋|道路|大厦|园区/.test(String(x.level || ""))) continue;
    // 诚信护栏：地理编码结果必须包含查询词本体，避免把无关/乱码地址当真实坐标采信
    if (qc && clean(x.formatted_address || "").indexOf(qc) === -1) continue;
    const g = geoOf(loc, {
      name: "", address: x.formatted_address || "",
      pname: x.province || "", cityname: x.city || "", adname: x.district || "",
      type: "地理编码（" + String(x.level || "") + "）"
    }, "amap-geocode");
    return g;
  }
  return null;
}

/**
 * @param {string} name 机构名称
 * @param {object} opts { key, region, timeout }
 * @param {object} deps 可注入 { fetchImpl, now, skipThrottle }，便于无 Key 单测
 */
async function resolveGeo(name, opts, deps) {
  opts = opts || {}; deps = deps || {};
  const q = normName(name);
  if (!q) return { found: false, reason: "empty-name", message: "机构名称为空" };
  if (!opts.key || /Please apply|replace this placeholder|^\s*$/i.test(opts.key)) {
    return { found: false, reason: "no-key", message: "服务端未配置高德 Web服务 Key，已回退离线定位" };
  }

  const now = deps.now || Date.now;
  const hit = cache.get(q);
  if (hit && now() - hit.t < CACHE_TTL) return Object.assign({}, hit.v, { cached: true });

  const fetchImpl = deps.fetchImpl || fetch;
  const timeout = opts.timeout || 4500;
  const skip = !!deps.skipThrottle;
  const region = opts.region || "福建";
  let geo = null, limited = false;

  const steps = [
    // 注意：place/text 必须带 city（业务覆盖的省级行政区），否则高德按全国返回，
    // 同名异地机构排在福建结果之前被 inScope 包围盒过滤，导致模糊名 no-poi（2026-11-08 修复）
    { path: "/v3/place/text", params: { keywords: q, offset: 10, page: 1, extensions: "base", city: region }, pick: r => pickPlaceText(r, q) },
    { path: "/v3/assistant/inputtips", params: { keywords: q, datatype: "poi", city: region }, pick: r => pickInputtips(r, q) },
    { path: "/v3/geocode/geo", params: { address: q, city: region }, pick: r => pickGeocode(r, q) }
  ];

  for (const st of steps) {
    const r = await request(st.path, st.params, opts.key, timeout, fetchImpl, skip);
    if (r && r.__badkey) {
      return { found: false, reason: "bad-key", message: "地图服务密钥无效或平台类型不匹配，已回退离线定位" };
    }
    if (r && r.__limited) { limited = true; continue; }
    if (r && r.__net) continue;
    try { geo = st.pick(r); } catch (e) { geo = null; }
    if (geo) break;
  }

  if (!geo) {
    return {
      found: false,
      reason: limited ? "quota-exceeded" : "no-poi",
      message: limited
        ? "地图服务触发限流或日配额上限，已回退离线定位"
        : "公开地图未匹配到该机构在业务覆盖范围内的真实坐标，已回退离线定位"
    };
  }

  const out = {
    found: true,
    query: q,
    geo,
    provider: "高德地图开放平台（Web服务 API）",
    coordSystem: "GCJ-02",
    verifiedAt: new Date().toISOString().slice(0, 10)
  };
  cache.set(q, { t: now(), v: out });
  return out;
}

// ===== 机构名称输入联想（/api/suggest，2026-11-08）=====
// 数据源实测结论：inputtips 的 city/citylimit 参数不生效（返回全国 POI，如「教育局」给出
// 天津和平区/河南洛阳/广东紫金），而 /v3/place/text 传 city=福建 能稳定返回省内真实机构名
// （福建省教育厅、福清市教育局、福州市鼓楼区教育局…）。故联想统一走 place/text。
// 仅返回「名称与输入词有字面关联」且在业务覆盖范围内的候选；每条建议只给名称/地址/区划，
// 前端选中后再走 /api/geo 取真实坐标；密钥仍仅服务端持有。
const suggestCache = new Map();
const SUGGEST_TTL = 24 * 60 * 60 * 1000;
const NON_ORG = /出入口|停车场|地铁站|公交站|加油站|收费站|ATM|公共厕所|厕所|便利店|超市|银行网点|宿舍|小区|新村|新城|大厦/;

function pickSuggestions(j, q) {
  if (!j || String(j.status) !== "1" || !Array.isArray(j.pois)) return [];
  const qc = clean(q), arr = [], seen = new Set();
  j.pois.forEach(x => {
    if (!x) return;
    const name = String(x.name || "").trim();
    if (!name || name.length < 2 || seen.has(name) || NON_ORG.test(name)) return;
    const nc = clean(name);
    // 字面相关性护栏：过滤高德按语义返回但名称不含输入词的 POI（如「研究院」混入「教育局」）
    if (!qc || nc.indexOf(qc) === -1) return;
    const loc = parseLocation(x.location);
    if (loc && !inScope(loc.lat, loc.lng)) return;
    const cat = String(x.type || "");
    seen.add(name);
    arr.push({
      name: name,
      address: String(x.address || ""),
      district: String(x.adname || x.cityname || ""),
      category: cat,
      lat: loc ? loc.lat : null,
      lng: loc ? loc.lng : null,
      // 政务/事业机构优先，生活服务类降权，保证下拉前几条就是目标单位
      _s: (GOOD.test(cat) ? 100 : 0) - (BAD.test(cat) ? 60 : 0) + (nc.indexOf(qc) === 0 ? 20 : 0)
    });
  });
  arr.sort((a, b) => b._s - a._s);
  return arr.slice(0, 8).map(x => {
    const y = Object.assign({}, x);
    delete y._s;
    return y;
  });
}

async function suggestNames(name, opts, deps) {
  opts = opts || {}; deps = deps || {};
  const q = normName(name);
  if (!q) return { found: false, reason: "empty-name", suggestions: [] };
  if (q.length < 2) return { found: false, reason: "too-short", suggestions: [] };
  if (!opts.key || /Please apply|replace this placeholder|^\s*$/i.test(opts.key)) {
    return { found: false, reason: "no-key", suggestions: [] };
  }
  const now = deps.now || Date.now;
  const hit = suggestCache.get(q);
  if (hit && now() - hit.t < SUGGEST_TTL) return Object.assign({}, hit.v, { cached: true });

  const fetchImpl = deps.fetchImpl || fetch;
  const region = opts.region || "福建";
  const r = await request("/v3/place/text",
    { keywords: q, offset: 10, page: 1, extensions: "base", city: region },
    opts.key, opts.timeout || 2500, fetchImpl, !!deps.skipThrottle);
  if (r && r.__badkey) return { found: false, reason: "bad-key", suggestions: [] };
  if (r && (r.__limited || r.__net || r.__http)) {
    return { found: false, reason: "upstream-unavailable", suggestions: [] };
  }
  let list = [];
  try { list = pickSuggestions(r, q); } catch (e) { list = []; }
  const out = {
    found: list.length > 0, query: q, suggestions: list,
    provider: "高德地图开放平台（Web服务 API · place/text）",
    verifiedAt: new Date().toISOString().slice(0, 10)
  };
  suggestCache.set(q, { t: now(), v: out });
  return out;
}

module.exports = {
  resolveGeo, suggestNames, pickSuggestions,
  pickPlaceText, pickInputtips, pickGeocode,
  inScope, parseLocation, sim,
  _resetCache: () => { cache.clear(); suggestCache.clear(); }
};
