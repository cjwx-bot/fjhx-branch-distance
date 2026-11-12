# -*- coding: utf-8 -*-
"""构建单文件 H5：福建海峡银行最近网点查询（极简版）。

简化目标（用户 2026-11-05 要求）：
- 仅保留「机构名称」录入 + 「查询」按钮 + 「刷新」按钮；
- 去除：机构类型、单位地址、实时识别、所在地市、所在区县、精确经纬度 六项；
- 结果区仅展示「距离最近的福建海峡银行网点」（hero + 列表），不再反显机构所在行政区划/经纬度；
- 机构事实由 WorkBuddy 会话侧技能全网检索公开渠道补齐、逐字段留痕后内联（intel/org_intel.json），
  前端零 Key：页面不携带任何地图 Key 或凭据，不直连地图域名；定位按「资料库真实坐标 → 同源后端代理实时坐标 → 行政区划中心近似」三级降级。
数据：server/data/branches.json 91 家权威网点 + 内置区县中心坐标 + 技能核验资料库，全部内联。
"""
import json, os, base64, io
from intel_pipeline import load_validated, write_report

# ===== B 方案：后端代理实时真实定位 + 三级降级数据链路（2026-11-07）=====
# 机构事实由 WorkBuddy 会话侧技能全网检索公开渠道补齐、逐字段交叉核验并留痕，
# 结构化落盘为 intel/org_intel.json；构建时强校验后内联为 window.ORG_INTEL。
# 页面不携带任何地图 Key / 商业数据接口凭据，不直连任何第三方地图域名；
# 实时定位仅向同源 /api/geo 发起一次请求，由后端代理持有高德 Web服务 Key。
INTEL_DATA, INTEL_STATS = load_validated()
write_report(INTEL_DATA, INTEL_STATS)
ORG_INTEL_JS = json.dumps(INTEL_DATA, ensure_ascii=False, separators=(",", ":"))

# 静态版跨域代理：构建时注入 GEO_PROXY_URL，则查询阶段经该 URL 调主链接后端 /api/geo
# 获取真实高德坐标（密钥仍仅在服务端，前端零 Key 不变）。主链接（同源）留空，使用相对路径。
# 例：https://fjhx-branch-distance.app.workbuddy.host/api/geo?sharecode=RTP3JR7MH6&name=
GEO_PROXY_URL = os.environ.get("GEO_PROXY_URL", "").strip()

# 静态版单位画像跨域代理：构建时注入 PROFILE_PROXY_URL，则结果卡片与「编制参阅材料」
# 均经该 URL 调主链接后端 /api/profile 取启信慧眼单位画像（凭据仍仅服务端）。
# 主链接（同源）留空，使用相对路径 api/profile。留空时静态版自动降级为「未取得画像」并如实标注。
# 例：https://fjhx-branch-distance.app.workbuddy.host/api/profile?sharecode=RTP3JR7MH6&name=
PROFILE_PROXY_URL = os.environ.get("PROFILE_PROXY_URL", "").strip()

# 静态版机构名称联想跨域代理：构建时注入 SUGGEST_PROXY_URL，录入时经该 URL 调主链接后端
# /api/suggest 取高德实时相近机构名；主链接（同源）留空，使用相对路径 api/suggest。
# 例：https://fjhx-branch-distance.app.workbuddy.host/api/suggest?sharecode=RTP3JR7MH6&name=
SUGGEST_PROXY_URL = os.environ.get("SUGGEST_PROXY_URL", "").strip()

# 街道底图瓦片同源代理：主站留空使用相对路径 api/tiles?；静态 Pages 版注入主站完整 URL
# （含 sharecode），页面只请求该 URL 取得瓦片，不直连任何地图域名、不携带 Key。
# 例：https://fjhx-branch-distance.app.workbuddy.host/api/tiles?sharecode=RTP3JR7MH6&
TILE_PROXY_URL = os.environ.get("TILE_PROXY_URL", "").strip()

# 参阅材料 CSS：规范固化自 fjhx-doc-pipeline/references/style-guide.md
# （深蓝 #0D47A1 / 中蓝 #1976D2 / 浅蓝底 #eef3fb，微软雅黑，A4 12mm×13mm，
#   cover 左侧竖条、章节标题下划线、kv-table 深蓝表头、note 虚线资料来源）
DOC_CSS = r""".doc{font-family:"Microsoft YaHei","微软雅黑","Source Han Sans SC","Noto Sans CJK SC",SimSun,sans-serif;
  color:#1a1a1a;font-size:9.8pt;line-height:1.42;background:#fff;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
.doc *{box-sizing:border-box}
.doc .cover{border-left:7px solid #0D47A1;padding:8px 0 8px 14px;margin-bottom:9px}
.doc .eyebrow{font-size:9pt;color:#1565C0;letter-spacing:1px;margin-bottom:3px}
.doc .cover .title{font-size:16pt;font-weight:800;line-height:1.35;color:#0D47A1}
.doc .cover .subtitle{font-size:10pt;color:#444;margin-top:5px}
.doc .cover .meta{font-size:8.6pt;color:#888;margin-top:6px;line-height:1.6}
.doc h2.sec{font-size:12.5pt;font-weight:800;color:#0D47A1;border-bottom:2.5px solid #0D47A1;
  padding-bottom:3px;margin:11px 0 5px;page-break-after:avoid}
.doc h3.sub{font-size:10.6pt;font-weight:700;color:#0D47A1;margin:7px 0 3px;padding-left:8px;
  border-left:4px solid #1976D2;page-break-after:avoid}
.doc p{margin:3px 0;text-align:justify}
.doc .indent{text-indent:2em}
.doc table{width:100%;border-collapse:collapse;margin:5px 0 8px;font-size:9pt}
.doc th,.doc td{border:1px solid #b9c8e0;padding:4px 6px;vertical-align:top;text-align:left}
.doc thead th{background:#0D47A1;color:#fff;font-weight:700}
.doc tbody tr:nth-child(even) td{background:#eef3fb}
.doc table.kv-table tbody th{background:#0D47A1;color:#fff;width:28%;font-weight:700}
.doc .abstract{background:#eef3fb;border:1px solid #c9d6ec;border-radius:5px;padding:6px 10px;margin:5px 0 8px}
.doc .abstract b{color:#0D47A1}
.doc .toc{background:#f7f9fd;border:1px dashed #b9c8e0;border-radius:5px;padding:6px 10px;margin:5px 0 9px;
  font-size:9pt;line-height:1.65;color:#334}
.doc .toc b{color:#0D47A1}
.doc .coop-card{border:1px solid #c9d6ec;border-radius:6px;margin:5px 0;overflow:hidden}
.doc .coop-card .head{background:linear-gradient(90deg,#0D47A1,#1976D2);color:#fff;font-weight:700;
  font-size:10.2pt;padding:3px 9px;page-break-after:avoid}
.doc .coop-card .body{padding:4px 9px 5px}
.doc .coop-card .row{display:flex;gap:7px;margin:2px 0}
.doc .coop-card .tag{flex:0 0 62px;font-weight:700;color:#1565C0;font-size:9.1pt;padding-top:1px}
.doc .coop-card .val{flex:1}
.doc .coop-card .path{background:#e8f5e9;border-left:3px solid #2E7D32;padding:3px 7px;margin-top:3px;font-size:9.1pt}
.doc .coop-card .path b{color:#2E7D32}
.doc .coop-card .dept{color:#555;font-size:8.8pt;margin-top:2px}
.doc .coop-card .dept b{color:#0D47A1}
.doc ol.tight,.doc ul.tight{margin:3px 0 5px;padding-left:20px}
.doc ol.tight li,.doc ul.tight li{margin:2px 0;text-align:justify}
.doc .note{font-size:8.6pt;color:#777;margin-top:9px;border-top:1px dashed #ccc;padding-top:5px;line-height:1.6}
.doc .seal{display:inline-block;background:#E3F2FD;color:#0D47A1;border-radius:10px;padding:1px 8px;font-size:8.8pt;font-weight:700}
.doc .flag{background:#e8f5e9;border-left:3px solid #2E7D32;padding:4px 8px;margin:4px 0;font-size:9pt}
.doc .verify-links{margin:6px 0 8px;border:1px solid #d4e3f7;border-radius:7px;overflow:hidden}
.doc .verify-links a{display:flex;align-items:center;gap:8px;padding:6px 9px;border-bottom:1px solid #e6ecf4;
  color:#0D47A1;text-decoration:none;font-size:9pt;background:#f7fbff}
.doc .verify-links a:last-child{border-bottom:0}
.doc .verify-links .vl__n{flex:0 0 18px;height:18px;border-radius:5px;background:#0D47A1;color:#fff;
  font-size:8.5pt;display:flex;align-items:center;justify-content:center}
.doc .verify-links .vl__t{flex:1}
.doc .verify-links .vl__go{color:#1976D2;font-weight:700}
@page{size:A4;margin:12mm 13mm}
@media screen and (max-width:600px){.doc{font-size:11pt}.doc table{font-size:10pt}.doc .cover .title{font-size:17pt}
  .doc .coop-card .tag{flex:0 0 56px}.doc .toc{line-height:1.8}}"""
DOC_CSS_JS = json.dumps(DOC_CSS, ensure_ascii=False)

BASE = os.path.dirname(os.path.abspath(__file__))
BRANCH_JSON = os.path.join(BASE, "server", "data", "branches.json")

# 「网点辐射查询」数据索引：由 build_nearby_data.py 依据资料库 DATA 文件夹四份清单生成。
# 索引内联于页面，43,526 家机构明细按地市分片为 nearby_data/cN.js，查询时按包围盒按需加载，
# 不随页面一次性下载；分片均为纯静态公开登记信息，不含任何凭据。
NEARBY_MANIFEST_JSON = os.path.join(BASE, "nearby_data", "manifest.json")
with open(NEARBY_MANIFEST_JSON, "r", encoding="utf-8") as _f:
    NEARBY_MANIFEST = json.load(_f)
NEARBY_MANIFEST_JS = json.dumps(NEARBY_MANIFEST, ensure_ascii=False, separators=(",", ":"))
NEARBY_VER = "20261112a"   # 数据重建后递增，用于分片 URL 绕缓存

# 机构名称本地联想词库（2026-11-08）：公开级画像库 8 家 + 核验资料库 4 家的规范名与别名，
# 构建时内联。后端联想限流/不可达时前端仍即时给出候选（零网络请求），且只给已核验主体、不伪造。
def _local_suggest_payload():
    seen, out = set(), []
    for rel in ("intel/org_profile.json", "intel/org_intel.json"):
        p = os.path.join(BASE, rel)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        for o in (d.get("orgs") or []):
            n = str(o.get("name") or "").strip()
            if not n or n in seen:
                continue
            seen.add(n)
            aliases = [str(a).strip() for a in (o.get("aliases") or []) if str(a).strip()]
            out.append({"n": n, "a": aliases})
    return out

LOCAL_SUGGEST_JS = json.dumps(_local_suggest_payload(), ensure_ascii=False, separators=(",", ":"))

# 详细《业务合作参阅材料》模板与生成逻辑（独立片段，构建时内联进单文件 H5）
# org_struct.js：单位治理与组织画像知识库（通用研判口径）
# brief_doc.js ：十章章节编排、HTML / 纯文本双渲染与导出
# intel_brief.js：技能全网检索核验资料库的匹配、事实渲染与证据索引
_BRIEF_PARTS = ["org_struct.js", "brief_doc.js", "intel_brief.js", "profile_brief.js"]
BRIEF_JS = "\n".join(
    io.open(os.path.join(BASE, n), "r", encoding="utf-8").read().rstrip("\n")
    for n in _BRIEF_PARTS
)

with open(BRANCH_JSON, "r", encoding="utf-8") as f:
    branch_payload = json.load(f)

BRANCH_DATA_JS = json.dumps(branch_payload, ensure_ascii=False, separators=(",", ":"))

ICON_PATH = os.path.join(BASE, "icon.png")
with open(ICON_PATH, "rb") as _f:
    ICON_B64 = base64.b64encode(_f.read()).decode("ascii")

REGION_DATA = {
    "福州市": {
        "鼓楼区": [26.0885, 119.2920], "台江区": [26.0665, 119.3120], "仓山区": [26.0410, 119.2890],
        "晋安区": [26.1010, 119.3120], "马尾区": [25.9870, 119.4510], "长乐区": [25.9450, 119.4870],
        "闽侯县": [26.1530, 119.1490], "连江县": [26.2080, 119.5400], "罗源县": [26.5330, 119.5630],
        "闽清县": [26.2280, 118.8690], "永泰县": [25.8710, 118.9390], "平潭县": [25.5030, 119.7940]
    },
    "厦门市": {
        "思明区": [24.4798, 118.0894], "湖里区": [24.5210, 118.1350], "集美区": [24.5830, 118.0970],
        "海沧区": [24.4830, 118.0270], "同安区": [24.7220, 118.1500], "翔安区": [24.6230, 118.2530]
    },
    "漳州市": {
        "芗城区": [24.5133, 117.6553], "龙文区": [24.5210, 117.6930], "龙海区": [24.4410, 117.7910],
        "漳浦县": [24.1200, 117.6150], "云霄县": [23.9580, 117.3410], "诏安县": [23.7120, 117.1750],
        "东山县": [23.7040, 117.4230], "南靖县": [24.5100, 117.3590], "平和县": [24.3650, 117.3160],
        "华安县": [25.0080, 117.5300], "长泰区": [24.6140, 117.8180]
    },
    "泉州市": {
        "鲤城区": [24.9040, 118.5810], "丰泽区": [24.8840, 118.6010], "洛江区": [24.9400, 118.6500],
        "泉港区": [25.0510, 118.8930], "石狮市": [24.7240, 118.6510], "晋江市": [24.7860, 118.5540],
        "南安市": [24.9650, 118.3780], "惠安县": [25.0310, 118.7900], "安溪县": [25.0730, 118.1780],
        "永春县": [25.3240, 118.2830], "德化县": [25.4920, 118.2390], "金门县": [24.4480, 118.3800]
    },
    "莆田市": {
        "城厢区": [25.4380, 119.0060], "涵江区": [25.4830, 119.0900], "荔城区": [25.4390, 119.0160],
        "秀屿区": [25.2890, 119.1100], "仙游县": [25.3520, 118.6980]
    },
    "宁德市": {
        "蕉城区": [26.6650, 119.5500], "福安市": [27.0870, 119.6540], "福鼎市": [27.0980, 120.2150],
        "霞浦县": [26.8690, 120.0030], "古田县": [26.5700, 118.7470], "屏南县": [26.9080, 118.9850],
        "寿宁县": [27.4570, 119.5020], "周宁县": [27.0830, 119.3420], "柘荣县": [27.2310, 119.8970]
    },
    "龙岩市": {
        "新罗区": [25.0820, 117.0200], "永定区": [24.7270, 116.7400], "漳平市": [25.2880, 117.4060],
        "长汀县": [25.8410, 116.3590], "上杭县": [25.0470, 116.4210], "武平县": [25.0870, 116.0990],
        "连城县": [25.7260, 116.7520]
    },
    "三明市": {
        "三元区": [26.2650, 117.6390], "永安市": [25.9710, 117.3720], "明溪县": [26.3550, 117.1990],
        "清流县": [26.1780, 116.8240], "宁化县": [26.2690, 116.6450], "大田县": [25.6870, 117.8400],
        "尤溪县": [26.1730, 118.1530], "沙县区": [26.4020, 117.7960], "将乐县": [26.7270, 117.4750],
        "泰宁县": [26.8930, 117.1310], "建宁县": [26.8340, 116.8380]
    },
    "南平市": {
        "延平区": [26.6350, 118.1780], "建阳区": [27.3400, 118.1110], "邵武市": [27.3290, 117.4850],
        "武夷山市": [27.7200, 118.0300], "建瓯市": [27.0470, 118.3340], "顺昌县": [26.7830, 117.7940],
        "浦城县": [27.9190, 118.5310], "光泽县": [27.5420, 117.3340], "松溪县": [27.5180, 118.7850],
        "政和县": [27.3570, 118.8510]
    },
    "平潭综合实验区": { "平潭县": [25.5030, 119.7940] },
    "温州市": {
        "鹿城区": [27.9830, 120.6860], "龙湾区": [27.9220, 120.8100], "瓯海区": [27.9400, 120.6000],
        "洞头区": [27.8400, 121.1500], "瑞安市": [27.7700, 120.6650], "乐清市": [28.1040, 120.9730],
        "永嘉县": [28.1500, 120.6900], "平阳县": [27.6600, 120.5700], "苍南县": [27.5100, 120.4100],
        "文成县": [27.7900, 119.9400], "泰顺县": [27.5800, 119.7000]
    }
}
PROVINCE_OF_CITY = {
    "福州市": "福建省", "厦门市": "福建省", "漳州市": "福建省", "泉州市": "福建省", "莆田市": "福建省",
    "宁德市": "福建省", "龙岩市": "福建省", "三明市": "福建省", "南平市": "福建省", "平潭综合实验区": "福建省",
    "温州市": "浙江省"
}
REGION_JS = json.dumps(REGION_DATA, ensure_ascii=False, separators=(",", ":"))
PROV_JS = json.dumps(PROVINCE_OF_CITY, ensure_ascii=False, separators=(",", ":"))

