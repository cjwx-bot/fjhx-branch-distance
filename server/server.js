/**
 * 福建海峡银行最近网点查询 —— 实时后端代理
 * 接收 H5 的模糊机构名，调用 qcc/tyc（或 mock）获取全称/统一社会信用代码/注册地址/所属地区，
 * 结合内置 91 家网点库计算最近网点，返回 JSON 给前端。
 *
 * 启动：node server.js   （或 npm start）
 * 环境变量：见 .env.example（密钥不入库，仅本地 .env 提供）
 */
const fs = require("fs");
const path = require("path");
const http = require("http");
const https = require("https");
const { lookup } = require("./providers/lookup");
const { resolveGeo, suggestNames, providerLabel } = require("./providers/geo");
const { resolveProfile, stats: profileStats } = require("./providers/profile");
const core = require("./core");

// —— 轻量 .env 加载（避免额外依赖）——
function loadEnv() {
  const envPath = path.join(__dirname, ".env");
  if (!fs.existsSync(envPath)) return;
  const txt = fs.readFileSync(envPath, "utf8");
  txt.split(/\r?\n/).forEach(line => {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
    if (m && !(m[1] in process.env)) process.env[m[1]] = m[2];
  });
}
loadEnv();

const PORT = process.env.PORT || 3000;
const PROVIDER = (process.env.DATA_PROVIDER || "mock").toLowerCase();
const TYPE_LABEL = { government: "党政机关", public: "事业单位", group: "群团组织" };

// 简单缓存，降低 API 按次计费与限频压力
const cache = new Map();
const CACHE_TTL = 24 * 60 * 60 * 1000;

function getOpts() {
  return {
    appKey: process.env.QCC_APP_KEY,
    appSecret: process.env.QCC_APP_SECRET,
    token: process.env.TYC_TOKEN,
    mapKey: process.env.MAP_KEY,
    baseUrl: process.env.QCC_BASE_URL || process.env.TYC_BASE_URL
  };
}

function sendJSON(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
  });
  res.end(body);
}

// —— 街道底图瓦片同源代理（2026-11-12）——
// 页面只请求同源 /api/tiles，不直连任何地图域名、不携带任何 Key；
// 上游固定为高德公开瓦片（技能白名单内地图数据源），严格校验 z/x/y 防 SSRF。
// 上游不可用时返回 502，前端自动退回零依赖的点位分布图并如实标注，不以空白冒充底图。
const TILE_HOSTS = [
  "webrd01.is.autonavi.com", "webrd02.is.autonavi.com",
  "webrd03.is.autonavi.com", "webrd04.is.autonavi.com"
];
const TILE_TIMEOUT = Number(process.env.TILE_TIMEOUT_MS || 8000);

function tileError(res) {
  if (res.headersSent) { try { res.end(); } catch (e) {} return; }
  res.writeHead(502, {
    "Content-Type": "text/plain; charset=utf-8",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*"
  });
  res.end("tile upstream unavailable");
}

function proxyTile(res, z, x, y) {
  const host = TILE_HOSTS[(x + y) % TILE_HOSTS.length];
  const qs = "lang=zh_cn&size=1&scale=1&style=8&x=" + x + "&y=" + y + "&z=" + z;
  const up = https.get({
    host: host,
    path: "/appmaptile?" + qs,
    timeout: TILE_TIMEOUT,
    headers: {
      "User-Agent": "Mozilla/5.0 (compatible; fjhx-branch-distance/1.0)",
      "Accept": "image/png,image/*;q=0.9"
    }
  }, r => {
    const ct = String(r.headers["content-type"] || "");
    if (r.statusCode !== 200 || !/^image\/(png|jpe?g|webp)$/i.test(ct)) {
      r.resume();
      return tileError(res);
    }
    res.writeHead(200, {
      "Content-Type": ct,
      "Cache-Control": "public, max-age=86400",
      "Access-Control-Allow-Origin": "*",
      "X-Content-Type-Options": "nosniff"
    });
    r.pipe(res);
  });
  up.on("timeout", () => up.destroy(new Error("tile timeout")));
  up.on("error", () => tileError(res));
}

