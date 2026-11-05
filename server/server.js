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
const { lookup } = require("./providers/lookup");
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

const server = http.createServer(async (req, res) => {
  // CORS 预检
  if (req.method === "OPTIONS") { sendJSON(res, 204, {}); return; }

  const url = new URL(req.url, "http://localhost");
  const pathname = url.pathname;

  if (pathname === "/api/health") {
    return sendJSON(res, 200, { ok: true, provider: PROVIDER, mock: PROVIDER === "mock" });
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

  // 静态资源（可选：若与 H5 同目录部署，可直接托管前端）
  if (req.method === "GET") {
    const safePath = path.normalize(pathname).replace(/^(\.\.[\/\\])+/, "");
    const filePath = path.join(__dirname, "..", safePath);
    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
      const ext = path.extname(filePath);
      const mime = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json" }[ext] || "application/octet-stream";
      res.writeHead(200, { "Content-Type": mime + "; charset=utf-8", "Access-Control-Allow-Origin": "*" });
      return fs.createReadStream(filePath).pipe(res);
    }
  }

  sendJSON(res, 404, { error: "not found" });
});

server.listen(PORT, () => {
  console.log("✅ 福建海峡银行网点查询后端已启动");
  console.log("   监听端口:", PORT);
  console.log("   数据提供方 DATA_PROVIDER =", PROVIDER, PROVIDER === "mock" ? "（无密钥示例模式，接入密钥后切换 qcc/tyc）" : "");
  console.log("   接口: GET /api/org?name=机构名&type=government");
});