html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <meta name="format-detection" content="telephone=no">
  <title>最近网点查询</title>
  <meta name="description" content="输入机构名称，按真实经纬度精确测算最近的福建海峡银行网点。">
  <link rel="icon" href="__ICON_B64__">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="福建海峡银行">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:url" content="https://cjwx-bot.github.io/fjhx-branch-distance/">
  <meta property="og:title" content="最近网点查询">
  <meta property="og:description" content="输入机构名称，按真实经纬度精确测算最近的福建海峡银行网点。">
  <meta property="og:image" content="https://cjwx-bot.github.io/fjhx-branch-distance/share-card.png">
  <meta property="og:image:secure_url" content="https://cjwx-bot.github.io/fjhx-branch-distance/share-card.png">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="600">
  <meta property="og:image:height" content="600">
  <meta property="og:image:alt" content="最近网点查询 · 福建海峡银行">
  <meta itemprop="name" content="最近网点查询">
  <meta itemprop="description" content="输入机构名称，按真实经纬度精确测算最近的福建海峡银行网点。">
  <meta itemprop="image" content="https://cjwx-bot.github.io/fjhx-branch-distance/share-card.png">
  <meta name="twitter:card" content="summary">
  <meta name="theme-color" content="#006EFF">
  <style>
    :root{
      --brand:#1a5bb8; --brand-2:#2a75c7; --brand-deep:#0f3f86;
      --brand-soft:#eaf2fc; --brand-line:#d4e3f7;
      --ink:#16243a; --ink-2:#5a6b82; --ink-3:#92a2b8;
      --bg:#eef2f8; --card:#ffffff; --line:#e6ecf4;
      --ok:#1f9d57; --ok-soft:#e6f6ec; --warn:#c8841a; --danger:#d4473b;
      --radius:16px; --shadow:0 6px 22px rgba(26,91,184,.08);
    }
    *{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
    html,body{background:var(--bg)}
    body{font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei","PingFang SC","Helvetica Neue",sans-serif;
      color:var(--ink);font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
    .app{max-width:520px;margin:0 auto;min-height:100vh;background:var(--bg);display:flex;flex-direction:column}
    .top{position:relative;background:linear-gradient(135deg,var(--brand) 0%,var(--brand-2) 55%,#3f8fdc 100%);
      color:#fff;padding:26px 18px 30px;overflow:hidden}
    .top:after{content:"";position:absolute;right:-40px;top:-40px;width:180px;height:180px;border-radius:50%;background:rgba(255,255,255,.10)}
    .top:before{content:"";position:absolute;right:30px;bottom:-50px;width:120px;height:120px;border-radius:50%;background:rgba(255,255,255,.08)}
    .top__row{position:relative;z-index:1;display:flex;align-items:center;gap:10px}
    .top__logo{width:38px;height:38px;border-radius:10px;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;font-size:20px;backdrop-filter:blur(2px)}
    .top__title{font-size:19px;font-weight:700;letter-spacing:.5px}
    .top__sub{position:relative;z-index:1;margin-top:10px;font-size:12.5px;color:rgba(255,255,255,.86);line-height:1.55}
    .top__badge{position:relative;z-index:1;margin-top:12px;display:inline-flex;align-items:center;gap:6px;
      background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.22);padding:5px 11px;border-radius:999px;font-size:11.5px;color:#fff}
    .dot{width:6px;height:6px;border-radius:50%;background:#9be7b4;box-shadow:0 0 0 0 rgba(155,231,180,.7);animation:pulse 1.8s infinite}
    @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(155,231,180,.7)}70%{box-shadow:0 0 0 7px rgba(155,231,180,0)}100%{box-shadow:0 0 0 0 rgba(155,231,180,0)}}

    .body{flex:1;padding:18px 14px 8px;margin-top:-14px}
    .card{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);padding:16px;margin-bottom:14px}
    .card__h{display:flex;align-items:center;gap:8px;margin-bottom:14px}
    .card__h .bar{width:4px;height:16px;border-radius:3px;background:var(--brand)}
    .card__h h2{font-size:15.5px;font-weight:700;color:var(--ink)}

    label.fld{display:block;font-size:13px;color:var(--ink-2);font-weight:600;margin-bottom:7px}
    label.fld .opt{font-size:11px;color:var(--ink-3);font-weight:400}
    .inp{width:100%;border:1.5px solid var(--line);background:#fbfdff;border-radius:11px;padding:12px 13px;font-size:15px;color:var(--ink);outline:none;transition:.18s;font-family:inherit}
    .inp:focus{border-color:var(--brand);background:#fff;box-shadow:0 0 0 3px var(--brand-soft)}
    .inp::placeholder{color:#aab6c6}

    .btn{width:100%;border:none;border-radius:12px;font-size:16px;font-weight:700;cursor:pointer;font-family:inherit;transition:.15s;display:flex;align-items:center;justify-content:center;gap:8px}
    .btn-primary{height:50px;background:linear-gradient(135deg,var(--brand) 0%,var(--brand-2) 100%);color:#fff;box-shadow:0 8px 20px rgba(26,91,184,.28)}
    .btn-primary:active{transform:translateY(1px)}
    .btn-ghost{height:50px;background:#f1f5fb;color:var(--brand);font-size:15px;font-weight:600}
    .btn-ghost:active{opacity:.7}
    .btn-row{display:flex;gap:10px;margin-top:16px}
    .btn-row .btn-primary{flex:2}
    .btn-row .btn-ghost{flex:1}

    .tip{font-size:12.5px;color:var(--ink-2);background:var(--brand-soft);border-radius:11px;padding:10px 12px;line-height:1.55}
    .tip.err{background:#fdecea;color:var(--danger)}

    .orgbadge{display:none;background:var(--ok-soft);border:1px solid #c4e8d2;border-radius:11px;padding:10px 12px;font-size:13px;line-height:1.6;color:#1c7a45;margin-bottom:12px;word-break:break-word}
    .orgbadge.badge-warn{background:#fff4e5;border-color:#f3c98b;color:#9a5b00}
    .badge-link{color:#0b5fff;text-decoration:underline;font-weight:600;cursor:pointer}
    .profile-box{display:none;background:#f4f7ff;border:1px solid #c9d8ff;border-radius:13px;padding:12px 13px;margin-bottom:12px;font-size:13px;line-height:1.55;color:#1f3a73;word-break:break-word}
    .profile-box .pb__head{font-weight:700;font-size:13px;margin-bottom:8px;color:#0b3aa0}
    .profile-box .pb__rows{display:flex;flex-direction:column;gap:5px}
    .profile-box .pb__row{display:flex;gap:10px;align-items:baseline}
    .profile-box .pb__k{flex:0 0 96px;color:#5b6b8c;font-size:12.5px}
    .profile-box .pb__v{flex:1;font-weight:600;color:#14264d}
    .profile-box .pb__foot{margin-top:8px;font-size:12px;color:#7a8aa9}

    /* 机构名称实时联想下拉 */
    .sug-wrap{position:relative}
    .sug-list{display:none;position:absolute;left:0;right:0;top:calc(100% + 6px);z-index:40;
      background:#fff;border:1px solid #d3e0f5;border-radius:12px;padding:5px;max-height:270px;overflow-y:auto;
      box-shadow:0 12px 34px rgba(13,71,161,.16)}
    .sug-list.show{display:block}
    .sug-item{padding:9px 11px;border-radius:9px;cursor:pointer;display:flex;flex-direction:column;gap:3px}
    .sug-item:hover,.sug-item.active{background:#eef3fb}
    .sug-item__n{font-size:14px;font-weight:600;color:#14264d;line-height:1.35;word-break:break-all}
    .sug-item__d{font-size:12px;color:#6b7a99;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .sug-item__tag{font-size:11px;color:#0b5f9e;font-weight:600}
    .sug-hint{padding:7px 11px 5px;font-size:11.5px;color:#8b98b2;border-bottom:1px solid #eef2f9;margin-bottom:3px}

    /* 模式切换与「网点辐射查询」 */
    .mode-tabs{display:flex;gap:5px;padding:4px;background:#dfe9f7;border-radius:13px;margin-bottom:14px}
    .mode-tab{flex:1;border:none;background:transparent;color:#4a6285;font-family:inherit;font-size:13.5px;font-weight:600;
      padding:9px 6px;border-radius:10px;cursor:pointer;transition:.15s;line-height:1.35}
    .mode-tab.on{background:#fff;color:var(--brand-deep);box-shadow:0 3px 10px rgba(15,63,134,.14)}
    .rad-row{display:flex;gap:10px;align-items:flex-end}
    .rad-row .rad-main{flex:1;min-width:0}
    .rad-row .rad-side{flex:0 0 104px}
    .rad-side .inp{padding:12px 9px;text-align:center}
    .rad-unit{position:relative}
    .rad-unit:after{content:"km";position:absolute;right:9px;top:50%;transform:translateY(-50%);font-size:12px;color:var(--ink-3);pointer-events:none}
    .rad-stat{display:flex;gap:8px;flex-wrap:wrap;margin:13px 0 10px}
    .rad-stat__item{flex:1;min-width:74px;background:var(--brand-soft);border-radius:11px;padding:9px 6px;text-align:center}
    .rad-stat__n{font-size:20px;font-weight:800;color:var(--brand-deep);line-height:1.2}
    .rad-stat__t{font-size:11px;color:var(--ink-2);margin-top:2px}
    .rad-filter{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-bottom:9px}
    .rad-chip{border:1px solid var(--brand-line);background:#fff;color:var(--ink-2);border-radius:999px;
      padding:5px 11px;font-size:12px;cursor:pointer;font-family:inherit;transition:.15s}
    .rad-chip.on{background:var(--brand);border-color:var(--brand);color:#fff;font-weight:600}
    .rad-mini{border:1.5px solid var(--line);background:#fbfdff;border-radius:9px;padding:6px 8px;
      font-size:12px;color:var(--ink);font-family:inherit;outline:none;max-width:132px}
    .rad-mini:focus{border-color:var(--brand)}
    .rad-list{display:flex;flex-direction:column;gap:8px;margin-top:10px}
    .rad-item{border:1px solid var(--line);border-radius:11px;padding:10px 11px;background:#fbfdff}
    .rad-item__top{display:flex;justify-content:space-between;gap:9px;align-items:baseline}
    .rad-item__n{font-size:13.5px;font-weight:650;color:var(--ink);line-height:1.4;word-break:break-all}
    .rad-item__d{font-size:12.5px;font-weight:700;color:var(--brand);white-space:nowrap}
    .rad-item__meta{margin-top:5px;font-size:12px;color:var(--ink-2);line-height:1.55;word-break:break-all}
    .rad-tag{display:inline-block;background:#e8f1ff;color:#0b4ea2;border-radius:5px;padding:1px 6px;font-size:11px;margin-right:5px}
    .rad-tag.lv{background:#eaf7ee;color:#1c7a45}
    .rad-pager{display:flex;justify-content:center;align-items:center;gap:11px;margin-top:12px;font-size:12.5px;color:var(--ink-2)}
    .rad-pager button{border:1px solid var(--brand-line);background:#fff;color:var(--brand);border-radius:8px;
      padding:5px 12px;font-size:12.5px;cursor:pointer;font-family:inherit}
    .rad-pager button:disabled{opacity:.4;cursor:default}
    .rad-note{margin-top:12px;font-size:11.5px;color:var(--ink-3);line-height:1.65;
      background:#f7f9fc;border-radius:9px;padding:9px 10px}
    .rad-loading{text-align:center;padding:18px 10px;font-size:13px;color:var(--ink-2)}

    /* 半径结果地图视图：按经纬度等距投影自绘点位分布图，零外部地图依赖 */
    .rad-viewtabs{display:flex;gap:3px;margin-left:auto;background:#eef3fb;border-radius:9px;padding:3px}
    .rad-viewtabs button{border:none;background:transparent;color:#4a6285;font-family:inherit;font-size:12px;font-weight:700;
      padding:5px 9px;border-radius:7px;cursor:pointer;white-space:nowrap}
    .rad-viewtabs button.on{background:#fff;color:var(--brand-deep);box-shadow:0 2px 7px rgba(15,63,134,.12)}
    .rad-map-wrap{margin-top:11px}
    .rad-map-head{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px}
    .rad-map-head .mh{font-size:11.5px;color:var(--ink-2);background:var(--brand-soft);border-radius:8px;padding:4px 8px}
    .rad-map-head .mh b{color:var(--brand-deep)}
    .rad-map{position:relative;width:100%;height:min(62vh,460px);border:1px solid var(--brand-line);border-radius:13px;
      overflow:hidden;background:linear-gradient(180deg,#f8fbff 0%,#eef5fe 100%);touch-action:none;user-select:none}
    .rad-tiles{position:absolute;inset:0;overflow:hidden;z-index:0;background:#eaf0f7;pointer-events:none}
    .rad-tiles__inner{position:absolute;left:0;top:0;width:0;height:0;transform-origin:0 0;will-change:transform}
    .rad-tiles img{position:absolute;width:256px;height:256px;max-width:none;display:block;pointer-events:none;opacity:0}
    .rad-tiles img.ok{opacity:1}
    .rad-tiles img.bad{display:none}
    .rad-map svg{position:relative;z-index:1;display:block;width:100%;height:100%;cursor:grab;background:transparent}
    .rad-map svg.dragging{cursor:grabbing}
    .rad-grid{stroke:#dce8f8;stroke-width:1;opacity:.5}
    .rad-map.has-tiles .rad-grid{opacity:.22}
    .rad-hud-bg{fill:#fff;opacity:.84}
    .rad-ring{fill:rgba(26,91,184,.055);stroke:#1a5bb8;stroke-width:1.5;stroke-dasharray:6 5}
    .rad-ring-inner{fill:none;stroke:#a8c4e8;stroke-width:1;stroke-dasharray:3 5}
    .rad-axis{stroke:#c2d7f1;stroke-width:1;stroke-dasharray:4 6}
    .rad-pin{cursor:pointer}
    .rad-pin:hover{opacity:.72}
    .rad-cluster{cursor:pointer}
    .rad-cluster circle{stroke:#fff;stroke-width:2}
    .rad-cluster text{fill:#fff;font-size:10px;font-weight:800;text-anchor:middle;dominant-baseline:central;font-family:inherit}
    .rad-center-pin text{fill:#fff;font-size:11px;font-weight:800;text-anchor:middle;dominant-baseline:central;font-family:inherit}
    .rad-map__lbl{fill:#0f3f86;font-size:10.5px;font-weight:700;font-family:inherit;paint-order:stroke;stroke:#fff;stroke-width:3px}
    .rad-map__ov{fill:#5a6b82;font-size:10px;font-family:inherit;paint-order:stroke;stroke:#fff;stroke-width:3px}
    .rad-tools{position:absolute;right:9px;top:9px;display:flex;flex-direction:column;gap:6px;z-index:2}
    .rad-tools button{width:32px;height:32px;border:1px solid var(--brand-line);background:rgba(255,255,255,.94);
      color:var(--brand-deep);border-radius:9px;font-size:15px;font-weight:700;cursor:pointer;font-family:inherit;
      box-shadow:0 2px 8px rgba(15,63,134,.12)}
    .rad-tools button:active{background:var(--brand-soft)}
    .rad-tools button.off{background:#e9edf3;color:#98a5b8}
    .rad-legend{display:flex;flex-wrap:wrap;gap:6px 12px;margin:9px 0 2px;font-size:11.5px;color:var(--ink-2)}
    .rad-legend span{display:inline-flex;align-items:center;gap:5px}
    .rad-legend i{width:10px;height:10px;border-radius:50%;display:inline-block;border:1.5px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.08)}
    .rad-pin-info{margin-top:9px;border:1px solid var(--brand-line);background:#f7fbff;border-radius:11px;padding:10px 11px;
      font-size:12.5px;line-height:1.6;color:var(--ink);min-height:44px}
    .rad-pin-info .pi__t{font-weight:700;color:var(--brand-deep);font-size:13.5px;margin-bottom:4px;word-break:break-all}
    .rad-pin-info .pi__r{color:var(--ink-2)}
    .rad-pin-info .pi__row{padding:5px 0;border-top:1px dashed #dce8f7;cursor:pointer}
    .rad-pin-info .pi__row:first-of-type{border-top:0}
    /* 点击图钉弹出的单位主要信息卡 */
    .pin-modal{position:fixed;inset:0;z-index:120;background:rgba(12,24,45,.46);display:none;
      align-items:center;justify-content:center;padding:20px}
    .pin-modal.on{display:flex}
    .pin-card{background:#fff;border-radius:16px;width:100%;max-width:430px;max-height:84vh;overflow:auto;
      box-shadow:0 18px 50px rgba(9,25,51,.28);padding:16px 16px 14px;font-size:13px;line-height:1.6;color:var(--ink)}
    .pin-card__hd{display:flex;align-items:flex-start;gap:10px;margin-bottom:5px}
    .pin-card__ttl{flex:1;font-size:15px;font-weight:700;color:var(--brand-deep);word-break:break-all;line-height:1.45}
    .pin-card__x{flex:0 0 auto;border:0;background:#eef2f8;color:#5b6b8c;width:28px;height:28px;border-radius:50%;
      font-size:18px;line-height:26px;text-align:center;cursor:pointer;font-family:inherit}
    .pin-card__sub{font-size:11.5px;color:var(--ink-3);margin:0 0 10px}
    .pin-card__row{display:flex;gap:10px;padding:7px 0;border-top:1px solid #eef3fa}
    .pin-card__row:first-of-type{border-top:0}
    .pin-card__k{flex:0 0 72px;color:#6b7a93;font-size:12.5px}
    .pin-card__v{flex:1;color:#14264d;font-weight:600;word-break:break-all}
    .pin-card__dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;border:1px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.08)}
    .pin-card__dist{color:#1a5bb8}
    .pin-card__acts{display:flex;gap:8px;margin-top:12px}
    .pin-card__acts button{flex:1;border:1px solid var(--brand-line);background:var(--brand-soft);color:var(--brand-deep);
      border-radius:9px;padding:8px;font-size:12.5px;font-weight:600;cursor:pointer;font-family:inherit}
    .pin-card__acts button.ghost{background:#fff;color:#5b6b8c}
    .pin-card__li{padding:9px 8px;border:1px solid #e8f0fa;border-radius:9px;margin-bottom:7px;cursor:pointer;background:#fbfdff}
    .pin-card__li:active{background:#eef5ff}
    .pin-card__li .a{font-weight:600;color:#14264d;word-break:break-all}
    .pin-card__li .b{font-size:11.5px;color:#6b7a93;margin-top:2px}
    .pin-card__more{font-size:11.5px;color:var(--ink-3);padding:4px 2px}
    .rad-map-note{margin-top:8px;font-size:11px;color:var(--ink-3);line-height:1.6}
    .rad-map-wrap.full{position:fixed;inset:0;z-index:95;background:#fff;padding:12px 14px;overflow:auto;margin:0;
      display:flex;flex-direction:column}
    .rad-map-wrap.full .rad-map{height:auto;flex:1;min-height:300px}
    .rad-map-wrap.full .rad-pin-info{max-height:24vh;overflow:auto}
    body.rad-map-lock{overflow:hidden}
    .badge-link:hover{color:#0837c4}
    .orgbadge b{color:#13683a}

    .hero{display:none;border-radius:16px;overflow:hidden;margin-bottom:12px;
      background:linear-gradient(135deg,var(--brand-deep) 0%,var(--brand) 60%,var(--brand-2) 100%);color:#fff;position:relative;box-shadow:0 10px 26px rgba(26,91,184,.30)}
    .hero:after{content:"";position:absolute;right:-30px;top:-30px;width:130px;height:130px;border-radius:50%;background:rgba(255,255,255,.10)}
    .hero__inner{position:relative;z-index:1;padding:16px}
    .hero__tag{display:inline-flex;align-items:center;gap:6px;font-size:11.5px;background:rgba(255,255,255,.18);padding:4px 10px;border-radius:999px;margin-bottom:10px}
    .hero__name{font-size:17px;font-weight:700;line-height:1.4}
    .hero__meta{margin-top:8px;font-size:12.5px;color:rgba(255,255,255,.82);line-height:1.55}
    .hero__dist{display:flex;align-items:baseline;gap:6px;margin-top:12px}
    .hero__dist .n{font-size:30px;font-weight:800;letter-spacing:.5px}
    .hero__dist .u{font-size:14px;color:rgba(255,255,255,.85)}
    .hero__phone{margin-top:10px;display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.16);padding:6px 12px;border-radius:10px;font-size:13px;color:#fff;text-decoration:none}

    .list{display:flex;flex-direction:column;gap:9px}
    .item{border:1px solid var(--line);border-radius:12px;padding:11px 12px;background:#fff;display:flex;gap:10px;align-items:flex-start}
    .item__rank{flex:0 0 22px;height:22px;border-radius:7px;background:var(--brand-soft);color:var(--brand);font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-top:2px}
    .item__main{flex:1;min-width:0}
    .item__name{font-size:14px;font-weight:600;color:var(--ink)}
    .item__type{font-size:11px;color:var(--ink-3);margin-top:2px}
    .item__addr{font-size:12.5px;color:var(--ink-2);margin-top:5px;line-height:1.5;word-break:break-all}
    .item__dist{flex:0 0 auto;text-align:right}
    .item__dist .d{font-size:14px;font-weight:700;color:var(--brand)}
    .item__dist .p{font-size:11.5px;color:var(--ok);margin-top:3px}
    .empty{text-align:center;color:var(--ink-3);padding:26px 10px;font-size:13.5px}
    .empty .ic{font-size:32px;display:block;margin-bottom:8px;opacity:.5}

    .notes{font-size:12.5px;color:var(--ink-2);line-height:1.75;padding-left:18px}
    .notes li{margin-bottom:6px}
    .foot{text-align:center;padding:14px 16px 22px;font-size:11.5px;color:var(--ink-3)}

    .backend{display:none}
    .backend.show{display:block;margin-top:12px}
    .toggle{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--ink-2);cursor:pointer;user-select:none;margin-top:14px}
    .toggle .sw{width:38px;height:22px;border-radius:999px;background:#cfd8e3;position:relative;transition:.2s;flex:0 0 auto}
    .toggle .sw:after{content:"";position:absolute;top:2px;left:2px;width:18px;height:18px;border-radius:50%;background:#fff;transition:.2s}
    .toggle.on .sw{background:var(--brand)}
    .toggle.on .sw:after{transform:translateX(16px)}
    .backend__tip{font-size:12.5px;color:var(--ink-2);background:var(--brand-soft);border-radius:10px;padding:9px 11px;margin-bottom:12px;line-height:1.55}

    .mask{position:fixed;inset:0;background:rgba(15,25,40,.5);display:none;align-items:center;justify-content:center;z-index:50;padding:22px}
    .mask.show{display:flex}
    .sheet{background:#fff;border-radius:16px;width:100%;max-width:480px;padding:18px;max-height:82vh;display:flex;flex-direction:column}
    .sheet h3{font-size:16px;margin-bottom:12px}
    .sheet pre{background:#f6f8fc;border:1px solid var(--line);border-radius:11px;padding:12px;font-size:12.5px;color:var(--ink);white-space:pre-wrap;word-break:break-all;flex:1;overflow:auto;line-height:1.6;font-family:-apple-system,"Microsoft YaHei",sans-serif;max-height:46vh}
    .sheet__btns{display:flex;gap:10px;margin-top:14px}
    .sheet__btns .btn{flex:1;height:46px}

    .toast{position:fixed;left:50%;bottom:64px;transform:translateX(-50%) translateY(20px);background:rgba(22,36,58,.92);color:#fff;font-size:13.5px;padding:11px 18px;border-radius:999px;opacity:0;transition:.25s;z-index:80;pointer-events:none;display:flex;align-items:center;gap:7px}
    .toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
    /* ===== 参阅材料（规范来源：fjhx-doc-pipeline/style-guide.md） ===== */
    __DOC_CSS__
    .brief{display:flex;gap:10px;align-items:flex-start;background:var(--brand-soft);
      border:1px solid var(--brand-line);border-radius:12px;padding:11px 12px;margin-top:12px}
    .brief__ic{font-size:20px;line-height:1.2}
    .brief__main{flex:1;min-width:0}
    .brief__ttl{font-size:13.5px;font-weight:700;color:var(--brand-deep)}
    .brief__pill{display:inline-block;background:var(--ok-soft);color:#13683a;font-size:10.5px;
      font-weight:600;border-radius:999px;padding:1px 7px;margin-left:4px;vertical-align:1px}
    .brief__desc{font-size:12px;color:var(--ink-2);margin-top:4px;line-height:1.5}
    .brief__toc{font-size:11px;color:var(--brand);margin-top:6px;line-height:1.6;
      background:#fff;border:1px dashed var(--brand-line);border-radius:8px;padding:7px 9px;word-break:break-all}
    .sheet--doc .doc{flex:1;overflow:auto;max-height:54vh;padding:10px 8px;
      border:1px solid var(--line);border-radius:9px;background:#fff}
    /* ===== 全文全屏浏览 + 现场补录（2026-11-06） ===== */
    .sheet--doc .sheet__hd{display:flex;align-items:center;gap:9px;margin-bottom:9px}
    .sheet--doc .sheet__hd h3{flex:1;margin:0;font-size:15px;line-height:1.4}
    .fs-btn{flex:0 0 auto;border:1px solid var(--brand-line);background:#fff;color:var(--brand-deep);
      border-radius:9px;padding:7px 11px;font-size:12.5px;font-weight:700;cursor:pointer;white-space:nowrap}
    .fs-btn:active{background:var(--brand-soft)}
    .mask.fs-pad{padding:0}
    .mask .sheet--doc.fs{width:100%;max-width:none;height:100vh;height:100dvh;max-height:none;
      border-radius:0;padding:12px 14px 10px}
    .sheet--doc.fs .doc{max-height:none;flex:1;padding:14px 10px;-webkit-overflow-scrolling:touch}
    .sheet--doc.fs .sheet__btns{margin-top:9px}
    body.fs-lock{overflow:hidden}
    .fill{border:1px dashed var(--brand-line);background:var(--brand-soft);border-radius:9px;
      padding:8px 10px;margin-bottom:10px;font-size:12px}
    .fill summary{cursor:pointer;color:var(--brand-deep);font-weight:700;list-style:none;line-height:1.5}
    .fill summary::-webkit-details-marker{display:none}
    .fill summary:before{content:"▸ "}
    .fill[open] summary:before{content:"▾ "}
    .fill__grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px 9px;margin-top:9px}
    .fill label{display:block;color:var(--ink-2);font-size:11px}
    .fill input{width:100%;height:34px;border:1px solid var(--line);border-radius:7px;
      padding:0 8px;margin-top:3px;background:#fff;font-size:12.5px;color:var(--ink)}
    .fill__tip{color:var(--ink-3);font-size:11px;line-height:1.55;margin-top:8px}
    .fill__row{display:flex;gap:9px;margin-top:8px}
    .fill__row .btn{height:34px;flex:0 0 auto;padding:0 12px;font-size:12px}
    @media (max-width:560px){.fill__grid{grid-template-columns:1fr}}
    /* ===== 两阶段编制：资料库调取进度层（2026-11-07 · 前端零 Key） ===== */
    .mask--prog{z-index:70}
    .sheet--prog{display:flex;flex-direction:column;max-width:440px;max-height:88vh;overflow:hidden}
    .prog__top{flex:0 0 auto}
    .prog__scroll{flex:1 1 auto;min-height:0;overflow:auto;-webkit-overflow-scrolling:touch}
    .prog__hd{display:flex;gap:11px;align-items:center;margin-bottom:14px}
    .prog__hd h3{margin:0;font-size:15.5px;line-height:1.4}
    .prog__ico{flex:0 0 38px;height:38px;border-radius:11px;background:var(--brand-soft);
      color:var(--brand-deep);display:flex;align-items:center;justify-content:center;font-size:18px}
    .prog__sub{font-size:11.5px;color:var(--ink-3);margin-top:3px;max-width:270px;
      overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    .prog__barwrap{display:flex;align-items:center;gap:10px}
    .prog__bar{flex:1;height:9px;border-radius:999px;background:#e8eef7;overflow:hidden}
    .prog__fill{height:100%;width:0;border-radius:999px;
      background:linear-gradient(90deg,var(--brand),var(--brand-2));transition:width .34s ease}
    .prog__pct{flex:0 0 44px;text-align:right;font-size:13px;font-weight:700;
      color:var(--brand-deep);font-variant-numeric:tabular-nums}
    .prog__now{font-size:12px;color:var(--ink-2);margin:9px 0 10px;line-height:1.55;min-height:18px}
    .prog__stages{flex:0 0 auto;list-style:none;margin:0;padding:0;border:1px solid var(--line);border-radius:10px;overflow:hidden}
    .prog__stages li{display:flex;gap:9px;align-items:flex-start;padding:8px 10px;font-size:12px;
      border-bottom:1px solid var(--line);color:var(--ink-3);line-height:1.45}
    .prog__stages li:last-child{border-bottom:0}
    .prog__stages .st{flex:0 0 17px;height:17px;border-radius:50%;border:1.5px solid #cfd9e8;
      font-size:10px;display:flex;align-items:center;justify-content:center;margin-top:1px;background:#fff}
    .prog__stages li.done{color:var(--ink-2);background:#f7fbff}
    .prog__stages li.done .st{background:#2E7D32;border-color:#2E7D32;color:#fff}
    .prog__stages li.run{color:var(--brand-deep);background:var(--brand-soft);font-weight:600}
    .prog__stages li.run .st{border-color:var(--brand);color:var(--brand);animation:progSpin 1.2s linear infinite}
    @keyframes progSpin{to{transform:rotate(360deg)}}
    .prog__stages .sd{display:block;font-size:10.5px;color:var(--ink-3);font-weight:400;margin-top:2px}
    .prog__note{font-size:11px;color:var(--ink-3);line-height:1.6;margin-top:10px;
      background:#f7f9fc;border-radius:9px;padding:8px 10px}
    .prog__note summary{cursor:pointer;color:var(--brand-deep);font-weight:700;list-style:none}
    .prog__note summary::-webkit-details-marker{display:none}
    .prog__note summary:before{content:"▸ "}
    .prog__note[open] summary:before{content:"▾ "}
    .prog__note p{margin:7px 0 0}
    .sheet--prog .sheet__btns{flex:0 0 auto;margin-top:10px}
    .sheet--prog .sheet__btns .btn{height:40px;font-size:13px}
  </style>
</head>
<body>
  <div class="app">
    <header class="top">
      <div class="top__row">
        <div class="top__logo">🏦</div>
        <div class="top__title">福建海峡银行最近网点查询</div>
      </div>
      <p class="top__sub">输入机构名称（模糊即可），自动匹配距离最近的福建海峡银行网点。福建全省及浙江温州适用。</p>
    </header>

    <main class="body">
      <div class="mode-tabs" role="tablist">
        <button class="mode-tab on" id="tabOrg" role="tab" aria-selected="true">机构查最近网点</button>
        <button class="mode-tab" id="tabRadius" role="tab" aria-selected="false">网点半径内机构</button>
      </div>

      <!-- 查询卡片 -->
      <section class="card" id="orgCard">
        <div class="card__h"><span class="bar"></span><h2>机构名称查询</h2></div>

        <label class="fld" for="orgName">机构名称 <span class="opt">（边输入边提示相近机构，可点选）</span></label>
        <div class="sug-wrap">
          <input id="orgName" class="inp" type="text" autocomplete="off" placeholder="如：福建省财政厅 / 福州市教育局" maxlength="50">
          <div class="sug-list" id="sugList"></div>
        </div>

        <div class="btn-row">
          <button class="btn btn-primary" id="searchBtn">🔍 查询</button>
          <button class="btn btn-ghost" id="refreshBtn">↻ 刷新</button>
        </div>

        <!-- 高级设置（可选，默认收起） -->
        <div class="toggle" id="advToggle"><span class="sw"></span><span>高级设置（可选）</span></div>
        <div class="backend" id="advPanel">
          <p class="backend__tip">本工具前端零 Key：机构定位优先调取技能全网检索核验资料库的真实坐标；未收录时由同源后端代理向高德地图开放平台取得 POI 真实坐标，密钥仅在服务端持有、不下发页面；后端不可用或未配置时自动降级为行政区划中心近似并如实标注。本项为可选自定义后端扩展入口，留空即使用同源定位服务。</p>
          <label class="fld" for="backendUrl">后端代理地址 <span class="opt">（实时核验，可选）</span></label>
          <input id="backendUrl" class="inp" type="text" placeholder="后端地址，如 https://你的域名" maxlength="200">
          <button class="btn btn-ghost" id="saveBackend" style="margin-top:10px">保存</button>
          <div class="tip" id="backendStatus" style="display:none;margin-top:10px"></div>
        </div>
      </section>

      <!-- 结果卡片 -->
      <section class="card" id="resultCard">
        <div class="card__h"><span class="bar"></span><h2>查询结果</h2></div>
        <div class="orgbadge" id="orgBadge"></div>
        <div class="profile-box" id="profileBox" style="display:none"></div>
        <div class="tip" id="resultTip">请输入机构名称后点击「查询」。</div>
        <div class="hero" id="hero"></div>
        <div class="list" id="resultList"></div>
        <div class="brief" id="briefBar" style="display:none">
          <div class="brief__ic">📄</div>
          <div class="brief__main">
            <div class="brief__ttl">业务合作参阅材料 <span class="brief__pill" id="briefPill">待编制</span></div>
            <div class="brief__desc" id="briefDesc"></div>
            <div class="brief__toc" id="briefToc"></div>
          </div>
        </div>
        <div class="btn-row" id="briefActions" style="display:none">
          <button class="btn btn-primary" id="viewBrief">编制并查看参阅材料</button>
          <button class="btn btn-ghost" id="downloadBrief">编制并下载材料</button>
        </div>
        <div class="btn-row" id="resultActions" style="display:none">
          <button class="btn btn-ghost" id="copyBtn">复制结果到群</button>
        </div>
      </section>

      <!-- 网点辐射查询：录入卡片 -->
      <section class="card" id="radiusCard" style="display:none">
        <div class="card__h"><span class="bar"></span><h2>网点半径内机构查询</h2></div>

        <label class="fld" for="branchName">本行网点名称 <span class="opt">（模糊录入后点选具体网点）</span></label>
        <div class="sug-wrap">
          <input id="branchName" class="inp" type="text" autocomplete="off" placeholder="如：鼓楼 / 三山 / 平潭" maxlength="50">
          <div class="sug-list" id="branchSug"></div>
        </div>
        <div class="tip" id="branchPicked" style="display:none;margin-top:10px"></div>

        <label class="fld" for="radiusKm" style="margin-top:14px">查询半径 <span class="opt">（以所选网点经纬度为圆心，0.1—50 公里）</span></label>
        <div class="rad-row">
          <div class="rad-main"><div class="tip">按经纬度直线距离测算，覆盖机关、事业单位、学校三类主体。</div></div>
          <div class="rad-side rad-unit"><input id="radiusKm" class="inp" type="number" min="0.1" max="50" step="0.1" value="3" inputmode="decimal"></div>
        </div>

        <div class="btn-row">
          <button class="btn btn-primary" id="radiusBtn">🔍 查询半径内机构</button>
          <button class="btn btn-ghost" id="radiusReset">↻ 重置</button>
        </div>
      </section>

      <!-- 网点辐射查询：结果卡片 -->
      <section class="card" id="radResultCard" style="display:none">
        <div class="card__h"><span class="bar"></span><h2>半径内机构分布</h2>
          <div class="rad-viewtabs" role="tablist">
            <button type="button" class="on" id="radViewMap" role="tab" aria-selected="true">🗺 地图</button>
            <button type="button" id="radViewList" role="tab" aria-selected="false">☰ 清单</button>
          </div>
        </div>
        <div class="tip" id="radSummary">请选择本行网点并录入半径后查询。</div>
        <div class="rad-stat" id="radStat" style="display:none"></div>
        <div class="rad-filter" id="radFilter" style="display:none">
          <button class="rad-chip on" data-cat="0">全部</button>
          <button class="rad-chip" data-cat="1">机关</button>
          <button class="rad-chip" data-cat="2">事业单位</button>
          <button class="rad-chip" data-cat="4">学校</button>
          <select class="rad-mini" id="radLevel">
            <option value="">全部层级</option>
            <option value="1">中央级</option>
            <option value="2">省属</option>
            <option value="3">市属</option>
            <option value="4">区县属</option>
            <option value="5">街镇属</option>
            <option value="0">未标明</option>
          </select>
          <input class="rad-mini" id="radKeyword" type="text" placeholder="名称关键词" maxlength="30">
        </div>

        <!-- 地图视图：按经纬度等距投影自绘，不加载任何外部地图服务 -->
        <div class="rad-map-wrap" id="radMapWrap" style="display:none">
          <div class="rad-map-head" id="radMapHead"></div>
          <div class="rad-map" id="radMap">
            <div class="rad-tiles" id="radTiles"><div class="rad-tiles__inner" id="radTileInner"></div></div>
            <svg id="radSvg" viewBox="0 0 360 420" preserveAspectRatio="none" role="img" aria-label="半径内机构点位分布图">
              <defs><clipPath id="radClip"><rect id="radClipRect" x="0" y="0" width="360" height="420"/></clipPath></defs>
              <g id="radG"></g>
              <g clip-path="url(#radClip)"><g id="radPins"></g></g>
              <g id="radOvl"></g>
            </svg>
            <div class="rad-tools">
              <button type="button" id="radMapZoomIn" title="放大">＋</button>
              <button type="button" id="radMapZoomOut" title="缩小">－</button>
              <button type="button" id="radMapReset" title="复位">⟲</button>
              <button type="button" id="radMapFull" title="全屏">⛶</button>
              <button type="button" id="radMapLayer" title="街道底图开关">▦</button>
            </div>
          </div>
          <div class="rad-legend">
            <span><i style="background:#e05345"></i>机关</span>
            <span><i style="background:#1a5bb8"></i>事业单位</span>
            <span><i style="background:#1f9d57"></i>学校</span>
            <span><i style="background:#d98a12"></i>复合 / 其他</span>
            <span><i style="background:#0f3f86"></i>本行网点（圆心）</span>
          </div>
          <div class="rad-pin-info" id="radPinInfo">点击地图上的彩色图钉查看单位详情；同址或近距离机构以数字聚合显示。</div>
          <div class="rad-map-note" id="radMapNote"></div>
        </div>

        <div class="rad-list" id="radList"></div>
        <div class="rad-pager" id="radPager" style="display:none">
          <button id="radPrev">上一页</button><span id="radPageInfo"></span><button id="radNext">下一页</button>
        </div>
        <div class="rad-note" id="radNote" style="display:none"></div>
      </section>

      <!-- 使用说明 -->
      <section class="card">
        <div class="card__h"><span class="bar"></span><h2>使用说明</h2></div>
        <ul class="notes">
          <li>【网点半径内机构】切换顶部第二个模式，模糊录入本行网点名称并点选具体网点，再录入公里半径，点击「查询半径内机构」后即转为地图界面，可一键切回「清单」视图；数据来源为资料库 DATA 文件夹三份含经纬度整合清单（去重后 4.3 万余家主体，GCJ-02），按地市分片按需加载，页面不携带任何地图 Key 或商业数据凭据。</li>
          <li>地图叠加街道底图：深蓝大图钉标示本行网点（圆心）与半径圈，彩色小图钉按类别区分：机关红、事业单位蓝、学校绿、复合 / 其他橙；同址或近距离机构合并为带数字的聚合点；点击彩色小图钉即弹出「单位主要信息」卡，列示单位名称、机构类别、行政层级、所属区划、直线距离、登记地址、备注与坐标，点关闭按钮、卡片外区域或按 Esc 收起；点数字聚合点先列该位置多家单位，再点其中一家看主要信息。支持放大、缩小、复位、全屏、拖拽平移与街道底图开关。街道底图瓦片经同源 /api/tiles 代理取得（静态版经已授权主站跨域代理），页面不直连任何地图域名、不携带地图 Key；底图不可用时自动退回本地绘制的零依赖点位分布图并如实标注。瓦片按 Web Mercator 切片，与等距投影点位在半径范围内局部近似对齐，仅供位置参考。</li>
          <li>半径查询结果为经纬度直线距离估算，可按机构类别、行政层级与名称关键词筛选并分页，地图与清单同步筛选；仅列示公开登记的机构名称、类别、层级、区划与登记地址。部分主体坐标为登记机关或区县中心级定位，同址机构距离相同，现场应用请以登记地址复核。</li>
          <li>适用对象：福建省内及浙江温州地区的党政机关、事业单位、群团组织。</li>
          <li>距离为基于经纬度的直线距离估算（Haversine 公式），实际步行或驾车距离可能略有差异。</li>
          <li>网点坐标依据福建海峡银行官网网点目录（2026-08-21 版，共 91 家）结合合规公开地图（GCJ-02）位置实测匹配留存。</li>
          <li>本工具仅用于政务合作位置参考，录入信息仅保存在本设备本地。</li>
          <li>本工具分两步：录入机构名称并点击「查询」即反馈最近网点；点击「编制并查看参阅材料」后显示五阶段进度，调取技能全网检索核验资料库、生成证据索引并组装十章 + 两附录的详细材料，完成后弹出全文。</li>
          <li>机构全称、性质、主要职能、内设机构、上级及下属单位与真实坐标，均由 WorkBuddy 会话侧技能全网检索公开渠道补齐、逐字段留痕后内置；页面不携带任何地图 Key、不直连地图域名。第三章按收录状态分别呈现已核验事实或如实标注的通用研判；负责人姓名按最小必要原则不在公开页面列示，可在「现场补录」回填。支持全屏浏览、复制与下载打印；位置与网点信息仅列于附录 A。</li>
          <li>定位共三级：① 已收录机构用全网检索核验的真实坐标；② 未收录机构由后端代理取得高德地图 POI 真实坐标（密钥仅服务端持有；静态托管版经已授权跨域代理调用同一后端）；③ 后端不可用、未配置密钥或地图未匹配时，按行政区划中心近似并逐次如实标注。单位画像经后端 /api/profile 调取（凭据仍仅服务端），命中后在结果卡片与「参阅材料」中逐字段列示，未收录或通道不可用时如实标注、不伪造。如需补齐机构事实，请在 WorkBuddy 会话中发起「全网检索补齐」；如需补齐单位画像，发起「画像补齐 &lt;机构全称&gt;」。</li>
        </ul>
      </section>
    </main>

    <footer class="foot">福建海峡银行最近网点查询工具 · 仅用于政务合作位置参考</footer>
  </div>

  <!-- 单位主要信息弹窗：点击地图图钉/聚合点后弹出 -->
  <div class="pin-modal" id="pinModal" role="dialog" aria-modal="true" aria-label="单位主要信息">
    <div class="pin-card" id="pinCard"></div>
  </div>

  <!-- 分享弹窗 -->
  <div class="mask" id="shareMask">
    <div class="sheet">
      <h3>复制结果分享到群</h3>
      <pre id="shareContent"></pre>
      <div class="sheet__btns">
        <button class="btn btn-primary" id="confirmShare">复制并分享</button>
        <button class="btn btn-ghost" id="closeShare">关闭</button>
      </div>
    </div>
  </div>

  <!-- 参阅材料 · 分阶段编制进度 -->
  <div class="mask mask--prog" id="progMask">
    <div class="sheet sheet--prog" id="progSheet">
      <div class="prog__top">
        <div class="prog__hd">
          <div class="prog__ico">⚙</div>
          <div><h3>正在编制业务合作参阅材料</h3><div class="prog__sub" id="progOrg"></div></div>
        </div>
        <div class="prog__barwrap">
          <div class="prog__bar"><div class="prog__fill" id="progFill"></div></div>
          <div class="prog__pct" id="progPct">0%</div>
        </div>
        <div class="prog__now" id="progNow">准备就绪</div>
      </div>
      <div class="prog__scroll">
        <ol class="prog__stages" id="progStages"></ol>
        <details class="prog__note">
          <summary>编制说明与能力边界</summary>
          <p>五个阶段均为真实执行：读取网点基准、经同源 /api/profile 调取启信慧眼单位画像并读取核验资料库、拼装证据索引与官方核验入口、按十章体例组装、A4 排版渲染。编制阶段仅向同源后端发起一次画像调取（前端零凭据、不直连商业数据域名）；查询阶段的实时定位亦由同源后端代理，页面不携带地图 Key、不上传或缓存查询内容。画像与资料库均由会话侧核对公开来源后逐字段留痕；未收录或通道不可用时如实标注，不以模板内容冒充核验结果。</p>
        </details>
      </div>
      <div class="sheet__btns"><button class="btn btn-ghost" type="button" id="cancelProg">取消编制</button></div>
    </div>
  </div>

  <!-- 参阅材料预览 -->
  <div class="mask" id="briefMask">
    <div class="sheet sheet--doc" id="briefSheet">
      <div class="sheet__hd">
        <h3>业务合作参阅材料（详细版 · 行内参考）</h3>
        <button class="fs-btn" type="button" id="fullscreenBrief">⛶ 全屏</button>
      </div>
      <details class="fill" id="briefFill">
        <summary>✎ 现场补录：负责人 / 上级及下属单位（选填，仅本页有效）</summary>
        <div class="fill__grid">
          <label>主要负责人姓名<input type="text" id="fillLeader" maxlength="30" placeholder="以官方任免文件为准"></label>
          <label>分管财务负责人<input type="text" id="fillFinanceLeader" maxlength="30" placeholder="选填"></label>
          <label>办公室 / 财务对接人<input type="text" id="fillContact" maxlength="30" placeholder="选填"></label>
          <label>其他相关 / 对接人<input type="text" id="fillOtherLeader" maxlength="30" placeholder="选填"></label>
          <label>上级主管单位<input type="text" id="fillSuperior" maxlength="60" placeholder="以机构编制文件为准"></label>
          <label>内设机构核实情况<input type="text" id="fillInnerOrg" maxlength="60" placeholder="选填"></label>
          <label>下属 / 归口管理单位<input type="text" id="fillSubordinate" maxlength="60" placeholder="选填"></label>
        </div>
        <div class="fill__tip">补录内容即时写入第三章，并同步到「复制全文」「下载/打印」；仅保存在当前页面内存，不上传、不持久化，退出页面即失效。未填写项一律标注「待核实」。</div>
        <div class="fill__row"><button class="btn btn-ghost" type="button" id="fillReset">清空补录</button></div>
      </details>
      <div class="doc" id="briefPreview"></div>
      <div class="sheet__btns">
        <button class="btn btn-primary" id="copyBrief">复制全文</button>
        <button class="btn btn-ghost" id="printBrief">下载/打印</button>
        <button class="btn btn-ghost" id="closeBrief">关闭</button>
      </div>
    </div>
  </div>

  <div class="toast" id="toast"></div>

  <script>
    window.REGION_DATA = __REGION_JS__;
    window.PROVINCE_OF_CITY = __PROV_JS__;
    window.BRANCH_DATA = __BRANCH_DATA_JS__;
    window.NEARBY_MANIFEST = __NEARBY_MANIFEST_JS__;
    window.NEARBY_VER = "__NEARBY_VER__";
    // 技能全网检索核验资料库（构建时内联，前端零 Key）
    window.ORG_INTEL = __ORG_INTEL_JS__;
  </script>

  <script>
  (function(){
    "use strict";
    var REGIONS = window.REGION_DATA || {};
    var PROV = window.PROVINCE_OF_CITY || {};
    var BRANCHES = (window.BRANCH_DATA && window.BRANCH_DATA.branches) || [];
    var BACKEND_URL = (function(){ try{ return localStorage.getItem("fjhx_backend_url")||""; }catch(e){ return ""; } })();
    // 前端零 Key：页面不携带任何地图 Key / 商业数据接口凭据，也不直连任何地图域名。
    // 机构事实由会话侧技能全网检索补齐后内联于 window.ORG_INTEL；实时定位仅调同源 /api/geo。
    // 此处清理历史版本遗留的明文缓存。
    try{ localStorage.removeItem("fjhx_map_key"); }catch(e){}
    var lastBackend = null;
    var lastQuery = null;                 // 最近一次查询上下文，供参阅材料编制使用
    var DOC_CSS = __DOC_CSS_JS__;

    function $(id){ return document.getElementById(id); }
    var orgNameInput=$("orgName"), searchBtn=$("searchBtn"), refreshBtn=$("refreshBtn"),
        resultTip=$("resultTip"), resultList=$("resultList"), hero=$("hero"),
        orgBadge=$("orgBadge"), resultActions=$("resultActions"), copyBtn=$("copyBtn"),
        shareMask=$("shareMask"), shareContent=$("shareContent"), confirmShare=$("confirmShare"), closeShare=$("closeShare"),
        advToggle=$("advToggle"), advPanel=$("advPanel"), backendUrlInput=$("backendUrl"),
        saveBackend=$("saveBackend"), backendStatus=$("backendStatus"),
        briefBar=$("briefBar"), briefDesc=$("briefDesc"), briefActions=$("briefActions"),
        viewBrief=$("viewBrief"), downloadBrief=$("downloadBrief"),
        briefMask=$("briefMask"), briefSheet=$("briefSheet"), briefPreview=$("briefPreview"),
        copyBrief=$("copyBrief"), closeBriefBtn=$("closeBrief"),
        fullscreenBrief=$("fullscreenBrief"), fillResetBtn=$("fillReset"),
        progMask=$("progMask"), progOrg=$("progOrg"), progFill=$("progFill"),
        progPct=$("progPct"), progNow=$("progNow"), progStages=$("progStages"),
        cancelProg=$("cancelProg");

    function esc(s){ return String(s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];}); }
    function toast(msg){ var t=$("toast"); t.textContent=msg; t.classList.add("show"); setTimeout(function(){t.classList.remove("show");},1800); }

    function haversineM(la1,lo1,la2,lo2){
      var R=6371000, dLa=(la2-la1)*Math.PI/180, dLo=(lo2-lo1)*Math.PI/180;
      var a=Math.sin(dLa/2)*Math.sin(dLa/2)+Math.cos(la1*Math.PI/180)*Math.cos(la2*Math.PI/180)*Math.sin(dLo/2)*Math.sin(dLo/2);
      return 2*R*Math.asin(Math.sqrt(a));
    }
    // 机构查最近网点：入参为米（haversineM 返回值）。注意不可与半径模式的 fmtDistKm 重名，
    // 否则函数声明提升会让后定义的公里版覆盖本函数，导致米值被当成 km 显示。
    function fmtDist(m){ if(m<1000) return Math.round(m)+" 米"; if(m<100000) return (m/1000).toFixed(1)+" 公里"; return Math.round(m/1000)+" 公里"; }

    // ===== 前端零 Key + 三级定位降级（2026-11-07 B 方案）=====
    // 机构事实（全称、性质、主要职能、内设机构、上级与下属单位）由会话侧技能
    // 全网检索公开渠道补齐后内联于 window.ORG_INTEL，由 intel_pipeline.py 强校验。
    // 定位：① 资料库真实坐标 → ② 同源 /api/geo 后端代理的 POI 真实坐标
    //        → ③ 行政区划中心近似（并如实标注降级原因）。
    // 页面始终零 Key、零直连地图域名；密钥仅由服务端环境变量持有。

    // 由机构名称自动研判类型（用于后端实时查询入参）
    function classifyType(name){
      var t=String(name||"");
      if(/(学校|学院|大学|医院|研究院|研究|所|中心|馆|台|社|院|幼儿园|中学|小学)/.test(t)) return "public";
      if(/(团体|协会|工会|共青团|妇联|工商联|文联|科协|侨联|残联|红十字|联合会|商会|学会|基金会)/.test(t)) return "group";
      return "government";
    }

    // —— 行政区划索引（长名优先）——
    var DISTRICT_INDEX=(function(){
      var idx=[];
      Object.keys(REGIONS).forEach(function(city){
        var prov=PROV[city]||"福建省";
        Object.keys(REGIONS[city]).forEach(function(dist){
          idx.push({name:dist,city:city,province:prov,center:REGIONS[city][dist]});
        });
      });
      idx.sort(function(a,b){return b.name.length-a.name.length;});
      return idx;
    })();
    // 省级机构归位：含省名但未命中市/区县时，归位省会（福建→福州鼓楼；浙江→温州，即本行在浙唯一覆盖地）
    var PROVINCE_CAPITAL={
      "福建省":{city:"福州市",district:"鼓楼区",center:(REGIONS["福州市"]&&REGIONS["福州市"]["鼓楼区"])||[26.0885,119.2920]},
      "浙江省":{city:"温州市",district:"",center:(REGIONS["温州市"]&&REGIONS["温州市"]["鹿城区"])||[27.9830,120.6860]}
    };
    // 公共机构/事业单位常用名称词表：命中即视为政务类机构，按省会（福州）中心近似兜底。
    // 含地市的名称会被上方的地市循环优先命中（如「厦门市教育局」→ 厦门中心），此处仅兜底不含地名的短名。
    var GOV_UNITS=["人民政府","发展和改革委员会","发改委","财政厅","教育局","财政局","公安局","科技局","文旅局","文化和旅游局","卫生健康委","卫生健康委员会","卫健委","人力资源和社会保障","人社厅","人社局","自然资源厅","自然资源局","生态环境厅","生态环境局","交通运输厅","交通运输局","市场监督管理局","市场监管局","公安厅","司法厅","司法局","水利厅","水利局","农业农村厅","农业农村局","民政厅","民政局","住房和城乡建设厅","住建厅","住建局","商务厅","商务局","审计厅","审计局","林业局","海洋与渔业局","广播电视局","体育局","统计局","医疗保障局","医保局","机关事务管理局","机关事务局","粮食和物资储备局","监狱管理局","国资委","地方金融监督管理局","金融监管局","税务局","人民银行","央行","分行","监管局","法院","检察院","省委","组织部","宣传部","委员会","银保监","证监","工会","共青团","妇联","科协","残联","红十字会","文联","社科联","台联","侨联","工商联","贸促会","供销社","档案馆","党校","社会主义学院","研究院","科学院","社科院","农科院","监测中心","服务中心","管理中心","保障中心","医院","卫生院","保健院","学校","小学","中学","学院","大学","幼儿园","人大","政协","工委","信访局","气象局"];

    function parseAddress(text){
      if(!text||!text.trim()) return null;
      var t=text.trim(), matched=null;
      for(var i=0;i<DISTRICT_INDEX.length;i++){ if(t.indexOf(DISTRICT_INDEX[i].name)!==-1){ matched=DISTRICT_INDEX[i]; break; } }
      if(matched){
        return {province:matched.province,city:matched.city,district:matched.name,
          center:{lat:matched.center[0],lng:matched.center[1]}};
      }
      var cities=Object.keys(REGIONS).sort(function(a,b){return b.length-a.length;}), cityHit=null;
      for(var c=0;c<cities.length;c++){ if(t.indexOf(cities[c])!==-1){ cityHit=cities[c]; break; } }
      if(cityHit){
        var ds=REGIONS[cityHit], ks=Object.keys(ds), la=0, lo=0;
        ks.forEach(function(k){ la+=ds[k][0]; lo+=ds[k][1]; });
        return {province:PROV[cityHit]||"福建省",city:cityHit,district:"",
          center:{lat:la/ks.length,lng:lo/ks.length},precision:"city"};
      }
      // —— 省级机构层（新增）：含省名即归位省会，覆盖"人民银行福建省分行""XX省XX厅"等省级机构 ——
      var provinces=Object.keys(PROVINCE_CAPITAL);
      for(var p=0;p<provinces.length;p++){
        if(t.indexOf(provinces[p])!==-1){
          var cap=PROVINCE_CAPITAL[provinces[p]];
          return {province:provinces[p],city:cap.city,district:cap.district||"",
            center:{lat:cap.center[0],lng:cap.center[1]},precision:"province"};
        }
      }
      for(var g=0;g<GOV_UNITS.length;g++){
        if(t.indexOf(GOV_UNITS[g])!==-1){
          var fc=REGIONS["福州市"]["鼓楼区"];
          return {province:"福建省",city:"福州市",district:"鼓楼区",center:{lat:fc[0],lng:fc[1]},precision:"govhint"};
        }
      }
      return null;
    }

    function computeItems(base){
      var items=[];
      for(var i=0;i<BRANCHES.length;i++){
        var b=BRANCHES[i]; if(!b||!b.lat||!b.lng) continue;
        items.push({branch:b,dist:haversineM(base.lat,base.lng,b.lat,b.lng)});
      }
      items.sort(function(a,b){return a.dist-b.dist;});
      return items;
    }

    __BRIEF_JS__

    function renderResult(items, baseLabel, approxNote){
      resultActions.style.display="flex";
      resultTip.className="tip";
      if(!items.length){
        resultTip.className="tip err";
        resultTip.textContent="未匹配到福建海峡银行网点，请更换机构名称后重试。";
        hero.style.display="none";
        resultList.innerHTML='<div class="empty"><span class="ic">📍</span>暂无可匹配网点</div>';
        return;
      }
      var top=items.slice(0,8);
      resultTip.textContent="已匹配 "+items.length+" 家网点，以下为距离最近的 "+top.length+" 家（直线距离测算"+(approxNote||"")+"）：";
      var first=top[0], b=first.branch;
      hero.style.display="block";
      hero.innerHTML=
        '<div class="hero__inner">'+
          '<div class="hero__tag">🏆 距离最近</div>'+
          '<div class="hero__name">'+esc(b.name)+'</div>'+
          '<div class="hero__meta">'+esc(b.type||"二级支行")+' · '+esc(b.address||"地址未收录")+'</div>'+
          '<div class="hero__dist"><span class="n">'+fmtDist(first.dist)+'</span><span class="u">直线距离</span></div>'+
          (b.phone?'<a class="hero__phone" href="tel:'+esc(b.phone)+'">☎ '+esc(b.phone)+'</a>':'')+
        '</div>';
      resultList.innerHTML="";
      top.slice(1).forEach(function(item,idx){
        var bb=item.branch, node=document.createElement("div"); node.className="item";
        node.innerHTML=
          '<div class="item__rank">'+(idx+2)+'</div>'+
          '<div class="item__main">'+
            '<div class="item__name">'+esc(bb.name)+'</div>'+
            '<div class="item__type">'+esc(bb.type||"二级支行")+'</div>'+
            '<div class="item__addr">'+esc(bb.address||"地址未收录")+'</div>'+
          '</div>'+
          '<div class="item__dist"><div class="d">'+fmtDist(item.dist)+'</div>'+(bb.phone?'<div class="p">☎ '+esc(bb.phone)+'</div>':'')+'</div>';
        resultList.appendChild(node);
      });
      renderBriefBar();
    }

    // ===== 三级定位降级（2026-11-07 · B 方案：后端代理实时真实定位）=====
    // ① 技能全网检索核验资料库真实坐标（构建时内联，零网络请求）
    // ② 同源后端 /api/geo 代理的高德地图 POI 真实坐标（Key 仅服务端持有，前端零 Key）
    // ③ 行政区划中心近似（后端不可用 / 未配置 / 未命中时，如实标注）
    // 页面始终不携带任何地图 Key、不直连任何地图域名；定位来源逐次如实标注。
    // 跨域代理 URL（构建时注入）：非空时查询阶段经该 URL 调主链接后端 /api/geo 取真实坐标；
    // 留空则使用同源相对路径（主链接Web渲染）。两种方式均不向前端暴露任何地图 Key。
    var GEO_PROXY = "__GEO_PROXY__";
    // 单位画像跨域代理 URL（构建时注入）：非空时「编制参阅材料」与结果内联卡片经该 URL 调主链接后端
    // /api/profile 取启信慧眼单位画像；留空则使用同源相对路径（主链接 Web 渲染，后端直供）。
    // 两种方式均不向前端暴露任何 Key（启信慧眼 Key 仅服务端持有），亦不直连商业数据域名。
    var PROFILE_PROXY = "__PROFILE_PROXY__";
    // 机构名称联想跨域代理 URL（构建时注入）：非空时静态版经该 URL 调主链接后端 /api/suggest
    // 取高德实时相近机构名；留空则使用同源相对路径（主链接 Web 渲染）。两者均前端零 Key。
    var SUGGEST_PROXY = "__SUGGEST_PROXY__";
    // 街道底图瓦片代理（构建时注入）：主站留空使用同源 /api/tiles?；静态版注入主站完整 URL。
    // 页面只向该 URL 请求瓦片图片，不直连任何地图域名、不携带任何 Key。
    var TILE_BASE = "__TILE_PROXY__" || "/api/tiles?";
    // 由跨域代理 URL 推导「完整版（实时定位）」主页，用于实时定位通道不可用时的自愈跳转。
    // 主链接（同源）GEO_PROXY 为空 → BACKEND_HOME 为空 → 不渲染自愈入口。
    var BACKEND_HOME = (function(){
      if(!GEO_PROXY) return "";
      var u=GEO_PROXY.replace("/api/geo","/");   // ...host/?sharecode=XXX&name=
      var i=u.indexOf("&name=");
      return i>0 ? u.slice(0,i) : u;             // ...host/?sharecode=XXX
    })();
    var geoToken = 0;

    // 三级定位第三级（离线近似）：仅在「实时高德地图」通道不可用（后端鉴权/网络）
    // 或「公开地图未匹配到该机构」时才触发。如实标注原因，不再使用「资料库未收录」
    // 等易被误解为「仅支持预置库」的措辞——本工具对任意机构名均优先调用高德实时定位。
    function runLocalSearch(geoNote){
      lastBackend=null;
      orgBadge.className="orgbadge badge-warn";
      orgBadge.style.display="block";
      var name=orgNameInput.value.trim();
      var base=parseAddress(name);
      var unrecognized=false;
      if(!base){
        // 地名/机构关键词均无法识别时，回退到福建省会（福州）中心近似，确保始终给出最近网点参考
        var fc=REGIONS["福州市"]["鼓楼区"];
        base={province:"福建省",city:"福州市",district:"鼓楼区",center:{lat:fc[0],lng:fc[1]},precision:"unknown"};
        unrecognized=true;
      }
      var items=computeItems(base.center);
      var approx=(unrecognized?"按福建省会（福州）中心近似测算":"按行政区划中心近似测算");
      var why=unrecognized
        ? "未能从机构名称识别到具体区县"
        : (geoNote||"实时定位通道暂不可用");
      var head="⚠ 实时高德地图定位未就绪（"+esc(why)+"），已"+approx;
      var tail=BACKEND_HOME
        ? ('；<a class="badge-link" href="'+esc(BACKEND_HOME)+'&name='+encodeURIComponent(name)+'" target="_blank" rel="noopener">打开完整版（实时定位）→</a>')
        : "；如需以已核验机构事实编制参阅材料，请在 WorkBuddy 会话中发起「全网检索补齐」。";
      orgBadge.innerHTML=head+tail;
      lastQuery={name:name,mode:"approx",region:base,geo:null,intel:null,items:items,
        geoNote:why};
      renderResult(items, "该机构位置（近似测算）", "（"+approx+"）");
      showProfile(name);
    }

    function geoReason(j){
      if(!j) return "后端未返回有效定位结果";
      if(j.reason==="no-key") return "服务端未配置定位密钥";
      if(j.reason==="bad-key") return "地图服务密钥无效或平台类型不匹配";
      if(j.reason==="quota-exceeded") return "地图服务触发限流或日配额上限";
      if(j.reason==="no-poi") return "公开地图未匹配到该机构真实坐标";
      if(j.reason==="geo-error") return "实时定位服务暂不可用";
      return String(j.message||"实时定位未命中");
    }

    // —— ② 同源后端代理实时真实定位（Key 仅服务端持有）——
    function doGeoSearch(name){
      var my=++geoToken;
      resultTip.className="tip";
      resultTip.textContent="正在通过同源后端调取「"+name+"」的真实坐标…";
      hero.style.display="none"; resultList.innerHTML=""; resultActions.style.display="none";
      orgBadge.style.display="block";
      orgBadge.innerHTML="◌ 正在调取实时真实坐标（同源后端代理 · 前端零 Key）…";
      var ctrl=(typeof AbortController!=="undefined")?new AbortController():null;
      var timer=setTimeout(function(){ try{ if(ctrl) ctrl.abort(); }catch(e){} },4500);
      var opt=ctrl?{signal:ctrl.signal,headers:{"Accept":"application/json"}}:{headers:{"Accept":"application/json"}};
      var geoUrl = GEO_PROXY ? (GEO_PROXY + encodeURIComponent(name)) : ("api/geo?name="+encodeURIComponent(name));
      fetch(geoUrl,opt)
        .then(function(r){ if(!r.ok) throw new Error("HTTP-"+r.status); return r.json(); })
        .then(function(j){
          clearTimeout(timer);
          if(my!==geoToken) return;
          if(!j||!j.found||!j.geo){ runLocalSearch(geoReason(j)); return; }
          applyGeoResult(name,j);
        })
        .catch(function(e){
          clearTimeout(timer);
          if(my!==geoToken) return;
          runLocalSearch("后端/网络不可达（"+String((e&&e.message)||"请求失败")+"）");
        });
    }

    function applyGeoResult(name,j){
      lastBackend=null;
      var g=j.geo;
      var hint={province:g.province||"福建省",city:g.city||"",district:g.district||"",
                center:{lat:g.lat,lng:g.lng}};
      var items=computeItems({lat:g.lat,lng:g.lng});
      orgBadge.style.display="block";
      orgBadge.innerHTML="✓ 已取得实时真实坐标：<b>"+esc(g.title||name)+"</b>"+
        (g.address?" · "+esc(g.address):"")+
        " · "+esc(j.provider||"高德地图开放平台")+"（GCJ-02，" +esc(j.verifiedAt||"")+"）";
      lastQuery={name:name,mode:"geo",region:hint,
        geo:{title:g.title||name,address:g.address||"",lat:g.lat,lng:g.lng,
             source:g.source,provider:j.provider,verifiedAt:j.verifiedAt},
        intel:null,items:items,geoNote:""};
      renderResult(items, "该机构实时真实坐标（后端代理定位）", "");
      showProfile(name);
    }

    // 单位画像内联卡片：经跨域代理 PROFILE_PROXY（静态托管）或同源 /api/profile（主链接）调取启信慧眼画像，
    // 前端零 Key、不直连商业数据域名；未取得则不展示卡片。
    var profToken = 0;
    function showProfile(name){
      var box=$("profileBox");
      if(!box) return;
      if(!name){ box.style.display="none"; return; }
      var my=++profToken;
      box.style.display="block";
      box.innerHTML='<div class="pb__head">◌ 正在调取启信慧眼单位画像…</div>';
      var url=PROFILE_PROXY ? (PROFILE_PROXY+encodeURIComponent(name)) : ("api/profile?name="+encodeURIComponent(name));
      fetch(url,{cache:"no-store",headers:{"Accept":"application/json"}})
        .then(function(r){ return (r && r.ok) ? r.json() : null; })
        .then(function(j){
          if(my!==profToken) return;
          if(!j || !j.found || !j.profile){ box.style.display="none"; return; }
          var p=j.profile, flds=p.fields||{}, labels=p.fieldLabels||{}, rows="";
          Object.keys(labels).forEach(function(k){
            var f=flds[k];
            if(f && f.s==="verified" && f.v){
              rows+='<div class="pb__row"><span class="pb__k">'+esc(labels[k])+'</span><span class="pb__v">'+esc(String(f.v))+'</span></div>';
            }
          });
          box.innerHTML='<div class="pb__head">🏛 启信慧眼单位画像（'+esc(j.provider||"")+(j.verifiedAt?(" · "+esc(j.verifiedAt)+" 核验"):"")+'）</div>'+
            (rows?('<div class="pb__rows">'+rows+'</div>'):'<div class="pb__row"><span class="pb__v">该单位已收录，但未公示可核验字段</span></div>')+
            '<div class="pb__foot">完整字段与证据索引见「编制并查看参阅材料」。</div>';
        })
        .catch(function(){ if(my===profToken) box.style.display="none"; });
    }

    // —— ① 资料库命中：技能全网检索核验的真实坐标测算（零网络请求）——
    function doIntelSearch(name){
      lastBackend=null;
      var o=lookupIntel(name);
      if(!o){ doGeoSearch(name); return; }
      var dv=String((o.fields.district&&o.fields.district.v)||"").split(/\s*\/\s*/);
      var hint={province:dv[0]||"福建省",city:dv[1]||"",district:dv[2]||"",
                center:{lat:o.geo.lat,lng:o.geo.lng}};
      var items=computeItems({lat:o.geo.lat,lng:o.geo.lng});
      var cov=intelCoverage(o);
      orgBadge.style.display="block";
      orgBadge.innerHTML="✓ 已命中技能全网检索核验资料库：<b>"+esc(o.name)+"</b> · "+
        esc(intelFieldText(o.fields.orgType))+" · "+esc(intelFieldText(o.fields.address))+
        "（"+esc(o.verifiedAt)+" 核验，"+cov.sources+" 条证据）";
      lastQuery={name:name,mode:"intel",region:hint,
        geo:{title:o.name,address:intelFieldText(o.fields.address),lat:o.geo.lat,lng:o.geo.lng},
        intel:o,items:items,geoNote:""};
      renderResult(items, "该机构真实位置（技能全网检索核验坐标）", "");
      showProfile(name);
    }

    searchBtn.addEventListener("click",function(){
      var name=orgNameInput.value.trim();
      if(!name){ toast("请输入机构名称"); orgNameInput.focus(); return; }
      if(BACKEND_URL){ doBackendSearch(name); return; }
      doIntelSearch(name);
    });
    // ===== 机构名称实时联想（2026-11-08）=====
    // 双来源：① 构建时内联的已核验机构名/别名（零网络，限流或后端不可达时仍可用）；
    //        ② 后端 /api/suggest 经高德 place/text 取省内真实相近机构名（Key 仅服务端持有）。
    // 静态托管版经 SUGGEST_PROXY 跨域代理，主链接走同源相对路径；前端始终零 Key、不直连地图域名。
    var LOCAL_SUGGEST = __LOCAL_SUGGEST_JS__;
    var sugList=$("sugList"), sugWrap=orgNameInput.parentNode;
    var sugItems=[], sugIndex=-1, sugToken=0, sugTimer=null, sugCtrl=null;

    function hideSug(){
      if(sugTimer){ clearTimeout(sugTimer); sugTimer=null; }
      sugItems=[]; sugIndex=-1;
      sugList.classList.remove("show"); sugList.innerHTML="";
    }
    function localSuggest(q){
      var qc=String(q||"").replace(/\s+/g,""), out=[];
      if(qc.length<2) return out;
      LOCAL_SUGGEST.forEach(function(o){
        var hit=o.n.indexOf(qc)>=0, a=o.a||[];
        for(var i=0;!hit&&i<a.length;i++){ if(a[i].indexOf(qc)>=0) hit=true; }
        if(hit) out.push({name:o.n,address:"",district:"",local:true});
      });
      return out;
    }
    function mergeSug(remote){
      var seen={}, out=[];
      localSuggest(orgNameInput.value.trim()).forEach(function(x){
        if(!seen[x.name]){ seen[x.name]=1; out.push(x); }
      });
      (remote||[]).forEach(function(x){
        if(x && x.name && !seen[x.name]){ seen[x.name]=1; out.push(x); }
      });
      return out.slice(0,8);
    }
    function renderSug(list, note){
      sugItems=list||[]; sugIndex=-1;
      if(!sugItems.length){ sugList.classList.remove("show"); sugList.innerHTML=""; return; }
      var h='<div class="sug-hint">'+esc(note||"相近机构名称 · 点击直接查询")+'</div>';
      sugItems.forEach(function(x,i){
        var sub=x.local ? "本行已核验资料库 · 规范机构全称"
                        : ((x.district?esc(x.district)+" · ":"")+esc(x.address||"公开地图相近机构"));
        h+='<div class="sug-item" data-i="'+i+'"><div class="sug-item__n">'+esc(x.name)+
           (x.local?' <span class="sug-item__tag">已核验</span>':'')+'</div>'+
           '<div class="sug-item__d">'+sub+'</div></div>';
      });
      sugList.innerHTML=h;
      sugList.classList.add("show");
    }
    function moveSug(d){
      if(!sugItems.length) return;
      sugIndex=(sugIndex+d+sugItems.length)%sugItems.length;
      var nodes=sugList.querySelectorAll(".sug-item");
      for(var i=0;i<nodes.length;i++) nodes[i].classList.toggle("active",i===sugIndex);
      if(nodes[sugIndex] && nodes[sugIndex].scrollIntoView) nodes[sugIndex].scrollIntoView({block:"nearest"});
    }
    function chooseSug(i){
      var x=sugItems[i]; if(!x) return;
      sugToken++;
      orgNameInput.value=x.name;
      hideSug();
      searchBtn.click();          // 选中即回填并直接查询最近网点
    }
    function runSug(){
      var q=orgNameInput.value.trim();
      if(q.length<2){ hideSug(); return; }
      var my=++sugToken;
      renderSug(localSuggest(q), "本行已核验资料库 · 正在检索公开地图…");  // 本地候选即时可见
      var url=SUGGEST_PROXY ? (SUGGEST_PROXY+encodeURIComponent(q))
                            : ("api/suggest?name="+encodeURIComponent(q));
      if(sugCtrl){ try{ sugCtrl.abort(); }catch(e){} }
      sugCtrl=(typeof AbortController!=="undefined")?new AbortController():null;
      var opt=sugCtrl?{signal:sugCtrl.signal,headers:{"Accept":"application/json"}}
                     :{headers:{"Accept":"application/json"}};
      fetch(url,opt)
        .then(function(r){ return (r && r.ok) ? r.json() : null; })
        .then(function(j){
          if(my!==sugToken) return;
          var remote=(j && j.found && j.suggestions) ? j.suggestions : [];
          renderSug(mergeSug(remote),
            remote.length ? "相近机构名称 · 高德地图实时检索" : "本行已核验资料库（实时检索暂不可用）");
        })
        .catch(function(){ /* 网络异常/取消：保留已展示的本地候选，不弹错、不伪造 */ });
    }
    orgNameInput.addEventListener("input",function(){
      if(sugTimer) clearTimeout(sugTimer);
      sugToken++;                                  // 作废上一条在途请求
      sugTimer=setTimeout(runSug,320);            // 防抖，避免逐字触发上游限流
    });
    orgNameInput.addEventListener("keydown",function(e){
      if(e.key==="ArrowDown"){ if(sugItems.length){ e.preventDefault(); moveSug(1); } return; }
      if(e.key==="ArrowUp"){ if(sugItems.length){ e.preventDefault(); moveSug(-1); } return; }
      if(e.key==="Escape"){ hideSug(); return; }
      if(e.key==="Enter"){
        e.preventDefault();
        if(sugItems.length && sugIndex>=0){ chooseSug(sugIndex); return; }
        sugToken++; hideSug(); searchBtn.click();
      }
    });
    sugList.addEventListener("mousedown",function(e){
      var node=e.target, item=null;
      while(node && node!==sugList){
        if(node.classList && node.classList.contains("sug-item")){ item=node; break; }
        node=node.parentNode;
      }
      if(item){ e.preventDefault(); chooseSug(Number(item.getAttribute("data-i"))); }
    });
    document.addEventListener("click",function(e){
      if(sugWrap && !sugWrap.contains(e.target)) hideSug();
    });
    searchBtn.addEventListener("click",function(){ sugToken++; hideSug(); });
    refreshBtn.addEventListener("click",function(){ sugToken++; hideSug(); });

    function doBackendSearch(name){
      resultTip.className="tip"; resultTip.textContent="正在实时查询「"+name+"」的机构信息…";
      hero.style.display="none"; resultList.innerHTML=""; resultActions.style.display="none";
      var sep=BACKEND_URL.indexOf("?")!==-1?"&":"?";
      var url=BACKEND_URL.replace(/\/+$/,"")+"/api/org"+sep+"name="+encodeURIComponent(name)+"&type="+classifyType(name);
      fetch(url,{headers:{"Accept":"application/json"}})
        .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});})
        .then(function(res){
          var j=res.j;
          if(!res.ok||!j||j.found===false){
            resultTip.className="tip err";
            resultTip.textContent=((j&&j.error)?j.error:"实时查询未匹配到该机构")+"；已切换为本地行政区划估算。";
            runLocalSearch(); return;
          }
          renderFromBackend(j);
        })
        .catch(function(e){
          resultTip.className="tip err";
          resultTip.textContent="实时查询请求失败（后端不可达）："+e.message+"；已切换为本地行政区划估算。";
          runLocalSearch();
        });
    }
    function renderFromBackend(j){
      var o=j.org||{}; lastBackend=j;
      if(o.fullName||o.creditCode){
        orgBadge.style.display="block";
        orgBadge.innerHTML="实时核验：<b>"+esc(o.fullName||"")+(o.creditCode?" · "+esc(o.creditCode):"")+"</b>"+(o.address?" · 📍"+esc(o.address):"");
      } else { orgBadge.style.display="none"; }
      var items=(j.nearest||[]).map(function(x){return {branch:{name:x.name,type:x.type,address:x.address,phone:x.phone},distText:x.distText};});
      lastQuery={name:orgNameInput.value.trim()||(o.fullName||"机构"),mode:"backend",
        region:parseAddress(orgNameInput.value.trim()),org:o,items:items};
      renderResult(items,"「"+(o.fullName||"")+"」位置");
    }

    // —— 分享文本 ——
    function buildShareLocal(){
      var name=orgNameInput.value.trim()||"（未填写）";
      var base=parseAddress(name); if(!base) return "【福建海峡银行最近网点查询】\n未识别到行政区划，无法匹配网点。";
      var items=computeItems(base.center);
      var text="【福建海峡银行最近网点查询结果】\n查询机构："+name+"\n以下为距离最近的福建海峡银行网点（直线距离估算）：\n";
      if(!items.length) text+="未匹配到网点。\n";
      else items.slice(0,8).forEach(function(it,i){ text+=(i+1)+". "+it.branch.name+"（"+(it.branch.type||"二级支行")+"，距离："+fmtDist(it.dist)+"）："+(it.branch.address||"地址未收录")+"；电话："+(it.branch.phone||"—")+"\n"; });
      text+="——数据来源：福建海峡银行网点公开信息（2026-08-21 版，共 "+BRANCHES.length+" 家），距离仅供参考。";
      return text;
    }
    function buildShareFromBackend(j){
      var o=j.org||{};
      var text="【福建海峡银行最近网点查询结果】（实时核验）\n";
      text+="机构全称："+(o.fullName||"—")+(o.creditCode?"；\n统一社会信用代码："+o.creditCode:"")+"\n";
      text+="以下为距离最近的福建海峡银行网点（直线距离估算）：\n";
      (j.nearest||[]).slice(0,8).forEach(function(x,i){ text+=(i+1)+". "+x.name+"（"+x.type+"，距离："+x.distText+"）："+x.address+"；电话："+x.phone+"\n"; });
      text+="——数据来源：可选后端扩展点 + 福建海峡银行网点公开信息（共 "+(j.branchCount||"")+" 家），距离仅供参考。";
      return text;
    }
    function buildShareIntel(q){
      var o=q.intel, text="【福建海峡银行最近网点查询结果】\n";
      text+="查询机构："+q.name+"（资料库规范名称："+o.name+"）\n";
      text+="机构坐标："+o.geo.lat+", "+o.geo.lng+"（技能全网检索核验，"+o.verifiedAt+"）\n";
      text+="以下为距离最近的福建海峡银行网点（直线距离估算）：\n";
      (q.items||[]).slice(0,8).forEach(function(it,i){
        var b=it.branch||{};
        text+=(i+1)+". "+b.name+"（"+(b.type||"二级支行")+"，距离："+fmtDist(it.dist)+"）："+(b.address||"地址未收录")+"；电话："+(b.phone||"—")+"\n";
      });
      text+="——数据来源：福建海峡银行官网公开网点目录（2026-08-21 版，共 "+BRANCHES.length+" 家）与技能全网检索核验资料库；距离仅供参考。";
      return text;
    }
    copyBtn.addEventListener("click",function(){
      var text = lastBackend ? buildShareFromBackend(lastBackend) :
        ((lastQuery && lastQuery.intel) ? buildShareIntel(lastQuery) : buildShareLocal());
      shareContent.textContent=text; shareMask.classList.add("show");
    });
    function fallbackCopy(t){ var ta=document.createElement("textarea"); ta.value=t; ta.style.position="fixed"; ta.style.opacity="0"; document.body.appendChild(ta); ta.select(); try{document.execCommand("copy");}catch(e){} document.body.removeChild(ta); }
    confirmShare.addEventListener("click",function(){
      var t=shareContent.textContent;
      if(navigator.clipboard&&navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(closeShare,function(){fallbackCopy(t);closeShare();});
      else { fallbackCopy(t); closeShare(); }
    });
    closeShare.addEventListener("click",closeShare);
    shareMask.addEventListener("click",function(e){ if(e.target===shareMask) closeShare(); });
    function closeShare(){ shareMask.classList.remove("show"); shareContent.textContent=""; }

    // —— 刷新：清空输入与结果，便于再次录入 ——
    refreshBtn.addEventListener("click",function(){
      geoToken++;                       // 作废未返回的实时定位请求，避免覆盖新查询
      orgNameInput.value="";
      orgBadge.style.display="none";
      hero.style.display="none";
      resultList.innerHTML="";
      resultActions.style.display="none";
      lastQuery=null;
      briefBar.style.display="none"; briefActions.style.display="none";
      cancelBriefPipeline(); exitBriefFs(); resetBriefFields(); clearFillInputs();
      briefMask.classList.remove("show"); briefPreview.innerHTML="";
      resultTip.className="tip";
      resultTip.textContent="请输入机构名称后点击「查询」。";
      orgNameInput.focus();
      toast("已清空，可重新录入");
    });

    // —— 全文全屏浏览：优先浏览器全屏 API，微信内置浏览器不支持时回退为视口铺满 ——
    function isBriefFs(){ return briefMask.classList.contains("fs-pad"); }
    function syncFsBtn(){ if(fullscreenBrief) fullscreenBrief.textContent=isBriefFs()?"退出全屏":"⛶ 全屏"; }
    function enterBriefFs(){
      briefMask.classList.add("fs-pad"); briefSheet.classList.add("fs");
      document.body.classList.add("fs-lock"); syncFsBtn();
      try{
        var el=document.documentElement;
        if(el.requestFullscreen){ var pr=el.requestFullscreen(); if(pr&&pr.catch) pr.catch(function(){}); }
        else if(el.webkitRequestFullscreen){ el.webkitRequestFullscreen(); }
      }catch(e){}
    }
    function exitBriefFs(){
      briefMask.classList.remove("fs-pad"); briefSheet.classList.remove("fs");
      document.body.classList.remove("fs-lock"); syncFsBtn();
      try{
        if(document.fullscreenElement||document.webkitFullscreenElement){
          var fn=document.exitFullscreen||document.webkitExitFullscreen;
          if(fn) fn.call(document);
        }
      }catch(e){}
    }
    function rerenderBrief(){
      if(!lastQuery) return;
      var top=briefPreview.scrollTop;
      briefPreview.innerHTML=briefFragment(lastQuery);
      briefPreview.scrollTop=top;
    }

    // —— 现场补录：负责人 / 上级及下属单位，仅内存，不持久化 ——
    var FILL_MAP={fillLeader:"leader",fillFinanceLeader:"financeLeader",fillContact:"contact",
                  fillOtherLeader:"otherLeader",fillSuperior:"superior",
                  fillInnerOrg:"innerOrg",fillSubordinate:"subordinate"};
    function clearFillInputs(){
      Object.keys(FILL_MAP).forEach(function(id){ var el=$(id); if(el) el.value=""; });
    }
    Object.keys(FILL_MAP).forEach(function(id){
      var el=$(id); if(!el) return;
      el.addEventListener("input",function(){
        setBriefField(FILL_MAP[id],el.value);
        rerenderBrief();
      });
    });
    if(fillResetBtn) fillResetBtn.addEventListener("click",function(){
      resetBriefFields(); clearFillInputs(); rerenderBrief(); toast("补录内容已清空");
    });

    // ===== 两阶段编制流水线（2026-11-07 · 前端零 Key 版）=====
    // 查询阶段只反馈最近网点（其间可由同源后端代理完成一次实时定位）；
    // 点击参阅材料按钮后启动本流水线，五阶段均为页面内真实计算：
    // 基准与资料库匹配 → 证据索引拼装 → 十章组装 → 排版渲染，
    // 编制阶段仅向后端 /api/profile 调取单位画像（静态版经跨域代理，前端零凭据、不直连商业数据域名）；
    // 通道不可用或未收录时如实降级，不伪装为已核验。其余章节为本地资料库与模板组装。
    function nowStr(){
      var d=new Date(), p=function(n){return (n<10?"0":"")+n;};
      return d.getFullYear()+"-"+p(d.getMonth()+1)+"-"+p(d.getDate())+" "+p(d.getHours())+":"+p(d.getMinutes());
    }
    var BRIEF_STAGES=[
      {t:"读取网点基准与机构类别知识库", d:"官网公开网点目录 · 机构画像知识库", pct:14},
      {t:"调取启信慧眼单位画像与核验资料库", d:"后端 /api/profile · 机构登记画像 · 逐字段核验状态", pct:40},
      {t:"生成证据索引与官方核验直达入口", d:"来源链接 · 口径差异 · 时点复核入口", pct:58},
      {t:"按十章体例组装参阅材料", d:"已核验事实 · 场景 · 方向 · 合规边界", pct:82},
      {t:"A4 排版渲染与密级标识校验", d:"行内参考 请勿外传", pct:100}
    ];
    var briefRunToken=0;
    function renderProgStages(){
      if(!progStages) return;
      progStages.innerHTML=BRIEF_STAGES.map(function(x,i){
        return '<li><span class="st">'+String(i+1)+'</span><span>'+esc(x.t)+
          '<span class="sd">'+esc(x.d)+'</span></span></li>';
      }).join("");
    }
    function setProg(idx, pct, note){
      if(progFill) progFill.style.width=pct+"%";
      if(progPct) progPct.textContent=pct+"%";
      if(progNow) progNow.textContent=note||"";
      if(!progStages) return;
      var lis=progStages.getElementsByTagName("li");
      for(var i=0;i<lis.length;i++){
        lis[i].className = i<idx ? "done" : (i===idx ? "run" : "");
        var st=lis[i].getElementsByClassName("st")[0];
        if(st) st.textContent = i<idx ? "✓" : String(i+1);
      }
    }
    function sleepProg(ms){ return new Promise(function(r){ setTimeout(r,ms); }); }
    function cancelBriefPipeline(){
      briefRunToken++;
      if(progMask) progMask.classList.remove("show");
      document.body.classList.remove("fs-lock");
    }
    function runBriefPipeline(mode){
      var q=lastQuery;
      if(!q){ toast("请先查询机构"); return; }
      var token=++briefRunToken;
      function alive(){ return token===briefRunToken; }
      function stageStart(i,note){
        if(!alive()) return;
        setProg(i, i===0?0:BRIEF_STAGES[i-1].pct, note||("正在执行："+BRIEF_STAGES[i].t+"…"));
      }
      function stageDone(i){
        if(!alive()) return;
        setProg(i+1, BRIEF_STAGES[i].pct, BRIEF_STAGES[i].t+"：完成");
      }
      exitBriefFs();
      if(briefMask) briefMask.classList.remove("show");
      renderProgStages(); setProg(0,0,"正在启动编制流程…");
      if(progOrg) progOrg.textContent="查询机构："+(q.name||"机构");
      if(progMask) progMask.classList.add("show");
      document.body.classList.add("fs-lock");

      Promise.resolve()
      // ① 本地基准
      .then(function(){ stageStart(0); return sleepProg(230); })
      .then(function(){ if(!alive()) return; stageDone(0); return sleepProg(150); })
      // ② 编制阶段真实调取启信慧眼单位画像（后端 /api/profile，静态版经跨域代理）+ 读取会话侧核验资料库
      .then(function(){
        if(!alive()) return null;
        stageStart(1,"正在经后端 /api/profile 调取启信慧眼单位画像，并读取技能全网检索核验资料库…");
        q.intel = q.intel || lookupIntel(q.name) || null;
        var cov = q.intel ? intelCoverage(q.intel) : null;
        var pUrl = PROFILE_PROXY ? (PROFILE_PROXY+encodeURIComponent(q.name||""))
                                 : ("api/profile?name="+encodeURIComponent(q.name||""));
        var req = (typeof fetch==="function")
          ? fetch(pUrl, {cache:"no-store"})
              .then(function(r){ return r.ok ? r.json() : null; })
              .catch(function(){ return null; })
          : Promise.resolve(null);
        return req.then(function(j){
          if(!alive()) return null;
          q.profile = (j && j.found && j.profile) ? j : null;
          q.profileReason = j ? (j.reason||"") : "offline";
          var p = q.profile && q.profile.profile;
          var msg = p
            ? ("已调取启信慧眼画像："+p.name+" · "+Object.keys(p.fields||{}).length+" 类字段 / "+(p.sources||[]).length+" 项接口来源（"+(q.profile.verifiedAt||"—")+" 核验）"+(cov?("；资料库另命中 "+q.intel.name+" "+cov.ok+" 项字段"):""))
            : ("画像调取未命中："+profileReasonText(q)+"；第三章按既有口径如实标注，不伪造画像");
          setProg(2, BRIEF_STAGES[1].pct, msg);
          return sleepProg(420);
        });
      })
      // ③ 证据索引与官方核验直达入口（真实拼装）
      .then(function(){
        if(!alive()) return null;
        setProg(2, BRIEF_STAGES[1].pct, "正在拼装证据索引、口径差异说明与官方核验直达入口…");
        return sleepProg(260);
      })
      .then(function(){ if(!alive()) return; stageDone(2); return sleepProg(140); })
      // ④ 十章组装（真实生成并校验密级标识）
      .then(function(){
        if(!alive()) return null;
        stageStart(3,"正在按十章体例组装已核验事实、单位治理与组织画像、业务研判与合规边界…");
        return sleepProg(260);
      })
      .then(function(){
        if(!alive()) return null;
        var frag=briefFragment(q);
        if(!frag || frag.indexOf("行内参考 请勿外传")<0) throw new Error("材料组装校验未通过");
        q.__frag=frag;
        stageDone(3); return sleepProg(150);
      })
      // ⑤ 排版渲染
      .then(function(){
        if(!alive()) return null;
        stageStart(4,"正在进行 A4 排版渲染与密级标识校验…");
        return sleepProg(220);
      })
      .then(function(){ if(!alive()) return; stageDone(4); return sleepProg(240); })
      .then(function(){
        if(!alive()) return;
        document.body.classList.remove("fs-lock");
        if(progMask) progMask.classList.remove("show");
        var pill=$("briefPill"); if(pill) pill.textContent="已生成";
        if(mode==="download"){ downloadBriefFile(); toast("参阅材料已编制完成并下载"); return; }
        briefPreview.innerHTML=q.__frag||briefFragment(q);
        briefPreview.scrollTop=0;
        if(briefMask) briefMask.classList.add("show");
        toast("参阅材料已编制完成");
      })
      .catch(function(e){
        if(!alive()) return;
        document.body.classList.remove("fs-lock");
        if(progMask) progMask.classList.remove("show");
        toast("编制未完成："+(e&&e.message?e.message:"请重试"));
      });
    }
    if(cancelProg) cancelProg.addEventListener("click",function(){
      cancelBriefPipeline(); toast("已取消编制");
    });

    // —— 参阅材料交互 ——
    viewBrief.addEventListener("click",function(){ runBriefPipeline("view"); });
    downloadBrief.addEventListener("click",function(){ runBriefPipeline("download"); });
    copyBrief.addEventListener("click",function(){
      if(!lastQuery) return;
      var t=briefText(lastQuery);
      if(navigator.clipboard&&navigator.clipboard.writeText){
        navigator.clipboard.writeText(t).then(function(){toast("全文已复制");},function(){fallbackCopy(t);toast("全文已复制");});
      } else { fallbackCopy(t); toast("全文已复制"); }
    });
    if(fullscreenBrief) fullscreenBrief.addEventListener("click",function(){
      if(isBriefFs()) exitBriefFs(); else enterBriefFs();
    });
    function closeBriefSheet(){ exitBriefFs(); briefMask.classList.remove("show"); }
    closeBriefBtn.addEventListener("click",closeBriefSheet);
    briefMask.addEventListener("click",function(e){ if(e.target===briefMask) closeBriefSheet(); });
    ["fullscreenchange","webkitfullscreenchange"].forEach(function(ev){
      document.addEventListener(ev,function(){
        if(isBriefFs() && !(document.fullscreenElement||document.webkitFullscreenElement)) exitBriefFs();
      });
    });
    document.addEventListener("keydown",function(e){
      if(e.key!=="Escape"&&e.keyCode!==27) return;
      if(progMask && progMask.classList.contains("show")){ cancelBriefPipeline(); toast("已取消编制"); return; }
      if(isBriefFs()) exitBriefFs();
    });

    // —— 高级设置折叠（可选自定义后端；定位凭据仅服务端持有，页面不可见） ——
    if(BACKEND_URL) backendUrlInput.value=BACKEND_URL;
    advToggle.addEventListener("click",function(){
      var show=advPanel.classList.toggle("show");
      advToggle.classList.toggle("on",show);
      if(show && BACKEND_URL) backendUrlInput.value=BACKEND_URL;
    });
    saveBackend.addEventListener("click",function(){
      var v=backendUrlInput.value.trim();
      try{ if(v) localStorage.setItem("fjhx_backend_url",v); else localStorage.removeItem("fjhx_backend_url"); }catch(e){}
      BACKEND_URL=v;
      backendStatus.style.display="block"; backendStatus.className="tip";
      backendStatus.textContent=v?"已保存自定义后端地址；留空则使用同源实时定位服务（前端零 Key）。":"已清除，恢复同源实时定位服务；无后端时自动降级为行政区划中心近似。";
    });

    // ===== 网点半径内机构查询（2026-11-12）=====
    // 数据源：资料库 DATA 文件夹三份含经纬度清单，由 build_nearby_data.py 去重后按地市分片。
    // 前端按查询圆外接矩形与市域包围盒相交情况按需加载分片，本地完成测距与筛选，
    // 不调用任何后端接口、不携带任何 Key 或凭据，静态托管与同源部署行为一致。
    var MANIFEST = window.NEARBY_MANIFEST || {cities:[],total:0,catLabels:{},levelLabels:{}};
    var NEARBY_VER = window.NEARBY_VER || "1";
    var tabOrg=$("tabOrg"), tabRadius=$("tabRadius"),
        branchInput=$("branchName"), branchSug=$("branchSug"), branchPicked=$("branchPicked"),
        radiusInput=$("radiusKm"), radiusBtn=$("radiusBtn"), radiusReset=$("radiusReset"),
        radSummary=$("radSummary"), radStat=$("radStat"), radFilter=$("radFilter"),
        radList=$("radList"), radPager=$("radPager"), radPrev=$("radPrev"), radNext=$("radNext"),
        radPageInfo=$("radPageInfo"), radNote=$("radNote"),
        radLevel=$("radLevel"), radKeyword=$("radKeyword");

    // 地图视图：经纬度等距投影自绘，不依赖任何地图 SDK / 瓦片 / Key
    var CAT_COLORS={1:"#e05345",2:"#1a5bb8",4:"#1f9d57",0:"#d98a12"};
    var radView="map", radViewMap=$("radViewMap"), radViewList=$("radViewList"),
        mapWrap=$("radMapWrap"), mapBox=$("radMap"), mapSvg=$("radSvg"),
        radG=$("radG"), radPins=$("radPins"), radOvl=$("radOvl"), radClipRect=$("radClipRect"),
        radMapHead=$("radMapHead"), radPinInfo=$("radPinInfo"), radMapNote=$("radMapNote"),
        pinModal=$("pinModal"), pinCard=$("pinCard"),
        radMapZoomIn=$("radMapZoomIn"), radMapZoomOut=$("radMapZoomOut"),
        radMapReset=$("radMapReset"), radMapFull=$("radMapFull"), radMapLayer=$("radMapLayer"),
        radTiles=$("radTiles"), radTileInner=$("radTileInner"),
        mapScale=1, mapPanX=0, mapPanY=0, mapBuckets=[], mapDrag=null, mapMoved=false, mapResizeTimer=null,
        tilesOn=true, tilesAvailable=true, tileEls={}, tileOk=0, tileErr=0;

    function setMode(m){
      var isRad=(m==="radius");
      tabOrg.classList.toggle("on",!isRad); tabRadius.classList.toggle("on",isRad);
      tabOrg.setAttribute("aria-selected",isRad?"false":"true");
      tabRadius.setAttribute("aria-selected",isRad?"true":"false");
      $("orgCard").style.display=isRad?"none":"";
      $("resultCard").style.display=isRad?"none":"";
      $("radiusCard").style.display=isRad?"":"none";
      $("radResultCard").style.display=isRad?"":"none";
      var sub=document.querySelector(".top__sub");
      if(sub) sub.textContent=isRad
        ? "选择本行网点并录入公里半径，查询范围内机关、事业单位与学校。福建全省及浙江温州适用。"
        : "输入机构名称（模糊即可），自动匹配距离最近的福建海峡银行网点。福建全省及浙江温州适用。";
    }
    tabOrg.addEventListener("click",function(){ setMode("org"); });
    tabRadius.addEventListener("click",function(){ setMode("radius"); });

    // —— 本行网点模糊联想：91 家权威网点本地匹配，零网络请求 ——
    var pickedBranch=null, branchItems=[], branchActive=-1, branchTimer=null;
    function hideBranchSug(){ branchSug.classList.remove("show"); branchActive=-1; }
    function renderBranchSug(q){
      var s=String(q).replace(/\\s+/g,"").toLowerCase();
      var items=s ? BRANCHES.filter(function(b){
        return [b.name,b.city,b.district,b.type,b.address].join(" ").toLowerCase().indexOf(s)>=0;
      }).slice(0,8) : [];
      branchItems=items;
      if(!items.length){ hideBranchSug(); return; }
      branchSug.innerHTML='<div class="sug-hint">本行网点资料库（共 '+BRANCHES.length+' 家，点选后作为圆心）</div>'+
        items.map(function(b,i){
          return '<div class="sug-item" data-i="'+i+'"><div class="sug-item__n">'+esc(b.name)+'</div>'+
            '<div class="sug-item__d">'+esc(b.city+" · "+b.district)+'　'+esc(b.address)+'</div></div>';
        }).join("");
      branchSug.classList.add("show");
    }
    function pickBranch(i){
      var b=branchItems[i]; if(!b) return;
      pickedBranch=b; branchInput.value=b.name; hideBranchSug();
      branchPicked.style.display="block";
      branchPicked.innerHTML="已选圆心：<b>"+esc(b.name)+"</b>　"+esc(b.city+" · "+b.district)+
        "<br>网点坐标："+Number(b.lat).toFixed(6)+", "+Number(b.lng).toFixed(6)+"（GCJ-02）";
    }
    branchInput.addEventListener("input",function(){
      pickedBranch=null; branchPicked.style.display="none";
      clearTimeout(branchTimer);
      var q=branchInput.value.trim();
      branchTimer=setTimeout(function(){ renderBranchSug(q); },160);
    });
    branchInput.addEventListener("keydown",function(e){
      if(!branchSug.classList.contains("show")){
        if(e.key==="Enter"){ e.preventDefault(); radiusBtn.click(); }
        return;
      }
      if(e.key==="ArrowDown"||e.key==="ArrowUp"){
        e.preventDefault();
        branchActive+=(e.key==="ArrowDown"?1:-1);
        if(branchActive<0) branchActive=branchItems.length-1;
        if(branchActive>=branchItems.length) branchActive=0;
        Array.prototype.forEach.call(branchSug.querySelectorAll(".sug-item"),function(el,i){
          el.classList.toggle("active",i===branchActive);
        });
      }else if(e.key==="Enter"){
        e.preventDefault(); pickBranch(branchActive>=0?branchActive:0);
      }else if(e.key==="Escape"){ hideBranchSug(); }
    });
    branchSug.addEventListener("mousedown",function(e){
      var t=e.target;
      while(t && t!==branchSug && !(t.classList&&t.classList.contains("sug-item"))) t=t.parentNode;
      if(t && t!==branchSug){ e.preventDefault(); pickBranch(parseInt(t.getAttribute("data-i"),10)); }
    });
    document.addEventListener("click",function(e){
      if($("radiusCard").contains(e.target)) return;
      hideBranchSug();
    });

    // —— 分片按需加载 ——
    window.NEARBY_CHUNK=window.NEARBY_CHUNK||{};
    var chunkLoading={};
    function loadChunk(i){
      if(window.NEARBY_CHUNK[i]) return Promise.resolve(window.NEARBY_CHUNK[i]);
      if(chunkLoading[i]) return chunkLoading[i];
      chunkLoading[i]=new Promise(function(res,rej){
        var s=document.createElement("script"), done=false;
        var timer=setTimeout(function(){ if(!done){ done=true; drop(s); rej(new Error("timeout")); } },20000);
        function drop(el){ if(el&&el.parentNode) el.parentNode.removeChild(el); }
        s.src="nearby_data/c"+i+".js?v="+NEARBY_VER;
        s.onload=function(){ if(done) return; done=true; clearTimeout(timer); res(window.NEARBY_CHUNK[i]||[]); };
        s.onerror=function(){ if(done) return; done=true; clearTimeout(timer); drop(s); rej(new Error("load-failed")); };
        document.head.appendChild(s);
      });
      return chunkLoading[i];
    }
    function bboxFor(lat,lng,km){
      var dLat=km/111.32, cos=Math.max(0.2,Math.cos(lat*Math.PI/180)), dLng=km/(111.32*cos);
      return [lat-dLat,lat+dLat,lng-dLng,lng+dLng];
    }
    function boxHit(a,b){ return a[0]<=b[1]&&a[1]>=b[0]&&a[2]<=b[3]&&a[3]>=b[2]; }

    // —— 查询、筛选、分页 ——
    var radAll=[], radShown=[], radPage=1, radCat=0, radCenter=null, radKm=0, radToken=0, radKwTimer=null;
    var PAGE_SIZE=50;
    // 半径模式：入参为公里（x.km）。与上方机构查网点的 fmtDist（入参米）分开命名，避免同名覆盖。
    function fmtDistKm(km){ return km<1 ? Math.round(km*1000)+" m" : km.toFixed(2)+" km"; }
    function catNames(bit){
      var a=[]; if(bit&1)a.push("机关"); if(bit&2)a.push("事业单位"); if(bit&4)a.push("学校");
      return a.join("·")||"其他";
    }
    function setChipState(){
      Array.prototype.forEach.call(radFilter.querySelectorAll(".rad-chip"),function(el){
        el.classList.toggle("on",parseInt(el.getAttribute("data-cat"),10)===radCat);
      });
    }
    function runRadius(){
      var my=++radToken;
      closePinCard();
      exitMapFull();
      mapWrap.style.display="none"; radList.style.display="flex";
      clearTiles(); tilesAvailable=true; tileOk=0; tileErr=0;
      radPinInfo.innerHTML="点击地图上的彩色图钉查看单位详情；同址或近距离机构以数字聚合显示。";
      if(!pickedBranch){
        radSummary.className="tip err";
        radSummary.textContent="请先模糊录入网点名称，并在下拉列表中点选具体网点作为圆心。";
        radList.innerHTML=""; return;
      }
      var km=parseFloat(radiusInput.value);
      if(!isFinite(km)||km<0.1||km>50){
        radSummary.className="tip err";
        radSummary.textContent="请录入 0.1—50 之间的公里半径数字。";
        radList.innerHTML=""; return;
      }
      radCenter=pickedBranch; radKm=km; radCat=0; radPage=1;
      radLevel.value=""; radKeyword.value=""; setChipState();
      var box=bboxFor(pickedBranch.lat,pickedBranch.lng,km);
      var need=(MANIFEST.cities||[]).filter(function(c){ return boxHit(box,c.bbox); });
      radStat.style.display="none"; radFilter.style.display="none";
      radPager.style.display="none"; radNote.style.display="none";
      if(!need.length){
        radSummary.className="tip err";
        radSummary.textContent="该半径未与任何已收录地市片区相交，请放大半径后重试。";
        radList.innerHTML=""; return;
      }
      radSummary.className="tip";
      radSummary.innerHTML="正在加载 "+need.length+" 个地市数据分片并测算距离…";
      radList.innerHTML='<div class="rad-loading">正在读取资料库清单，请稍候…</div>';
      Promise.all(need.map(function(c){ return loadChunk(c.i); })).then(function(chunks){
        if(my!==radToken) return;
        var out=[];
        chunks.forEach(function(rows,j){
          var cityName=need[j].name;
          (rows||[]).forEach(function(r){
            var d=haversineM(radCenter.lat,radCenter.lng,r[5],r[6]);
            if(d<=km*1000) out.push({n:r[0],c:r[1],l:r[2],d:r[3],a:r[4],e:r[7],city:cityName,
              km:d/1000,lat:r[5],lng:r[6]});
          });
        });
        out.sort(function(a,b){ return a.km-b.km || (a.n<b.n?-1:a.n>b.n?1:0); });
        radAll=out;
        radView="map"; mapScale=1; mapPanX=0; mapPanY=0;
        applyRadFilter();
        // 查询完成后视口自动移到地图，形成「点查询 → 进入地图界面」的连续体验
        setTimeout(function(){
          if(my!==radToken||radView!=="map") return;
          try{ mapWrap.scrollIntoView({behavior:"smooth",block:"start"}); }
          catch(err){ mapWrap.scrollIntoView(); }
        },80);
      }).catch(function(err){
        if(my!==radToken) return;
        radSummary.className="tip err";
        radSummary.textContent="资料库分片加载失败（"+esc(String(err&&err.message||"网络异常"))+"）；请检查网络后重试，页面不会以估算数据替代。";
        radList.innerHTML="";
      });
    }
    function applyRadFilter(){
      var lv=radLevel.value, kw=radKeyword.value.trim().toLowerCase();
      radShown=radAll.filter(function(x){
        if(radCat && !(x.c & radCat)) return false;
        if(lv!=="" && String(x.l)!==lv) return false;
        if(kw && x.n.toLowerCase().indexOf(kw)<0) return false;
        return true;
      });
      radPage=1; renderRad();
    }
    function renderRad(){
      var total=radAll.length, shown=radShown.length;
      var c1=0,c2=0,c4=0;
      radAll.forEach(function(x){ if(x.c&1)c1++; if(x.c&2)c2++; if(x.c&4)c4++; });
      radStat.innerHTML=
        '<div class="rad-stat__item"><div class="rad-stat__n">'+total+'</div><div class="rad-stat__t">合计主体</div></div>'+
        '<div class="rad-stat__item"><div class="rad-stat__n">'+c1+'</div><div class="rad-stat__t">机关</div></div>'+
        '<div class="rad-stat__item"><div class="rad-stat__n">'+c2+'</div><div class="rad-stat__t">事业单位</div></div>'+
        '<div class="rad-stat__item"><div class="rad-stat__n">'+c4+'</div><div class="rad-stat__t">学校</div></div>';
      radStat.style.display="flex"; radFilter.style.display="flex";
      radSummary.className="tip";
      radSummary.innerHTML="以 <b>"+esc(radCenter.name)+"</b> 为圆心、半径 <b>"+radKm+" km</b>，命中 <b>"+total+
        "</b> 家主体"+(shown!==total?"，当前筛选显示 "+shown+" 家":"")+"；按直线距离由近及远排列。";
      var pages=Math.max(1,Math.ceil(shown/PAGE_SIZE));
      if(radPage>pages) radPage=pages;
      var start=(radPage-1)*PAGE_SIZE, rows=radShown.slice(start,start+PAGE_SIZE);
      if(!rows.length){
        radList.innerHTML='<div class="rad-loading">当前筛选条件下暂无已收录主体，可放宽筛选或放大半径。</div>';
      }else{
        radList.innerHTML=rows.map(function(x){
          var meta='<span class="rad-tag">'+esc(catNames(x.c))+'</span>'+
            '<span class="rad-tag lv">'+esc((MANIFEST.levelLabels||{})[String(x.l)]||"未标明")+'</span>'+
            esc(x.city+" · "+x.d);
          if(x.e) meta+='　<span class="rad-tag">'+esc(x.e)+'</span>';
          meta+='<br>登记地址：'+esc(x.a||"未列示");
          return '<div class="rad-item"><div class="rad-item__top">'+
            '<div class="rad-item__n">'+esc(x.n)+'</div>'+
            '<div class="rad-item__d">'+fmtDistKm(x.km)+'</div></div>'+
            '<div class="rad-item__meta">'+meta+'</div></div>';
        }).join("");
      }
      radPager.style.display=pages>1?"flex":"none";
      radPageInfo.textContent="第 "+radPage+" / "+pages+" 页";
      radPrev.disabled=radPage<=1; radNext.disabled=radPage>=pages;
      radNote.style.display="block";
      radNote.innerHTML="数据来源：资料库 DATA 文件夹「机关 / 事业单位 / 学校」三份含经纬度整合清单（"+
        esc(MANIFEST.generated||"")+" 生成，去重后 "+(MANIFEST.total||0)+" 家主体，"+
        esc(MANIFEST.coordSystem||"GCJ-02")+"）。本页仅列示公开登记的机构名称、类别、行政层级、区划与登记地址；"+
        "距离为经纬度直线距离估算，部分主体坐标为登记机关或区县中心级定位，同址机构距离相同。"+
        "结果仅供行内政务合作位置参考，现场应用请以登记地址复核。";
      // 查询结果默认进入地图视图，清单视图可一键切回；两视图共用同一份筛选结果
      radViewMap.classList.toggle("on",radView==="map");
      radViewList.classList.toggle("on",radView==="list");
      radViewMap.setAttribute("aria-selected",radView==="map"?"true":"false");
      radViewList.setAttribute("aria-selected",radView==="list"?"true":"false");
      mapWrap.style.display=radView==="map"?"":"none";
      radList.style.display=radView==="list"?"flex":"none";
      radPager.style.display=(radView==="list"&&pages>1)?"flex":"none";
      radNote.style.display=radView==="list"?"block":"none";
      if(radView==="map") renderRadMap();
    }

    // ===== 地图渲染：等距投影 + 类别着色图钉 + 同址聚合（零外部地图依赖）=====
    function catKey(c){
      var n=((c&1)?1:0)+((c&2)?1:0)+((c&4)?1:0);
      if(n>1) return 0;
      if(c&1) return 1;
      if(c&2) return 2;
      if(c&4) return 4;
      return -1;
    }
    function catColor(c){
      var k=catKey(c);
      return k<0 ? "#8a97aa" : CAT_COLORS[k];
    }
    function niceStep(km){
      var raw=Math.max(0.01,km)/3.5, p=Math.pow(10,Math.floor(Math.log(raw)/Math.LN10)), f=raw/p;
      return (f<1.5?1:f<3?2:f<7?5:10)*p;
    }
    function trimNum(v){
      if(v>=1) return (Math.round(v*10)/10)+"";
      return (Math.round(v*100)/100)+"";
    }
    function bucketColor(items){
      var cnt={}, max=0, win=-1;
      items.forEach(function(x){
        var k=catKey(x.c); cnt[k]=(cnt[k]||0)+1;
        if(cnt[k]>max){ max=cnt[k]; win=k; }
      });
      if(win<0) return "#8a97aa";
      if(max/items.length<=0.5) return CAT_COLORS[0];
      return CAT_COLORS[win];
    }
    function exitMapFull(){
      if(mapWrap.classList.contains("full")){
        mapWrap.classList.remove("full");
        document.body.classList.remove("rad-map-lock");
        radMapFull.textContent="⛶";
      }
    }
    // ===== 街道底图瓦片层（同源 /api/tiles 代理，前端零 Key、不直连地图域名）=====
    // 瓦片按 Web Mercator 切片，与页面等距投影在半径范围内局部近似对齐并如实标注。
    function clearTiles(){
      Object.keys(tileEls).forEach(function(k){
        var el=tileEls[k]; if(el.parentNode) el.parentNode.removeChild(el);
      });
      tileEls={};
    }
    function tileHealth(){
      if(tilesAvailable && tileErr>=2 && tileOk===0){
        tilesAvailable=false;
        radTiles.style.display="none";
        renderRadMap();   // 重绘 HUD 与说明，如实标注底图不可用、不显示空白底图
      }
    }
    function renderTiles(o){
      if(!tilesOn||!tilesAvailable){
        radTiles.style.display="none"; mapBox.classList.remove("has-tiles"); return;
      }
      radTiles.style.display="block"; mapBox.classList.add("has-tiles");
      var TS=256, n=Math.pow(2,o.z);
      var x0=Math.floor((o.wx-o.cx/o.s)/TS), x1=Math.floor((o.wx+(o.W-o.cx)/o.s)/TS);
      var y0=Math.floor((o.wy-o.cy/o.s)/TS), y1=Math.floor((o.wy+(o.H-o.cy)/o.s)/TS);
      if((x1-x0+1)*(y1-y0+1)>140){
        radTiles.style.display="none"; mapBox.classList.remove("has-tiles"); return;
      }
      var need={};
      for(var tx=x0;tx<=x1;tx++){
        for(var ty=y0;ty<=y1;ty++){
          if(tx<0||ty<0||tx>=n||ty>=n) continue;
          var key=o.z+"/"+tx+"/"+ty; need[key]=1;
          if(!tileEls[key]){
            var img=document.createElement("img");
            img.alt=""; img.setAttribute("data-key",key);
            img.style.left=(tx*TS)+"px"; img.style.top=(ty*TS)+"px";
            img.onload=function(){ this.className="ok"; tileOk++; };
            img.onerror=function(){ this.className="bad"; tileErr++; tileHealth(); };
            img.src=TILE_BASE+"z="+o.z+"&x="+tx+"&y="+ty;
            tileEls[key]=img; radTileInner.appendChild(img);
          }
        }
      }
      Object.keys(tileEls).forEach(function(k){
        if(!need[k]){ var el=tileEls[k]; if(el.parentNode) el.parentNode.removeChild(el); delete tileEls[k]; }
      });
      radTileInner.style.transform="translate("+o.cx+"px,"+o.cy+"px) scale("+o.s+") translate("+(-o.wx)+"px,"+(-o.wy)+"px)";
    }

    function renderRadMap(){
      if(!radCenter || !radAll.length) return;
      if(!radShown.length) radPinInfo.innerHTML="当前筛选条件下暂无已收录主体，可放宽筛选或放大半径。";
      var W=mapBox.clientWidth||340, H=mapBox.clientHeight||420;
      if(W<60||H<60) return;
      mapSvg.setAttribute("viewBox","0 0 "+W+" "+H);
      radClipRect.setAttribute("width",W);
      radClipRect.setAttribute("height",H);
      var cx=W/2+mapPanX, cy=H/2+mapPanY;
      var R=Math.min(W,H)*0.40*mapScale, kmPerPx=radKm/R;
      var cosLat=Math.max(0.2,Math.cos(radCenter.lat*Math.PI/180));
      function proj(lat,lng){
        return [cx+(lng-radCenter.lng)*111.32*cosLat/kmPerPx,
                cy-(lat-radCenter.lat)*111.32/kmPerPx];
      }
      // 街道底图：Web Mercator 瓦片级别与局部缩放，使瓦片与等距投影图钉对齐
      var targetPxPerKm=R/radKm;
      var tz=Math.round(Math.log(targetPxPerKm*360*111.32*cosLat/256)/Math.LN2);
      tz=Math.max(3,Math.min(18,tz));
      var world=256*Math.pow(2,tz);
      var mercPxPerKm=world/(360*111.32*cosLat);
      var tileScale=targetPxPerKm/mercPxPerKm;
      var latR=radCenter.lat*Math.PI/180;
      var wx=(radCenter.lng+180)/360*world;
      var wy=(1-Math.log(Math.tan(latR)+1/Math.cos(latR))/Math.PI)/2*world;
      // 经纬网格（等距近似）与半径圈
      var step=niceStep(radKm), base="", n=Math.ceil(radKm/step)+3;
      for(var i=-n;i<=n;i++){
        var v=i*step, gx=cx+v/kmPerPx, gy=cy-v/kmPerPx;
        if(gx>=0&&gx<=W) base+='<line class="rad-grid" x1="'+gx.toFixed(1)+'" y1="0" x2="'+gx.toFixed(1)+'" y2="'+H+'"/>';
        if(gy>=0&&gy<=H) base+='<line class="rad-grid" x1="0" y1="'+gy.toFixed(1)+'" x2="'+W+'" y2="'+gy.toFixed(1)+'"/>';
      }
      base+='<line class="rad-axis" x1="0" y1="'+cy.toFixed(1)+'" x2="'+W+'" y2="'+cy.toFixed(1)+'"/>'+
        '<line class="rad-axis" x1="'+cx.toFixed(1)+'" y1="0" x2="'+cx.toFixed(1)+'" y2="'+H+'"/>'+
        '<circle class="rad-ring" cx="'+cx.toFixed(1)+'" cy="'+cy.toFixed(1)+'" r="'+R.toFixed(1)+'"/>'+
        '<circle class="rad-ring-inner" cx="'+cx.toFixed(1)+'" cy="'+cy.toFixed(1)+'" r="'+(R/2).toFixed(1)+'"/>';
      radG.innerHTML=base;

      // 类别图钉：按 22px 网格聚合，视口外不绘制，控制节点数
      var CELL=22, buckets={}, list=[];
      radShown.forEach(function(x){
        if(!isFinite(x.lat)||!isFinite(x.lng)) return;
        var p=proj(x.lat,x.lng), px=p[0], py=p[1];
        if(px<-24||px>W+24||py<-24||py>H+24) return;
        var key=Math.floor(px/CELL)+"|"+Math.floor(py/CELL), b=buckets[key];
        if(!b){ b={x:0,y:0,items:[]}; buckets[key]=b; list.push(b); }
        b.items.push(x); b.x+=px; b.y+=py;
      });
      mapBuckets=list;
      var pins="";
      list.forEach(function(b,bi){
        b.x/=b.items.length; b.y/=b.items.length;
        var col=bucketColor(b.items), pos='transform="translate('+b.x.toFixed(1)+','+b.y.toFixed(1)+')"';
        if(b.items.length===1){
          pins+='<g class="rad-pin" data-k="'+bi+'" '+pos+'>'+
            '<path d="M0 0 C-5 -7 -8 -12 -8 -16 A8 8 0 1 1 8 -16 C8 -12 5 -7 0 0 Z" fill="'+col+'" stroke="#fff" stroke-width="1.5"/>'+
            '<circle cx="0" cy="-16" r="2.6" fill="#fff"/></g>';
        }else{
          var r=Math.min(17,10+Math.min(6,Math.floor(b.items.length/8)));
          pins+='<g class="rad-cluster" data-k="'+bi+'" '+pos+'>'+
            '<circle r="'+r+'" fill="'+col+'" opacity=".92"/>'+
            '<text y="0">'+(b.items.length>99?"99+":b.items.length)+'</text></g>';
        }
      });
      // 圆心：本行网点
      var shortName=radCenter.name.split("(")[1]||radCenter.name;
      shortName=shortName.replace(")","").replace("）","");
      if(shortName.length>12) shortName=shortName.slice(0,12)+"…";
      pins+='<g class="rad-center-pin" transform="translate('+cx.toFixed(1)+','+cy.toFixed(1)+')">'+
        '<path d="M0 0 C-8 -11 -13 -17 -13 -24 A13 13 0 1 1 13 -24 C13 -17 8 -11 0 0 Z" fill="#0f3f86" stroke="#fff" stroke-width="2"/>'+
        '<text y="-24">行</text></g>'+
        '<text class="rad-map__lbl" x="'+(cx+16).toFixed(1)+'" y="'+(cy+4).toFixed(1)+'">'+esc(shortName)+'</text>';
      radPins.innerHTML=pins;

      // 叠加信息：中心坐标、半径、格距、比例尺、北针
      var scaleKm=niceStep(radKm/2.5), scalePx=scaleKm/kmPerPx, guard=0;
      while(scalePx<34&&guard++<8){ scaleKm*=2; scalePx=scaleKm/kmPerPx; }
      while(scalePx>110&&guard++<8){ scaleKm/=2; scalePx=scaleKm/kmPerPx; }
      radOvl.innerHTML=
        '<rect class="rad-hud-bg" x="4" y="3" width="'+Math.min(W-8,268)+'" height="33" rx="6"/>'+
        '<text class="rad-map__ov" x="10" y="16">N ↑　圆心 '+Number(radCenter.lat).toFixed(4)+', '+Number(radCenter.lng).toFixed(4)+'（GCJ-02）</text>'+
        '<text class="rad-map__ov" x="10" y="31">半径 '+radKm+' km　网格 '+trimNum(step)+' km　显示 '+radShown.length+' / '+radAll.length+' 家</text>'+
        '<rect class="rad-hud-bg" x="4" y="'+(H-30)+'" width="'+Math.min(W-8,102+scalePx)+'" height="25" rx="6"/>'+
        '<line x1="10" y1="'+(H-16)+'" x2="'+(10+scalePx).toFixed(1)+'" y2="'+(H-16)+'" stroke="#5a6b82" stroke-width="2"/>'+
        '<line x1="10" y1="'+(H-20)+'" x2="10" y2="'+(H-12)+'" stroke="#5a6b82" stroke-width="2"/>'+
        '<line x1="'+(10+scalePx).toFixed(1)+'" y1="'+(H-20)+'" x2="'+(10+scalePx).toFixed(1)+'" y2="'+(H-12)+'" stroke="#5a6b82" stroke-width="2"/>'+
        '<text class="rad-map__ov" x="'+(16+scalePx).toFixed(1)+'" y="'+(H-12)+'">'+trimNum(scaleKm)+' km</text>';
      var tileState=!tilesAvailable
        ? '<span class="mh">街道底图未就绪 · 已显示零依赖点位分布图</span>'
        : (tilesOn ? '<span class="mh">街道底图：同源代理 · 前端零 Key</span>'
                   : '<span class="mh">街道底图已关闭 · 点位分布图</span>');
      radMapHead.innerHTML='<span class="mh">圆心 <b>'+esc(radCenter.name)+'</b></span>'+
        '<span class="mh">半径 <b>'+radKm+' km</b></span>'+
        '<span class="mh">当前视图 <b>'+radShown.length+'</b> 家</span>'+
        '<span class="mh">街道底图 + 等距投影点位图层（局部近似对齐）</span>'+tileState;
      radMapNote.innerHTML="图钉颜色按资料库登记的机构类别区分（聚合点按该点内多数类别着色）；同址或近距离机构合并为带数字的聚合点，点击可展开明细。"+
        "部分主体坐标为登记机关或区县中心级定位，同址机构位置重合属正常现象，现场应用请以登记地址复核。"+
        "街道底图瓦片经同源 /api/tiles 代理取得（静态版经已授权主站跨域代理），页面不直连任何地图域名、不携带地图 Key；"+
        "底图不可用时自动退回本地绘制的点位分布图并如实标注。瓦片按 Web Mercator 切片，与等距投影点位在半径范围内局部近似对齐，仅供位置参考。";
      renderTiles({z:tz,wx:wx,wy:wy,s:tileScale,cx:cx,cy:cy,W:W,H:H});
    }
    function pinInfoRows(x){
      return '<div class="pin-card__row"><span class="pin-card__k">机构类别</span>'+
          '<span class="pin-card__v"><i class="pin-card__dot" style="background:'+catColor(x.c)+'"></i>'+
          esc(catNames(x.c))+'</span></div>'+
        '<div class="pin-card__row"><span class="pin-card__k">行政层级</span>'+
          '<span class="pin-card__v">'+esc((MANIFEST.levelLabels||{})[String(x.l)]||"未标明")+'</span></div>'+
        '<div class="pin-card__row"><span class="pin-card__k">所属区划</span>'+
          '<span class="pin-card__v">'+esc(x.city+" · "+x.d)+'</span></div>'+
        '<div class="pin-card__row"><span class="pin-card__k">直线距离</span>'+
          '<span class="pin-card__v pin-card__dist">距圆心 '+fmtDistKm(x.km)+'</span></div>'+
        '<div class="pin-card__row"><span class="pin-card__k">登记地址</span>'+
          '<span class="pin-card__v">'+esc(x.a||"未列示")+'</span></div>'+
        (x.e?'<div class="pin-card__row"><span class="pin-card__k">备注</span>'+
          '<span class="pin-card__v">'+esc(x.e)+'</span></div>':'')+
        '<div class="pin-card__row"><span class="pin-card__k">坐标</span>'+
          '<span class="pin-card__v">'+Number(x.lat).toFixed(6)+', '+Number(x.lng).toFixed(6)+'（GCJ-02）</span></div>';
    }
    // 点击图钉/聚合点内的单位 → 弹出「单位主要信息」卡
    function openPinCard(x){
      if(!x) return;
      pinCard.innerHTML='<div class="pin-card__hd"><div class="pin-card__ttl">'+esc(x.n)+'</div>'+
        '<button type="button" class="pin-card__x" data-close aria-label="关闭">×</button></div>'+
        '<div class="pin-card__sub">单位主要信息 · 公开登记口径</div>'+
        pinInfoRows(x)+
        '<div class="pin-card__acts"><button type="button" data-close>关闭</button></div>';
      pinModal.classList.add("on");
    }
    function openPinCluster(arr){
      var rows='<div class="pin-card__hd"><div class="pin-card__ttl">该位置共 '+arr.length+' 家主体</div>'+
        '<button type="button" class="pin-card__x" data-close aria-label="关闭">×</button></div>'+
        '<div class="pin-card__sub">同址或近距离聚合 · 点击单位查看主要信息</div>';
      arr.slice(0,20).forEach(function(x,i){
        rows+='<div class="pin-card__li" data-pi="'+i+'"><div class="a"><i class="pin-card__dot" style="background:'+
          catColor(x.c)+'"></i>'+esc(x.n)+'</div><div class="b">'+esc(catNames(x.c))+' · '+esc(x.d)+
          ' · 距圆心 '+fmtDistKm(x.km)+'</div></div>';
      });
      if(arr.length>20) rows+='<div class="pin-card__more">仅展示距圆心最近 20 家，切换「清单」查看全部。</div>';
      rows+='<div class="pin-card__acts"><button type="button" data-close>关闭</button></div>';
      pinCard.innerHTML=rows;
      pinCard._items=arr;
      pinModal.classList.add("on");
    }
    function closePinCard(){ pinModal.classList.remove("on"); pinCard._items=null; }
    function renderPinInfo(x){
      if(!x) return;
      radPinInfo.innerHTML='<div class="pi__t">'+esc(x.n)+'</div>'+
        '<div class="pi__r"><span style="color:'+catColor(x.c)+'">●</span> '+esc(catNames(x.c))+' · '+
        esc((MANIFEST.levelLabels||{})[String(x.l)]||"未标明")+' · '+esc(x.city+" · "+x.d)+
        '　距圆心 <b style="color:#1a5bb8">'+fmtDistKm(x.km)+'</b></div>'+
        '<div class="pi__r">登记地址：'+esc(x.a||"未列示")+'</div>'+
        (x.e?'<div class="pi__r">备注：'+esc(x.e)+'</div>':'')+
        '<div class="pi__r" style="margin-top:4px">点击图钉已弹出「单位主要信息」卡。</div>';
    }
    function showBucket(k){
      var b=mapBuckets[k]; if(!b||!b.items.length) return;
      var arr=b.items.slice().sort(function(a,c){ return a.km-c.km; });
      if(arr.length===1){ renderPinInfo(arr[0]); openPinCard(arr[0]); return; }
      renderPinInfo(arr[0]);
      openPinCluster(arr);
    }
    function zoomMap(f){
      mapScale=Math.max(0.4,Math.min(16,mapScale*f));
      renderRadMap();
    }
    mapSvg.addEventListener("click",function(e){
      if(mapMoved){ mapMoved=false; return; }
      var t=e.target;
      while(t&&t!==mapSvg && !(t.getAttribute&&t.getAttribute("data-k")!==null)) t=t.parentNode;
      if(t&&t!==mapSvg) showBucket(parseInt(t.getAttribute("data-k"),10));
    });
    // 详情卡：点关闭按钮或遮罩关闭；聚合列表内点单位 → 看该单位主要信息
    pinModal.addEventListener("click",function(e){ if(e.target===pinModal) closePinCard(); });
    pinCard.addEventListener("click",function(e){
      var t=e.target;
      while(t&&t!==pinCard && !(t.getAttribute&&(t.getAttribute("data-close")!==null||t.getAttribute("data-pi")!==null))) t=t.parentNode;
      if(t===pinCard) return;
      if(t.getAttribute("data-close")!==null){ closePinCard(); return; }
      if(t.getAttribute("data-pi")!==null&&pinCard._items){
        var x=pinCard._items[parseInt(t.getAttribute("data-pi"),10)];
        if(x){ renderPinInfo(x); openPinCard(x); }
      }
    });
    function dragStart(x,y){
      mapDrag={x:x,y:y}; mapMoved=false;
      mapSvg.classList.add("dragging");
    }
    function dragMove(x,y){
      if(!mapDrag) return;
      var dx=x-mapDrag.x, dy=y-mapDrag.y;
      if(Math.abs(dx)+Math.abs(dy)>4) mapMoved=true;
      var tr="translate("+dx+","+dy+")";
      radG.setAttribute("transform",tr); radPins.setAttribute("transform",tr);
    }
    function dragEnd(x,y){
      if(!mapDrag) return;
      mapPanX+=(x-mapDrag.x); mapPanY+=(y-mapDrag.y);
      mapDrag=null; mapSvg.classList.remove("dragging");
      radG.removeAttribute("transform"); radPins.removeAttribute("transform");
      renderRadMap();
      setTimeout(function(){ mapMoved=false; },0);
    }
    if(window.PointerEvent){
      mapSvg.addEventListener("pointerdown",function(e){ dragStart(e.clientX,e.clientY);
        try{ mapSvg.setPointerCapture(e.pointerId); }catch(err){} });
      mapSvg.addEventListener("pointermove",function(e){ dragMove(e.clientX,e.clientY); });
      mapSvg.addEventListener("pointerup",function(e){ dragEnd(e.clientX,e.clientY); });
      mapSvg.addEventListener("pointercancel",function(e){ dragEnd(e.clientX,e.clientY); });
    }else{
      mapSvg.addEventListener("touchstart",function(e){ if(e.touches.length===1) dragStart(e.touches[0].clientX,e.touches[0].clientY); },{passive:true});
      mapSvg.addEventListener("touchmove",function(e){ if(e.touches.length===1) dragMove(e.touches[0].clientX,e.touches[0].clientY); },{passive:true});
      mapSvg.addEventListener("touchend",function(e){ dragEnd(e.changedTouches[0].clientX,e.changedTouches[0].clientY); });
    }
    mapSvg.addEventListener("wheel",function(e){
      e.preventDefault(); zoomMap(e.deltaY<0?1.25:0.8);
    },{passive:false});
    radMapZoomIn.addEventListener("click",function(){ zoomMap(1.5); });
    radMapZoomOut.addEventListener("click",function(){ zoomMap(1/1.5); });
    radMapReset.addEventListener("click",function(){
      mapScale=1; mapPanX=0; mapPanY=0; renderRadMap();
    });
    radMapFull.addEventListener("click",function(){
      var on=!mapWrap.classList.contains("full");
      if(on){ mapWrap.classList.add("full"); document.body.classList.add("rad-map-lock"); }
      else exitMapFull();
      radMapFull.textContent=on?"✕":"⛶";
      setTimeout(renderRadMap,30);
    });
    radMapLayer.addEventListener("click",function(){
      tilesOn=!tilesOn;
      radMapLayer.classList.toggle("off",!tilesOn);
      if(tilesOn){ tilesAvailable=true; tileOk=0; tileErr=0; clearTiles(); }
      else radTiles.style.display="none";
      renderRadMap();
    });
    radViewMap.addEventListener("click",function(){ radView="map"; renderRad(); });
    radViewList.addEventListener("click",function(){ radView="list"; renderRad(); });
    window.addEventListener("resize",function(){
      clearTimeout(mapResizeTimer);
      mapResizeTimer=setTimeout(function(){ if(radView==="map"&&radAll.length) renderRadMap(); },180);
    });
    document.addEventListener("keydown",function(e){
      if(e.key!=="Escape") return;
      if(pinModal.classList.contains("on")){ closePinCard(); return; }
      if(mapWrap.classList.contains("full")){ exitMapFull(); renderRadMap(); }
    });

    radiusBtn.addEventListener("click",runRadius);
    radiusInput.addEventListener("keydown",function(e){ if(e.key==="Enter"){ e.preventDefault(); radiusBtn.click(); } });
    radiusReset.addEventListener("click",function(){
      closePinCard();
      radToken++; pickedBranch=null; branchInput.value=""; radiusInput.value="3";
      hideBranchSug(); branchPicked.style.display="none";
      radAll=[]; radShown=[]; radPage=1; radCat=0; setChipState();
      radLevel.value=""; radKeyword.value="";
      radSummary.className="tip"; radSummary.textContent="请选择本行网点并录入半径后查询。";
      radList.innerHTML=""; radStat.style.display="none"; radFilter.style.display="none";
      radPager.style.display="none"; radNote.style.display="none";
      exitMapFull(); mapWrap.style.display="none"; mapBuckets=[];
      radView="map"; mapScale=1; mapPanX=0; mapPanY=0;
      clearTiles(); tilesOn=true; tilesAvailable=true; tileOk=0; tileErr=0;
      radTiles.style.display="none"; radMapLayer.classList.remove("off");
      radList.style.display="flex";
      radPinInfo.innerHTML="点击地图上的彩色图钉查看单位详情；同址或近距离机构以数字聚合显示。";
    });
    Array.prototype.forEach.call(radFilter.querySelectorAll(".rad-chip"),function(el){
      el.addEventListener("click",function(){
        radCat=parseInt(el.getAttribute("data-cat"),10); setChipState(); applyRadFilter();
      });
    });
    radLevel.addEventListener("change",applyRadFilter);
    radKeyword.addEventListener("input",function(){
      clearTimeout(radKwTimer);
      radKwTimer=setTimeout(applyRadFilter,200);
    });
    radPrev.addEventListener("click",function(){ if(radPage>1){ radPage--; renderRad(); } });
    radNext.addEventListener("click",function(){ if(radPage*PAGE_SIZE<radShown.length){ radPage++; renderRad(); } });

  })();
  </script>
</body>
</html>
"""

html = html.replace("__REGION_JS__", REGION_JS)
html = html.replace("__PROV_JS__", PROV_JS)
html = html.replace("__BRANCH_DATA_JS__", BRANCH_DATA_JS)
html = html.replace("__NEARBY_MANIFEST_JS__", NEARBY_MANIFEST_JS)
html = html.replace("__NEARBY_VER__", NEARBY_VER)
html = html.replace("__ORG_INTEL_JS__", ORG_INTEL_JS)

out = os.path.join(BASE, "index.html")
html = html.replace("__ICON_B64__", "data:image/png;base64," + ICON_B64)
html = html.replace("__DOC_CSS_JS__", DOC_CSS_JS)
html = html.replace("__DOC_CSS__", DOC_CSS)
html = html.replace("__BRIEF_JS__", BRIEF_JS)
html = html.replace("__GEO_PROXY__", GEO_PROXY_URL)
html = html.replace("__PROFILE_PROXY__", PROFILE_PROXY_URL)
html = html.replace("__SUGGEST_PROXY__", SUGGEST_PROXY_URL)
html = html.replace("__TILE_PROXY__", TILE_PROXY_URL)
html = html.replace("__LOCAL_SUGGEST_JS__", LOCAL_SUGGEST_JS)
# 强校验：构建产物不得残留任何占位符、地图 Key 变量或外部接口调用痕迹
for _bad in ("__ORG_INTEL_JS__", "__NEARBY_MANIFEST_JS__", "__NEARBY_VER__",
             "__MAP_KEY_EXPR__", "__GEO_PROXY__", "__PROFILE_PROXY__",
             "__SUGGEST_PROXY__", "__TILE_PROXY__", "__LOCAL_SUGGEST_JS__",
             "String.fromCharCode", "apis.map.qq.com", "restapi.amap.com"):
    assert _bad not in html, "构建产物残留禁止内容：" + _bad
# 前端零直连：页面不得出现瓦片服务域名，瓦片一律经 /api/tiles 代理。
# 注意：资料库证据来源含 ditu.amap.com 的公开 POI 页面链接（仅作阅读引用，不作页面请求），不拦截。
for _host in ("autonavi.com", "gtimg.com", "tianditu.gov.cn", "appmaptile", "DataServer"):
    assert _host not in html, "构建产物残留地图瓦片上游域名：" + _host
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", out, "bytes:", len(html.encode("utf-8")),
      "branches:", len(branch_payload["branches"]),
      "intel_orgs:", INTEL_STATS["orgs"], "intel_fields:", INTEL_STATS["fields"],
      "sources:", INTEL_STATS["sources"])