const server = http.createServer(async (req, res) => {
  // CORS 预检
  if (req.method === "OPTIONS") { sendJSON(res, 204, {}); return; }

  const url = new URL(req.url, "http://localhost");
  const pathname = url.pathname;

  // 能力探测：只回报是否已配置 Key，不回传 Key 本身
  if (pathname === "/api/health") {
    return sendJSON(res, 200, {
      ok: true,
      provider: PROVIDER,
      mock: PROVIDER === "mock",
      geoEnabled: !!process.env.MAP_KEY && !/Please apply|replace this placeholder/i.test(process.env.MAP_KEY),
      geoProvider: providerLabel(),
      profile: profileStats()
    });
  }

  // 街道底图瓦片：同源代理，前端零 Key、不直连地图域名
  if (pathname === "/api/tiles") {
    const zs = url.searchParams.get("z") || "";
    const xs = url.searchParams.get("x") || "";
    const ys = url.searchParams.get("y") || "";
    if (!/^\d{1,2}$/.test(zs) || !/^\d{1,7}$/.test(xs) || !/^\d{1,7}$/.test(ys)) {
      return sendJSON(res, 400, { error: "invalid tile params" });
    }
    const z = Number(zs), x = Number(xs), y = Number(ys), lim = Math.pow(2, z);
    if (z < 3 || z > 18 || x >= lim || y >= lim) {
      return sendJSON(res, 400, { error: "tile out of range" });
    }
    return proxyTile(res, z, x, y);
  }

  // 单位画像：编制参阅材料时按机构名称调取启信慧眼核验画像（凭据仅服务端持有）
  if (pathname === "/api/profile") {
    const name = (url.searchParams.get("name") || "").trim();
    if (!name) return sendJSON(res, 400, { found: false, reason: "empty-name", message: "缺少 name 参数" });
    try {
      const out = await resolveProfile(name, {
        provider: process.env.PROFILE_PROVIDER || "local",
        key: process.env.QIXIN_MCP_KEY,
        timeout: Number(process.env.PROFILE_TIMEOUT_MS || 6000)
      });
      return sendJSON(res, 200, out);
    } catch (e) {
      return sendJSON(res, 200, { found: false, reason: "profile-error", message: "画像资料库暂不可用，材料按未收录口径出具" });
    }
  }

  // 机构名称输入联想：录入时实时给出相近的真实机构名供选择（Key 仅服务端持有）
  if (pathname === "/api/suggest") {
    const name = (url.searchParams.get("name") || "").trim();
    if (!name) return sendJSON(res, 200, { found: false, reason: "empty-name", suggestions: [] });
    try {
      const out = await suggestNames(name, {
        key: process.env.MAP_KEY,
        provider: process.env.GEO_PROVIDER || "amap",
        region: process.env.GEO_REGION || "福建",
        timeout: Number(process.env.SUGGEST_TIMEOUT_MS || 2500)
      });
      return sendJSON(res, 200, out);
    } catch (e) {
      return sendJSON(res, 200, { found: false, reason: "upstream-unavailable", suggestions: [] });
    }
  }

  // 实时真实定位：按机构名称取高德 POI 坐标（Key 仅服务端持有）
  if (pathname === "/api/geo") {
    const name = (url.searchParams.get("name") || "").trim();
    if (!name) return sendJSON(res, 400, { found: false, reason: "empty-name", message: "缺少 name 参数" });
    try {
      const out = await resolveGeo(name, {
        key: process.env.MAP_KEY,
        provider: process.env.GEO_PROVIDER || "amap",
        region: process.env.GEO_REGION || "福建",
        timeout: Number(process.env.GEO_TIMEOUT_MS || 4500)
      });
      return sendJSON(res, 200, out);
    } catch (e) {
      // 不回传底层错误细节，避免泄露服务端配置
      return sendJSON(res, 200, { found: false, reason: "geo-error", message: "实时定位暂不可用，已回退离线定位" });
    }
  }

  if (pathname === "/api/org") {
    const name = (url.searchParams.get("name") || "").trim();
    const selType = (url.searchParams.get("type") || "government").toLowerCase();
    if (!name) return sendJSON(res, 400, { found: false, error: "缺少 name 参数" });

    // 命中缓存直接返回
    const cacheKey = PROVIDER + "::" + name + "::" + selType;
    const hit = cache.get(cacheKey);
    if (hit && (Date.now() - hit.t < CACHE_TTL)) {
      return sendJSON(res, 200, { ...hit.v, cached: true });
    }

    try {
      const org = await lookup(PROVIDER, name, getOpts());
      if (!org) {
        const out = { found: false, query: name, message: "未在企业库匹配到该机构（可能名称需更完整，或该机构未收录）" };
        cache.set(cacheKey, { t: Date.now(), v: out });
        return sendJSON(res, 200, out);
      }
      // 类型兜底：提供方未研判时，用前端所选类型
      let typeKey = org.typeKey, typeLabel = org.typeLabel;
      if (!typeKey) { typeKey = TYPE_LABEL[selType] ? selType : "government"; typeLabel = TYPE_LABEL[typeKey]; }

      // 坐标兜底
      let lat = org.lat, lng = org.lng, coordSource = org.coordSource;
      if (lat == null || lng == null) {
        const c = core.districtCenter(org.province, org.city, org.district);
        if (c) { lat = c.lat; lng = c.lng; coordSource = "district-center-fallback"; }
      }

      const nearest = core.computeNearest(lat, lng, 8);
      const out = {
        found: true,
        query: name,
        org: {
          fullName: org.fullName,
          creditCode: org.creditCode || "—",
          typeKey, typeLabel,
          address: org.address || "—",
          province: org.province || "福建省",
          city: org.city || "",
          district: org.district || "",
          lat, lng, coordSource
        },
        nearest,
        branchCount: core.BRANCHES.length
      };
      cache.set(cacheKey, { t: Date.now(), v: out });
      return sendJSON(res, 200, out);
    } catch (e) {
      return sendJSON(res, 502, { found: false, query: name, error: "数据提供方调用失败：" + e.message });
    }
  }

  // 未匹配的 API 路径统一按接口语义返回 404，不落入静态资源分支
  if (pathname.indexOf("/api/") === 0) {
    return sendJSON(res, 404, { error: "not found" });
  }

  // 静态资源（与 H5 同目录部署；根路径映射到 index.html）
  if (req.method === "GET") {
    let rel;
    try { rel = decodeURIComponent(pathname); } catch (e) { rel = pathname; }
    rel = path.normalize(rel).replace(/^[\\\/]+/, "");
    if (rel.indexOf("..") !== -1) return sendJSON(res, 403, { error: "forbidden" });
    if (!rel || rel === ".") rel = "index.html";
    else if (/[\\\/]$/.test(rel)) rel = rel + "index.html";

    // —— 静态资源安全边界（上线前强制）——
    // 后端 .env 与服务端源码不得经 HTTP 读取；仅放行页面运行所需的静态资源类型。
    // 单文件 H5 已内联全部 CSS/JS/数据，根目录其余源码不属于浏览器运行依赖。
    const norm = rel.replace(/\\/g, "/").toLowerCase();
    const denyDir = /(^|\/)(server|intel|chrome_profile|\.git|\.github|node_modules)(\/|$)/.test(norm);
    const denyEnv = /(^|\/)\.env(\.|$)/.test(norm);
    const denySrc = /(^|\/)(build_index\.py|brief_doc\.js|org_struct\.js|intel_brief\.js|intel_pipeline\.py|verify_index\.js|verify_browser_cdp\.py|package\.json|package-lock\.json)$/.test(norm);
    // 「网点半径内机构」地市分片：纯静态公开登记信息，仅放行 nearby_data/cN.js，不放行源码或凭据文件。
    const allowNearby = /^nearby_data\/c\d+\.js$/.test(norm);
    const safeExt = allowNearby || /\.(html?|css|png|jpe?g|gif|svg|ico|webp|txt|pdf|woff2?)$/.test(norm);
    if (denyDir || denyEnv || denySrc || !safeExt) {
      return sendJSON(res, 403, { error: "forbidden" });
    }

    const filePath = path.join(__dirname, "..", rel);
    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
      const ext = path.extname(filePath);
      const mime = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json" }[ext] || "application/octet-stream";
      res.writeHead(200, { "Content-Type": mime + "; charset=utf-8", "Access-Control-Allow-Origin": "*" });
      return fs.createReadStream(filePath).pipe(res);
    }
  }

  sendJSON(res, 404, { error: "not found" });
});

server.listen(PORT, "0.0.0.0", () => {
  console.log("✅ 福建海峡银行网点查询服务已启动（单端口：静态页 + 定位 API）");
  console.log("   监听端口:", PORT);
  console.log("   实时定位 MAP_KEY =", process.env.MAP_KEY ? "已配置" : "未配置（/api/geo 将如实回退）");
  console.log("   数据提供方 DATA_PROVIDER =", PROVIDER, PROVIDER === "mock" ? "（无密钥示例模式，接入密钥后切换 qcc/tyc）" : "");
  console.log("   接口: GET /api/health · GET /api/geo · GET /api/suggest · GET /api/profile · GET /api/tiles · GET /api/org");
  console.log("   街道底图: /api/tiles 同源代理（高德公开瓦片，无 Key，z 3—18，上游固定白名单域名）");
});
