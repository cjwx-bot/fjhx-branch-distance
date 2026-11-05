# -*- coding: utf-8 -*-
"""构建单文件 H5：福建海峡银行最近网点查询（极简版）。

简化目标（用户 2026-11-05 要求）：
- 仅保留「机构名称」录入 + 「查询」按钮 + 「刷新」按钮；
- 去除：机构类型、单位地址、实时识别、所在地市、所在区县、精确经纬度 六项；
- 结果区仅展示「距离最近的福建海峡银行网点」（hero + 列表），不再反显机构所在行政区划/经纬度；
- 后端实时核验（企查查/天眼查）逻辑保留，作为可折叠「高级设置」，默认收起。
数据：server/data/branches.json 91 家权威网点 + 内置区县中心坐标，全部内联。
"""
import json, os, base64

# 定位服务凭据：以字符编码形式存放，构建时注入为 JS 运行时表达式，
# 避免明文出现在页面源码、设置项与构建脚本中（用户 2026-11-05 要求隐藏）。
# 注意：静态前端直连方案下，浏览器网络请求仍会携带该值；彻底不暴露需改走后端代理。
_KEY_CODES = [73,55,71,66,90,45,73,79,75,51,88,45,88,89,72,52,85,45,84,75,55,71,89,45,50,54,66,75,69,45,74,51,66,52,70]
MAP_KEY_EXPR = "String.fromCharCode(" + ",".join(str(n) for n in _KEY_CODES) + ")"

