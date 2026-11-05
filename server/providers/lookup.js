/**
 * 数据提供方：根据机构名称返回结构化机构信息。
 * 支持三种模式（由 DATA_PROVIDER 决定）：
 *   - mock：无密钥，返回基于名称识别区县的示例数据（用于本地全链路联调）
 *   - qcc ：调用企查查 Open API（需 QCC_APP_KEY / QCC_APP_SECRET）
 *   - tyc  ：调用天眼查 Open API（需 TYC_TOKEN）
 *
 * ⚠️ qcc/tyc 的具体接口路径与返回字段因你订阅的产品版本而异。
 *    下方 normalizeXxx 负责字段映射，若与你实际返回结构不一致，改这里即可。
 */
const core = require("../core");

/** 无密钥模式：基于名称识别区县，返回示例机构信息（坐标用行政区划中心） */
function lookupMock(name) {
  // 收集全部区县，长名优先匹配
  const districts = [];
  Object.keys(core.regions).forEach(c => {
    core.provinceOfCity; // noop
    Object.keys(core.regions[c]).forEach(d => districts.push({ c, d }));
  });
  districts.sort((a, b) => b.d.length - a.d.length);
  let city = "福州市", district = "鼓楼区", province = "福建省";
  for (const x of districts) {
    if (name.indexOf(x.d) !== -1) { city = x.c; district = x.d; province = core.provinceOfCity[city] || "福建省"; break; }
  }
  const center = core.districtCenter(province, city, district);
  const typeInfo = core.classifyType(name) || { key: "government", label: "党政机关" };
  return {
    fullName: name,
    creditCode: "—（示例数据，未接入密钥）",
    typeKey: typeInfo.key, typeLabel: typeInfo.label,
    address: province + city + district + "（示例地址；接入密钥后返回真实注册地址）",
    province, city, district,
    lat: center ? center.lat : null, lng: center ? center.lng : null,
    coordSource: "district-center",
    mock: true
  };
}

/** 企查查 Open API */
async function lookupQcc(name, opts) {
  const { appKey, appSecret, mapKey, baseUrl } = opts;
  if (!appKey || !appSecret) throw new Error("缺少 qcc appKey/appSecret");
  const base = baseUrl || "https://api.qcc.com";
  // 1) 获取访问令牌
  const tokRes = await fetch(base + "/api/Authorize/GetToken", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ appkey: appKey, secret: appSecret })
  });
  const tokJson = await tokRes.json();
  const token = tokJson && (tokJson.access_token || (tokJson.Result && tokJson.Result.access_token) || tokJson.result || tokJson.token);
  if (!token) throw new Error("qcc 获取 token 失败：" + JSON.stringify(tokJson));
  // 2) 基础工商/登记信息
  const detRes = await fetch(base + "/api/intelProperty/getBasicDetail?keyword=" + encodeURIComponent(name) + "&access_token=" + token);
  const detJson = await detRes.json();
  const r = detJson && (detJson.Result || detJson.result || detJson);
  if (!r || !r.Name) return null;
  // —— 字段映射（以你实际订阅的 qcc API 文档为准）——
  const fullName = r.Name || r.EntName;
  const creditCode = r.CreditCode || r.UnifiedSocialCreditCode || r.USCC || (r.BaseInfo && r.BaseInfo.CreditCode);
  const address = r.RegistAddress || r.Address || (r.BaseInfo && r.BaseInfo.RegistAddress) || "";
  const province = r.Province || (r.BaseInfo && r.BaseInfo.Province) || "";
  const city = r.City || (r.BaseInfo && r.BaseInfo.City) || "";
  const district = r.District || (r.BaseInfo && r.BaseInfo.District) || "";
  const rawType = r.EnterpriseType || r.EconKind || r.EntType || (r.BaseInfo && r.BaseInfo.EnterpriseType) || "";
  const typeInfo = core.classifyType(rawType);
  let lat = null, lng = null, coordSource = "district-center";
  const geo = await core.geocodeByMap(address, mapKey);
  if (geo) { lat = geo.lat; lng = geo.lng; coordSource = "geocoded"; }
  if (lat == null) { const c = core.districtCenter(province, city, district); if (c) { lat = c.lat; lng = c.lng; } }
  return {
    fullName, creditCode, typeKey: typeInfo ? typeInfo.key : null, typeLabel: typeInfo ? typeInfo.label : null,
    address, province: province || "", city: city || "", district: district || "",
    lat, lng, coordSource, rawType
  };
}

/** 天眼查 Open API */
async function lookupTyc(name, opts) {
  const { token, mapKey, baseUrl } = opts;
  if (!token) throw new Error("缺少 tyc token");
  const base = baseUrl || "https://open.api.tianyancha.com/services/open/2.0";
  const res = await fetch(base + "/baseinfo?keyword=" + encodeURIComponent(name), {
    headers: { Authorization: "token " + token }
  });
  const j = await res.json();
  const r = j && (j.result || j.Result || j);
  if (!r || !r.name) return null;
  // —— 字段映射（以你实际订阅的天眼查 API 文档为准）——
  const fullName = r.name || r.companyName;
  const creditCode = r.creditCode || (r.baseInfo && r.baseInfo.creditCode);
  const address = r.regAddress || r.registAddress || r.address || (r.baseInfo && (r.baseInfo.regAddress || r.baseInfo.address)) || "";
  const province = r.province || (r.baseInfo && r.baseInfo.province) || "";
  const city = r.city || (r.baseInfo && r.baseInfo.city) || "";
  const district = r.district || (r.baseInfo && r.baseInfo.district) || "";
  const rawType = r.companyType || r.type || (r.baseInfo && (r.baseInfo.companyType || r.baseInfo.type)) || "";
  const typeInfo = core.classifyType(rawType);
  let lat = null, lng = null, coordSource = "district-center";
  const geo = await core.geocodeByMap(address, mapKey);
  if (geo) { lat = geo.lat; lng = geo.lng; coordSource = "geocoded"; }
  if (lat == null) { const c = core.districtCenter(province, city, district); if (c) { lat = c.lat; lng = c.lng; } }
  return {
    fullName, creditCode, typeKey: typeInfo ? typeInfo.key : null, typeLabel: typeInfo ? typeInfo.label : null,
    address, province: province || "", city: city || "", district: district || "",
    lat, lng, coordSource, rawType
  };
}

async function lookup(provider, name, opts) {
  if (provider === "qcc") return lookupQcc(name, opts);
  if (provider === "tyc") return lookupTyc(name, opts);
  return lookupMock(name);
}

module.exports = { lookup, lookupMock, lookupQcc, lookupTyc };
