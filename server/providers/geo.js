/**
 * 定位通道统一入口（facade）
 *
 * 默认走高德地图开放平台 Web服务 API；如高德配额或可用性不佳，
 * 只需把环境变量 GEO_PROVIDER 改为 tencent 即可回滚到腾讯位置服务实现，
 * 前端与 /api/geo 的返回结构完全不变。
 *
 * 两条通道均为合规白名单数据源、同为 GCJ-02 坐标系，与 91 家网点基准坐标一致，
 * 无需坐标转换。密钥仅由服务端环境变量持有，前端产物与响应体零凭据。
 */
const amap = require("./amap");
const tencent = require("./tencent");

const LABEL = {
  amap: "高德地图开放平台（Web服务 API）",
  tencent: "腾讯位置服务（WebServiceAPI）"
};

function pickProvider(v) {
  const p = String(v == null ? (process.env.GEO_PROVIDER || "amap") : v).trim().toLowerCase();
  return p === "tencent" ? "tencent" : "amap";
}

function impl(v) {
  return pickProvider(v) === "tencent" ? tencent : amap;
}

async function resolveGeo(name, opts, deps) {
  return impl(opts && opts.provider).resolveGeo(name, opts, deps);
}

/** 机构名称联想：当前仅高德通道提供；腾讯通道如实返回不支持，由前端本地词库兜底 */
async function suggestNames(name, opts, deps) {
  const p = impl(opts && opts.provider);
  return typeof p.suggestNames === "function"
    ? p.suggestNames(name, opts, deps)
    : { found: false, reason: "unsupported-provider", suggestions: [] };
}

module.exports = {
  resolveGeo, suggestNames,
  pickProvider,
  providerLabel: (v) => LABEL[pickProvider(v)],
  inScope: amap.inScope,
  // 解析函数导出供单元测试注入 mock（两套实现互不干扰）
  pickPlaceText: amap.pickPlaceText,
  pickInputtips: amap.pickInputtips,
  pickGeocode: amap.pickGeocode,
  pickSuggestions: amap.pickSuggestions,
  pickSuggestion: tencent.pickSuggestion,
  pickGeocoder: tencent.pickGeocoder,
  _resetCache: () => { amap._resetCache(); tencent._resetCache(); }
};