BASE = os.path.dirname(os.path.abspath(__file__))
BRANCH_JSON = os.path.join(BASE, "server", "data", "branches.json")

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

    .orgbadge{display:none;align-items:center;gap:8px;background:var(--ok-soft);border:1px solid #c4e8d2;border-radius:11px;padding:10px 12px;font-size:13px;color:#1c7a45;margin-bottom:12px}
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
      <div class="top__badge"><span class="dot"></span>已收录 91 家网点 · 直线距离估算</div>
    </header>

    <main class="body">
      <!-- 查询卡片 -->
      <section class="card">
        <div class="card__h"><span class="bar"></span><h2>机构名称查询</h2></div>

        <label class="fld" for="orgName">机构名称 <span class="opt">（模糊输入即可，如：福建省财政厅）</span></label>
        <input id="orgName" class="inp" type="text" placeholder="如：福建省财政厅 / 福州市教育局" maxlength="50">

        <div class="btn-row">
          <button class="btn btn-primary" id="searchBtn">🔍 查询</button>
          <button class="btn btn-ghost" id="refreshBtn">↻ 刷新</button>
        </div>

        <!-- 高级设置（可选，默认收起） -->
        <div class="toggle" id="advToggle"><span class="sw"></span><span>高级设置（可选）</span></div>
        <div class="backend" id="advPanel">
          <p class="backend__tip">本工具已启用精确定位：录入机构名称即按机构真实地址与经纬度测算最近网点，无需任何配置。如需对接企查查/天眼查实时核验机构全称与统一社会信用代码，可在此配置后端代理地址（仅保存在本设备）。</p>
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
        <div class="tip" id="resultTip">请输入机构名称后点击「查询」。</div>
        <div class="hero" id="hero"></div>
        <div class="list" id="resultList"></div>
        <div class="btn-row" id="resultActions" style="display:none">
          <button class="btn btn-ghost" id="copyBtn">复制结果到群</button>
        </div>
      </section>

      <!-- 使用说明 -->
      <section class="card">
        <div class="card__h"><span class="bar"></span><h2>使用说明</h2></div>
        <ul class="notes">
          <li>适用对象：福建省内及浙江温州地区的党政机关、事业单位、群团组织。</li>
          <li>距离为基于经纬度的直线距离估算（Haversine 公式），实际步行或驾车距离可能略有差异。</li>
          <li>网点坐标依据福建海峡银行官网网点目录（2026-08-21 版，共 91 家）结合腾讯地图公开位置实测匹配留存。</li>
          <li>本工具仅用于政务合作位置参考，录入信息仅保存在本设备本地。</li>
        </ul>
      </section>
    </main>

    <footer class="foot">福建海峡银行最近网点查询工具 · 仅用于政务合作位置参考</footer>
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

  <div class="toast" id="toast"></div>

  <script>
    window.REGION_DATA = __REGION_JS__;
    window.PROVINCE_OF_CITY = __PROV_JS__;
    window.BRANCH_DATA = __BRANCH_DATA_JS__;
  </script>

  <script>
  (function(){
    "use strict";
    var REGIONS = window.REGION_DATA || {};
    var PROV = window.PROVINCE_OF_CITY || {};
    var BRANCHES = (window.BRANCH_DATA && window.BRANCH_DATA.branches) || [];
    var BACKEND_URL = (function(){ try{ return localStorage.getItem("fjhx_backend_url")||""; }catch(e){ return ""; } })();
    // 精确定位凭据已内置且不可见：无输入框、不写入本地存储、页面源码不含明文。
    var MAP_KEY = (function(){
      try{ localStorage.removeItem("fjhx_map_key"); }catch(e){}  // 清理旧版本遗留的明文缓存
      return __MAP_KEY_EXPR__;
    })();
    var lastBackend = null;

    function $(id){ return document.getElementById(id); }
    var orgNameInput=$("orgName"), searchBtn=$("searchBtn"), refreshBtn=$("refreshBtn"),
        resultTip=$("resultTip"), resultList=$("resultList"), hero=$("hero"),
        orgBadge=$("orgBadge"), resultActions=$("resultActions"), copyBtn=$("copyBtn"),
        shareMask=$("shareMask"), shareContent=$("shareContent"), confirmShare=$("confirmShare"), closeShare=$("closeShare"),
        advToggle=$("advToggle"), advPanel=$("advPanel"), backendUrlInput=$("backendUrl"),
        saveBackend=$("saveBackend"), backendStatus=$("backendStatus");

    function esc(s){ return String(s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];}); }
    function toast(msg){ var t=$("toast"); t.textContent=msg; t.classList.add("show"); setTimeout(function(){t.classList.remove("show");},1800); }

    function haversineM(la1,lo1,la2,lo2){
      var R=6371000, dLa=(la2-la1)*Math.PI/180, dLo=(lo2-lo1)*Math.PI/180;
      var a=Math.sin(dLa/2)*Math.sin(dLa/2)+Math.cos(la1*Math.PI/180)*Math.cos(la2*Math.PI/180)*Math.sin(dLo/2)*Math.sin(dLo/2);
      return 2*R*Math.asin(Math.sqrt(a));
    }
    function fmtDist(m){ if(m<1000) return Math.round(m)+" 米"; if(m<100000) return (m/1000).toFixed(1)+" 公里"; return Math.round(m/1000)+" 公里"; }

    // —— JSONP 轻量封装（用于跨域调用腾讯地图 WebService）——
    function jsonp(url, cbName, timeout){
      return new Promise(function(resolve,reject){
        var sc=document.createElement("script"), called=false;
        var t=setTimeout(function(){ if(!called){ called=true; cleanup(); reject(new Error("请求超时")); } }, timeout||7000);
        function cleanup(){ clearTimeout(t); if(sc.parentNode) sc.parentNode.removeChild(sc); try{ delete window[cbName]; }catch(e){} }
        window[cbName]=function(d){ if(called) return; called=true; cleanup(); resolve(d); };
        sc.src=url+(url.indexOf("?")>-1?"&":"?")+"output=jsonp&callback="+encodeURIComponent(cbName);
        document.head.appendChild(sc);
      });
    }
    // 腾讯地图「地点建议」：凭机构名称反查真实坐标与地址（精确测算基准）
    function geocodeByName(name, region, key){
      var url="https://apis.map.qq.com/ws/place/v1/suggestion/?keyword="+encodeURIComponent(name)+
        "&region="+encodeURIComponent(region||"")+"&key="+encodeURIComponent(key);
      var cb="_qqsug"+Date.now();
      return jsonp(url, cb).then(function(j){
        if(j && j.status===0 && j.data && j.data.length){
          var d=j.data[0];
          if(d && d.location) return {title:d.title, address:d.address||"", lat:d.location.lat, lng:d.location.lng};
        }
        return null;
      }).catch(function(){ return null; });
    }

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
    var GOV_UNITS=["人民政府","发展和改革委员会","发改委","财政厅","教育厅","卫生健康委员会","卫健委","人力资源和社会保障","人社厅","自然资源厅","生态环境厅","交通运输厅","市场监督管理局","市场监管局","公安厅","司法厅","水利厅","农业农村厅","文化和旅游厅","文旅厅","民政厅","住房和城乡建设厅","住建厅","商务厅","审计厅","林业局","海洋与渔业局","广播电视局","体育局","统计局","医疗保障局","医保局","机关事务管理局","粮食和物资储备局","监狱管理局","人民银行","央行","分行","监管局","税务局","法院","检察院","省委","组织部","宣传部","委员会","银保监","证监","工会","共青团"];

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
    }

    function runLocalSearch(){
      lastBackend=null;
      orgBadge.style.display="none";
      var name=orgNameInput.value.trim();
      var base=parseAddress(name);
      if(!base){
        hero.style.display="none"; resultList.innerHTML=""; resultActions.style.display="none";
        resultTip.className="tip err";
        resultTip.textContent="未能识别行政区划。请在机构名称中填写含区/县名的内容（如“鼓楼区”），或展开「高级设置」配置实时核验。";
        return;
      }
      var approxNote = (MAP_KEY||BACKEND_URL) ? "" : "（按行政区划中心近似）";
      renderResult(computeItems(base.center), "该机构位置（行政区划中心近似）", approxNote);
    }

    // —— 精确测算：腾讯地图反查机构真实坐标后算最近网点 ——
    function doGeocodeSearch(name){
      lastBackend=null;
      resultTip.className="tip"; resultTip.textContent="正在通过地图精确定位「"+name+"」的真实地址与坐标…";
      hero.style.display="none"; resultList.innerHTML=""; resultActions.style.display="none";
      var hint=parseAddress(name);
      var region = hint ? (hint.city||hint.province) : "福建省";
      geocodeByName(name, region, MAP_KEY).then(function(g){
        if(!g){
          resultTip.className="tip err";
          resultTip.textContent="地图定位未返回结果（机构名称无法识别或服务暂不可用）；已切换为行政区划中心近似。";
          runLocalSearch(); return;
        }
        orgBadge.style.display="flex";
        orgBadge.innerHTML="📍 精确定位："+esc(g.title||"")+(g.address?" · "+esc(g.address):"");
        renderResult(computeItems({lat:g.lat,lng:g.lng}), "该机构真实位置（经纬度测算）");
      }).catch(function(e){
        resultTip.className="tip err";
        resultTip.textContent="地图定位请求失败："+e.message+"；已切换为行政区划中心近似。";
        runLocalSearch();
      });
    }

    searchBtn.addEventListener("click",function(){
      var name=orgNameInput.value.trim();
      if(!name){ toast("请输入机构名称"); orgNameInput.focus(); return; }
      if(BACKEND_URL){ doBackendSearch(name); return; }
      if(MAP_KEY){ doGeocodeSearch(name); return; }
      runLocalSearch();
    });
    orgNameInput.addEventListener("keydown",function(e){ if(e.key==="Enter"){ searchBtn.click(); } });

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
        orgBadge.style.display="flex";
        orgBadge.innerHTML="实时核验：<b>"+esc(o.fullName||"")+(o.creditCode?" · "+esc(o.creditCode):"")+"</b>"+(o.address?" · 📍"+esc(o.address):"");
      } else { orgBadge.style.display="none"; }
      var items=(j.nearest||[]).map(function(x){return {branch:{name:x.name,type:x.type,address:x.address,phone:x.phone},distText:x.distText};});
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
      text+="——数据来源：企查查/天眼查 + 福建海峡银行网点公开信息（共 "+(j.branchCount||"")+" 家），距离仅供参考。";
      return text;
    }
    copyBtn.addEventListener("click",function(){
      var text = lastBackend ? buildShareFromBackend(lastBackend) : buildShareLocal();
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
      orgNameInput.value="";
      orgBadge.style.display="none";
      hero.style.display="none";
      resultList.innerHTML="";
      resultActions.style.display="none";
      resultTip.className="tip";
      resultTip.textContent="请输入机构名称后点击「查询」。";
      orgNameInput.focus();
      toast("已清空，可重新录入");
    });

    // —— 高级设置折叠（仅保留可选的后端代理；定位凭据已内置且不可见） ——
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
      backendStatus.textContent=v?"已保存后端地址，查询将走实时接口（企查查/天眼查）。":"已清除，查询使用本机离线估算。";
    });
  })();
  </script>
</body>
</html>
"""

html = html.replace("__REGION_JS__", REGION_JS)
html = html.replace("__PROV_JS__", PROV_JS)
html = html.replace("__BRANCH_DATA_JS__", BRANCH_DATA_JS)

out = os.path.join(BASE, "index.html")
html = html.replace("__ICON_B64__", "data:image/png;base64," + ICON_B64)
html = html.replace("__MAP_KEY_EXPR__", MAP_KEY_EXPR)
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", out, "bytes:", len(html.encode("utf-8")), "branches:", len(branch_payload["branches"]))
