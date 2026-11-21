/**
 * 最近网点查询 —— WorkBuddy 站点单端口入口（B 方案：后端代理实时真实定位）
 *
 * 目录保持为 H5 根目录，使站点发布沿用原 app 与链接；服务同时提供：
 *   GET /                → index.html（单文件 H5）
 *   GET /api/health      → 能力探测（只回报是否配置 Key，不回传 Key）
 *   GET /api/geo?name=   → 高德地图 POI 真实坐标（Key 仅服务端持有）
 *   GET /api/org?name=   → 机构主体信息扩展点（原有）
 *
 * 监听 process.env.PORT 并绑定 0.0.0.0，满足单端口反向代理托管要求。
 */
require("./server/server.js");
