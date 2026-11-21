/**
 * 腾讯位置服务 POI 定位通道（地图数据源白名单：腾讯地图 / GCJ-02）
 *
 * 合规要点：
 * - Key 仅从服务端环境变量读取，绝不写入前端产物、绝不回传响应、绝不写入日志；
 * - 页面只调同源 /api/geo，不直连任何地图域名、不携带任何凭据；
 * - 未配置 Key、超时、无 POI、坐标超出福建/温州包围盒时，一律如实返回 found:false
 *   并附 reason，由前端降级到行政区划中心近似，绝不伪造坐标。
 */
const CACHE_TTL = 24 * 60 * 60 * 1000;   // 24h 缓存，降低配额消耗
const cache = new Map();

// 福建全省 + 浙江温州的业务覆盖包围盒，过滤同名异地 POI
const BBOX = { minLat: 23.0, maxLat: 28.9, minLng: 115.4, maxLng: 121.3 };

function inScope(lat, lng) {
  return lat >= BBOX.minLat && lat <= BBOX.maxLat && lng >= BBOX.minLng && lng <= BBOX.maxLng;
}

function normName(name) {
  return String(name == null ? "" : name).trim().slice(0, 60);
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

/**
 * place/v1/suggestion：按机构名称取 POI 真实坐标。
 * 排序策略：先按类目分层（政府机关/教育机构加分，医疗、附属设施、交通等降权），
 * 再叠加标题与查询名的相似度（精确 > 短后缀前缀 > 包含）。
 * 实测修正：避免把「厦门大学附属第一医院」「福州大学附属省立医院」
 * 误当作学校本体，或把停车场、宿舍、校门当作机关所在地。
 */
function pickSuggestion(j, query) {
  if (!j || j.status !== 0 || !Array.isArray(j.data)) return null;
  const arr = j.data.filter(x => x && x.location &&
    Number.isFinite(Number(x.location.lat)) && Number.isFinite(Number(x.location.lng)) &&
    inScope(Number(x.location.lat), Number(x.location.lng)));
  if (!arr.length) return null;

  const clean = (s) => String(s == null ? "" : s).replace(/[\s()（）·\-]/g, "");
  const q = clean(query);
  const GOOD = /政府机关|机构团体|事业单位|行政|教育学校:大学|教育学校:学院|教育学校:中学|教育学校:小学/;
  const BAD = /医疗保健|停车场|门\/出入口|通行设施|住宅区|宿舍|招待所|地铁站|房产小区|酒店宾馆|室内及附属设施|基础设施|购物|餐饮/;
  const sim = (title) => {
    const t = clean(title);
    if (!q) return 0;
    if (t === q) return 100;
    if (t.indexOf(q) === 0) return 80 - Math.min(30, t.length - q.length);
    if (t.length >= 4 && q.indexOf(t) === 0) return 60;
    if (t.indexOf(q) > 0) return 45 - Math.min(25, t.length - q.length);
    return 0;
  };
  const scored = arr.map(x => {
    const cat = String(x.category || "");
    let c = GOOD.test(cat) ? 40 : 0;
    if (BAD.test(cat)) c -= 60;
    return { x: x, s: sim(x.title) + c };
  }).sort((a, b) => b.s - a.s);

  const p = scored[0].x;
  const lat = Number(p.location.lat), lng = Number(p.location.lng);
  const ad = p.ad_info || {};
  return {
    lat, lng,
    title: p.title || "",
    address: p.address || "",
    province: ad.province || "",
    city: ad.city || "",
    district: ad.district || p.district || "",
    category: p.category || "",
    source: "tencent-place-suggestion"
  };
}

/** geocoder/v1：按地址兜底取坐标 */
function pickGeocoder(j) {
  if (!j || j.status !== 0 || !j.result || !j.result.location) return null;
  const l = j.result.location;
  const lat = Number(l.lat), lng = Number(l.lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || !inScope(lat, lng)) return null;
  const ad = j.result.address_components || {};
  return {
    lat, lng,
    title: "",
    address: j.result.address || "",
    province: ad.province || "",
    city: ad.city || "",
    district: ad.district || "",
    category: "",
    source: "tencent-geocoder"
  };
}

/**
 * @param {string} name 机构名称
 * @param {object} opts { key, region, timeout }
 * @param {object} deps 可注入 { fetchImpl, now }，便于无 Key 单测
 */
async function resolveGeo(name, opts, deps) {
  opts = opts || {}; deps = deps || {};
  const q = normName(name);
  if (!q) return { found: false, reason: "empty-name", message: "机构名称为空" };
  if (!opts.key || /Please apply|replace this placeholder|^\s*$/i.test(opts.key)) {
    return { found: false, reason: "no-key", message: "服务端未配置腾讯位置服务 Key，已回退离线定位" };
  }

  const now = deps.now || Date.now;
  const hit = cache.get(q);
  if (hit && now() - hit.t < CACHE_TTL) return Object.assign({}, hit.v, { cached: true });

  const fetchImpl = deps.fetchImpl || fetch;
  const timeout = opts.timeout || 4500;
  const region = opts.region || "福建";
  let geo = null;

  try {
    const url = "https://apis.map.qq.com/ws/place/v1/suggestion?keyword=" +
      encodeURIComponent(q) + "&region=" + encodeURIComponent(region) +
      "&region_fix=0&page_size=5&key=" + encodeURIComponent(opts.key);
    geo = pickSuggestion(await fetchJSON(url, timeout, fetchImpl), q);
  } catch (e) { /* 超时或网络失败：继续兜底，错误不外泄 */ }

  if (!geo) {
    try {
      const url2 = "https://apis.map.qq.com/ws/geocoder/v1/?address=" +
        encodeURIComponent(q) + "&key=" + encodeURIComponent(opts.key);
      geo = pickGeocoder(await fetchJSON(url2, timeout, fetchImpl));
    } catch (e) { /* 同上 */ }
  }

  if (!geo) {
    return {
      found: false, reason: "no-poi",
      message: "公开地图未匹配到该机构在业务覆盖范围内的真实坐标，已回退离线定位"
    };
  }

  const out = {
    found: true,
    query: q,
    geo,
    provider: "腾讯位置服务（WebServiceAPI）",
    coordSystem: "GCJ-02",
    verifiedAt: new Date().toISOString().slice(0, 10)
  };
  cache.set(q, { t: now(), v: out });
  return out;
}

module.exports = {
  resolveGeo, pickSuggestion, pickGeocoder, inScope,
  _resetCache: () => cache.clear()
};
