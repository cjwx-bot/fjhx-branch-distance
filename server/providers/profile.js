/**
 * 单位画像调取通道（启信慧眼）
 *
 * provider = local（默认，立即可用）
 *   WorkBuddy 会话侧调用启信慧眼已授权接口核验后结构化落盘的公开级画像库
 *   intel/org_profile.json。页面点击「编制并查看参阅材料」时经同源 /api/profile 调取。
 *
 * provider = qixin-mcp（预留，需有效密钥）
 *   直连 https://mcp.qixin.com/mcp，Bearer 鉴权。用户提供的 ent_ 形态凭据经官方端点
 *   实测返回 401「OAuth access token 无效」，故默认不启用；须换用启信慧眼 AI 开放平台
 *   「显示密钥」给出的 mcp- 格式密钥，通过设置 QIXIN_MCP_KEY 启用。
 *
 * 安全：任何凭据仅从服务端环境变量读取，绝不回传响应体、不写入日志、不进入前端产物。
 * 分级：输出仅含机构层面字段，不含自然人姓名、对外投资明细、风险/涉诉类标签。
 */
"use strict";

const fs = require("fs");
const path = require("path");
const https = require("https");

const DATA_PATH = path.join(__dirname, "..", "..", "intel", "org_profile.json");
const MCP_ENDPOINT = "https://mcp.qixin.com/mcp";
const CACHE_TTL = 24 * 60 * 60 * 1000;

let _cache = null;
const _mcpCache = new Map();

function loadData() {
  if (_cache && Date.now() - _cache.at < CACHE_TTL) return _cache.data;
  const raw = fs.readFileSync(DATA_PATH, "utf8");
  const data = JSON.parse(raw);
  if (!data || data.schema !== "fjhx-org-profile/v1" || !Array.isArray(data.orgs)) {
    throw new Error("画像库格式不正确");
  }
  _cache = { at: Date.now(), data };
  return data;
}

