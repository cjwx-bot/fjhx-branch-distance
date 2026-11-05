/**
 * 核心计算模块：距离、行政区划中心坐标、机构类型研判、最近网点匹配
 * 数据来源：regions.json / province_of_city.json / branches.json（由 H5 校验数据抽取）
 */
const regions = require("../data/regions.json");
const provinceOfCity = require("../data/province_of_city.json");
const branchData = require("../data/branches.json");
const BRANCHES = branchData.branches || [];

function haversineM(lat1, lng1, lat2, lng2) {
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function formatDistance(meters) {
  if (meters == null) return "—";
  if (meters < 1000) return Math.round(meters) + " 米";
  if (meters < 100000) return (meters / 1000).toFixed(1) + " 公里";
  return Math.round(meters / 1000) + " 公里";
}

/**
 * 根据 省/市/区 反查行政区划中心坐标。
 * 优先级：区(县)直接命中 > 该市区县中心均值 > 该省任一首府城市均值。
 * 用于在无精确地图密钥时给出可用测算基准。
 */
function districtCenter(province, city, district) {
  // 先按 city -> district 精确命中
  if (city && regions[city] && district && regions[city][district]) {
    const c = regions[city][district];
    return { lat: c[0], lng: c[1], matched: "district" };
  }
  // 跨城市：在全部数据中查找同名区县
  for (const c of Object.keys(regions)) {
    if (regions[c][district]) {
      const cc = regions[c][district];
      return { lat: cc[0], lng: cc[1], matched: "district-cross" };
    }
  }
  // 仅命中城市：取该市区县中心均值
  if (city && regions[city]) {
    const ds = regions[city];
    const ks = Object.keys(ds);
    if (ks.length) {
      let la = 0, lo = 0;
      ks.forEach(k => { la += ds[k][0]; lo += ds[k][1]; });
      return { lat: la / ks.length, lng: lo / ks.length, matched: "city-avg" };
    }
  }
  // 仅命中省份：取该省首府（第一个城市）均值
  if (province) {
    const cities = Object.keys(provinceOfCity).filter(c => provinceOfCity[c] === province);
    if (cities.length) {
      const ds = regions[cities[0]];
      const ks = Object.keys(ds);
      if (ks.length) {
        let la = 0, lo = 0;
        ks.forEach(k => { la += ds[k][0]; lo += ds[k][1]; });
        return { lat: la / ks.length, lng: lo / ks.length, matched: "province-avg" };
      }
    }
  }
  return null;
}

/**
 * 将提供方返回的机构类型文本研判为三大类之一。
 * 返回 {key:'government'|'public'|'group', label} 或 null（需由前端/参数兜底）。
 */
function classifyType(raw) {
  const t = String(raw || "");
  if (/(党委|政府|机关|厅|局|委员会|工委|部|署|人大|法院|检察院|办事处|监察|政法)/.test(t)) {
    return { key: "government", label: "党政机关" };
  }
  if (/(事业|学校|学院|大学|医院|研究院|研究|所|中心|馆|台|社|院|幼儿园|中学|小学|学院)/.test(t)) {
    return { key: "public", label: "事业单位" };
  }
  if (/(团体|协会|工会|共青团|妇联|工商联|文联|科协|侨联|残联|红十字|联合会|商会|学会|基金会)/.test(t)) {
    return { key: "group", label: "群团组织" };
  }
  return null;
}

/** 计算距离某坐标最近的 n 家网点 */
function computeNearest(lat, lng, n = 8) {
  if (lat == null || lng == null) return [];
  return BRANCHES
    .filter(b => b.lat && b.lng)
    .map(b => ({ branch: b, dist: haversineM(lat, lng, b.lat, b.lng) }))
    .sort((a, b) => a.dist - b.dist)
    .slice(0, n)
    .map(x => ({
      name: x.branch.name,
      type: x.branch.type || "二级支行",
      address: x.branch.address || "地址未收录",
      phone: x.branch.phone || "—",
      distM: Math.round(x.dist),
      distText: formatDistance(x.dist)
    }));
}

/** 可选：用腾讯地图 WebService 对注册地址做精确地理编码（需 MAP_KEY） */
async function geocodeByMap(address, mapKey) {
  if (!mapKey || !address) return null;
  try {
    const url = "https://apis.map.qq.com/ws/geocoder/v1/?address=" +
      encodeURIComponent(address) + "&key=" + mapKey;
    const r = await fetch(url);
    const j = await r.json();
    if (j && j.status === 0 && j.result && j.result.location) {
      return { lat: j.result.location.lat, lng: j.result.location.lng };
    }
  } catch (e) { /* 失败时回退到行政区划中心 */ }
  return null;
}

module.exports = {
  haversineM, formatDistance, districtCenter, classifyType, computeNearest, geocodeByMap,
  BRANCHES, regions, provinceOfCity
};