function norm(s) {
  return String(s == null ? "" : s)
    .replace(/[\s\u3000（）()·、，,。.;；:：\-—_"'"']/g, "")
    .toLowerCase();
}

/** 名称/别名/信用代码精确优先，再做保守的唯一包含匹配 */
function lookupOrg(data, name) {
  const q = norm(name);
  if (!q) return null;
  for (const o of data.orgs) {
    if (norm(o.name) === q || norm(o.fields && o.fields.creditCode && o.fields.creditCode.v) === q) return o;
    if ((o.aliases || []).some(a => norm(a) === q)) return o;
  }
  if (q.length < 4) return null;
  const hits = data.orgs.filter(o => {
    const n = norm(o.name);
    return n.indexOf(q) >= 0 || q.indexOf(n) >= 0 ||
      (o.aliases || []).some(a => norm(a).indexOf(q) >= 0 || q.indexOf(norm(a)) >= 0);
  });
  return hits.length === 1 ? hits[0] : null;
}

/** 服务端二次分级：只输出白名单字段，杜绝内部级信息外泄 */
function publicProfile(data, o) {
  const labels = data.fieldLabels || {};
  const fields = {};
  Object.keys(labels).forEach(k => {
    const f = (o.fields || {})[k];
    fields[k] = f && f.s === "verified" && f.v
      ? { v: String(f.v), s: "verified", src: f.src || [] }
      : { v: "", s: "unverified", note: (f && f.note) || "启信慧眼未载明或未公示" };
  });
  const refs = data.sourceRefs || {};
  const sources = (o.sources || []).map(k => ({
    id: k,
    api_ref: (refs[k] || {}).api_ref || k,
    label: (refs[k] || {}).label || k
  }));
  return {
    id: o.id,
    name: o.name,
    fields,
    fieldLabels: labels,
    tags: o.tags || [],
    geo: (o.geo && Number.isFinite(o.geo.lat) && Number.isFinite(o.geo.lng))
      ? { lat: o.geo.lat, lng: o.geo.lng, s: o.geo.s || "verified" } : null,
    sources,
    policy: {
      visibility: (data.policy || {}).visibility || "public",
      scope: "按最小必要与行内参考口径，仅呈现机构属性类公开登记信息；自然人姓名、个人联系方式、对外投资明细与风险涉诉类信息不纳入公开页"
    }
  };
}

function localResolve(name) {
  const data = loadData();
  const o = lookupOrg(data, name);
  if (!o) {
    return {
      found: false,
      reason: "not-in-profile-library",
      message: "该单位未收录于启信慧眼核验画像库；如需补齐，请在 WorkBuddy 会话中发起「画像补齐 <机构名>」"
    };
  }
  return {
    found: true,
    query: String(name),
    profile: publicProfile(data, o),
    provider: "启信慧眼（会话侧核验画像库）",
    source: "启信慧眼",
    verifiedAt: data.generatedAt,
    coordSystem: "GCJ-02"
  };
}

/** 预留：直连启信慧眼 MCP（需 mcp- 格式有效密钥），失败时如实降级，不伪造画像 */
function mcpRequest(payload, session, token, timeout) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(payload);
    const u = new URL(MCP_ENDPOINT);
    const req = https.request({
      hostname: u.hostname, path: u.pathname, method: "POST", timeout,
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer " + token,
        ...(session ? { "Mcp-Session-Id": session } : {})
      }
    }, res => {
      let raw = "";
      res.setEncoding("utf8");
      res.on("data", c => { raw += c; });
      res.on("end", () => resolve({
        status: res.statusCode,
        session: res.headers["mcp-session-id"] || null,
        body: parseBody(raw)
      }));
    });
    req.on("timeout", () => req.destroy(new Error("timeout")));
    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

function parseBody(raw) {
  const s = String(raw || "").trim();
  if (!s) return null;
  if (s.charAt(0) === "{") { try { return JSON.parse(s); } catch (e) { /* fallthrough */ } }
  for (const line of s.split(/\r?\n/)) {
    if (line.indexOf("data:") === 0) {
      const v = line.slice(5).trim();
      if (v && v !== "[DONE]") { try { return JSON.parse(v); } catch (e) { /* next */ } }
    }
  }
  return null;
}

async function mcpResolve(name, opts) {
  const token = String(opts.key || "").trim();
  if (!token) return { found: false, reason: "provider-unavailable", message: "未配置有效的启信慧眼 MCP 密钥" };
  const hit = _mcpCache.get(norm(name));
  if (hit && Date.now() - hit.at < CACHE_TTL) return hit.value;
  try {
    const init = await mcpRequest({
      jsonrpc: "2.0", id: 1, method: "initialize",
      params: { protocolVersion: "2024-11-05", capabilities: {},
        clientInfo: { name: "fjhx-brief", version: "1.0" } }
    }, null, token, opts.timeout || 6000);
    if (init.status !== 200 || !init.session) {
      const msg = (init.body && init.body.error && init.body.error.message) || "";
      return { found: false, reason: "provider-auth-failed", message: "启信慧眼 MCP 鉴权未通过：" + String(msg).slice(0, 120) };
    }
    // 会话已建立；实际工具名与字段映射须以有效密钥下 tools/list 结果为准，当前凭据无效故不臆造调用。
    return { found: false, reason: "provider-not-configured",
      message: "MCP 会话已建立，但实时工具映射尚未在有效凭据下验证；请先配置官方 mcp- 格式密钥" };
  } catch (e) {
    return { found: false, reason: "provider-error", message: "启信慧眼 MCP 请求失败：" + String(e && e.message || e).slice(0, 120) };
  }
}

/**
 * 统一入口
 * @param {string} name 机构名称
 * @param {object} opts { provider, key, timeout }
 */
async function resolveProfile(name, opts) {
  const o = opts || {};
  const provider = String(o.provider || "local").toLowerCase();
  if (provider === "qixin-mcp" || provider === "mcp") {
    return mcpResolve(name, { key: o.key, timeout: o.timeout });
  }
  return localResolve(name);
}

function stats() {
  try {
    const d = loadData();
    return { enabled: true, orgs: d.orgs.length, generatedAt: d.generatedAt, source: d.source };
  } catch (e) {
    return { enabled: false, orgs: 0, error: String(e && e.message || e) };
  }
}

module.exports = { resolveProfile, stats, loadData, lookupOrg, norm };
