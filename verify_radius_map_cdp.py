#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""半径查询「地图视图 + 街道底图」浏览器端回归（Edge CDP，仅用标准库）。

覆盖：切换模式 → 模糊录入网点并点选 → 录入半径 → 查询后默认进入地图界面 →
同源 /api/tiles 街道底图瓦片加载 → 类别着色图钉 / 同址聚合 → 点击图钉看详情 →
类别筛选联动 → 地图/清单切换 → 放大缩放 → 街道底图开关 → 底图不可达时如实降级 →
无 JS 异常，并输出 390x844 手机视口截图。

脚本自包含：自行启动本地 Node 服务提供 /api/tiles，并把测试页的 TILE_BASE
指向该本地服务；正式 index.html 不被修改，临时测试页运行后删除。
"""
import base64
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request
import http.server
import socket
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
sys.path.insert(0, ROOT)
from html2pdf_cdp_edge import WS, cdp  # noqa: E402

EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"


def free_port():
    sk = socket.socket()
    sk.bind(("127.0.0.1", 0))
    port = sk.getsockname()[1]
    sk.close()
    return port


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class Server(socketserver.TCPServer):
    allow_reuse_address = True


def shot(ws, sid, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False}, sid=sid)
    if r and "result" in r and "data" in r["result"]:
        with open(path, "wb") as f:
            f.write(base64.b64decode(r["result"]["data"]))
        return True
    return False


def main():
    os.chdir(BASE)
    CDP_PORT, HTTP_PORT, NODE_PORT = free_port(), free_port(), free_port()
    test_page = os.path.join(BASE, "_test_tile_index.html")
    fail_page = os.path.join(BASE, "_test_tile_fail.html")

    # 本地 Node 服务：提供同源 /api/tiles 瓦片代理（上游为高德公开瓦片，无 Key）
    env = dict(os.environ)
    env["PORT"] = str(NODE_PORT)
    node = subprocess.Popen(["node", "server.js"], cwd=BASE, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # 测试页：仅把瓦片代理 URL 指向本地 Node 服务，其余与正式构建逐字节一致
    src = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
    tile_url = "http://127.0.0.1:%d/api/tiles?" % NODE_PORT
    patched = re.sub(r'var TILE_BASE = "[^"]*"', 'var TILE_BASE = "' + tile_url + '"', src, count=1)
    assert patched != src, "未能把瓦片代理注入测试页"
    open(test_page, "w", encoding="utf-8").write(patched)
    open(fail_page, "w", encoding="utf-8").write(
        patched.replace(tile_url, "http://127.0.0.1:1/api/tiles?"))

    URL = "http://127.0.0.1:%d/_test_tile_index.html" % HTTP_PORT
    srv = Server(("127.0.0.1", HTTP_PORT), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    ud = tempfile.mkdtemp(prefix="fjhx_map_cdp_")
    proc = subprocess.Popen(
        [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--remote-debugging-port=%d" % CDP_PORT, "--user-data-dir=" + ud],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ws = None
    try:
        nop = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(25):
            try:
                nop.open("http://127.0.0.1:%d/api/health" % NODE_PORT, timeout=2).read()
                break
            except Exception:
                time.sleep(0.4)

        ws_url = None
        for _ in range(50):
            try:
                txt = urllib.request.urlopen(
                    "http://127.0.0.1:%d/json/version" % CDP_PORT, timeout=2).read().decode()
                ws_url = json.loads(txt)["webSocketDebuggerUrl"]
                break
            except Exception:
                time.sleep(0.4)
        assert ws_url, "DevTools 端点不可用"
        ws = WS(ws_url)
        t = cdp(ws, "Target.createTarget", {"url": URL})
        sid = cdp(ws, "Target.attachToTarget",
                  {"targetId": t["result"]["targetId"], "flatten": True})["result"]["sessionId"]
        cdp(ws, "Page.enable", sid=sid)
        cdp(ws, "Runtime.enable", sid=sid)
        cdp(ws, "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True}, sid=sid)

        def ev(expr):
            r = cdp(ws, "Runtime.evaluate",
                    {"expression": expr, "returnByValue": True, "awaitPromise": True}, sid=sid)
            if not r or "error" in r:
                return {"__error": str(r)}
            res = r.get("result", {})
            if "exceptionDetails" in res:
                return {"__exception": str(res["exceptionDetails"])[:400]}
            return res.get("result", {}).get("value")

        def wait_ready():
            for _ in range(40):
                if ev("document.readyState") == "complete":
                    return True
                time.sleep(0.25)
            return False

        def run_query():
            """切到半径模式 → 联想点选网点 → 3km 查询 → 等待地图出现。"""
            ev("document.getElementById('tabRadius').click();true")
            ev("var b=document.getElementById('branchName');b.value='鼓楼';"
               "b.dispatchEvent(new Event('input',{bubbles:true}));true")
            time.sleep(0.5)
            ev("(function(){var e=document.querySelector('#branchSug .sug-item');"
               "e.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,cancelable:true}));return true})()")
            ev("document.getElementById('radiusKm').value='3';"
               "document.getElementById('radiusBtn').click();true")
            for _ in range(60):
                time.sleep(0.35)
                if ev("document.getElementById('radMapWrap').style.display!=='none' && "
                      "document.querySelectorAll('#radPins .rad-pin,#radPins .rad-cluster').length>0") is True:
                    return True
            return False

        checks = []

        def ck(name, cond, extra=""):
            checks.append((name, bool(cond)))
            print("  %-34s %s %s" % (name, "通过" if cond else "失败", extra))

        ev("window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(String(e.message));});true")
        print("\n半径查询地图 + 街道底图浏览器实跑：")
        ck("页面加载", wait_ready() and ev("document.title.indexOf('最近网点')>=0") is True)
        ck("查询后默认进入地图界面", run_query(),
           str(ev("document.getElementById('radSummary').innerText"))[:80])

        # —— 街道底图瓦片（同源 /api/tiles 代理）——
        tile_ok = 0
        for _ in range(40):
            time.sleep(0.3)
            tile_ok = ev("document.querySelectorAll('#radTiles img.ok').length") or 0
            if tile_ok >= 3:
                break
        ck("街道底图瓦片加载成功", tile_ok >= 3, "成功 %d 张" % tile_ok)
        ck("瓦片层与彩色图钉共存",
           ev("document.getElementById('radTiles').style.display==='block' && "
              "document.querySelectorAll('#radPins [data-k]').length>0") is True)
        ck("底图 HUD 标注同源代理",
           "同源代理" in str(ev("document.getElementById('radMapHead').innerText")))
        ck("页面无地图上游域名", ev("document.documentElement.innerHTML.indexOf('autonavi.com')<0") is True)

        pins = ev("document.querySelectorAll('#radPins .rad-pin').length") or 0
        clusters = ev("document.querySelectorAll('#radPins .rad-cluster').length") or 0
        colors = ev("(function(){var o={};document.querySelectorAll('#radPins path[fill],#radPins circle[fill]')"
                    ".forEach(function(e){var c=e.getAttribute('fill');o[c]=(o[c]||0)+1});return o})()")
        ck("类别小图钉已标注", pins > 0, "单点 %d 个" % pins)
        ck("同址聚合点已生成", clusters > 0, "聚合 %d 个" % clusters)
        ck("至少三种类别颜色", isinstance(colors, dict) and
           len([c for c in colors if c in ("#e05345", "#1a5bb8", "#1f9d57")]) >= 3,
           str(colors)[:110])
        # 六类互斥统计：标签齐全，且六类数字加总等于「合计主体」（去重无重复计数）
        stat = ev("(function(){var it=document.querySelectorAll('#radStat .rad-stat__item');"
                  "var o={};it.forEach(function(e){o[e.querySelector('.rad-stat__t').textContent]="
                  "parseInt(e.querySelector('.rad-stat__n').textContent,10)});return o})()")
        labels = ("合计主体", "机关", "事业单位", "公办学校", "民办学校", "医院", "宗教组织")
        ck("六类主体统计标签齐全", isinstance(stat, dict) and all(k in stat for k in labels),
           str(stat)[:110])
        if isinstance(stat, dict) and all(k in stat for k in labels):
            s = sum(stat[k] for k in labels[1:])
            ck("互斥去重加总等于合计", s == stat["合计主体"],
               "%d = %d" % (s, stat["合计主体"]))
        ck("半径圈与圆心大图钉", ev("document.querySelectorAll('#radG circle.rad-ring').length===1 && "
                                  "document.querySelectorAll('#radPins .rad-center-pin').length===1") is True)
        ck("地图 HUD 口径完整",
           "GCJ-02" in str(ev("document.getElementById('radOvl').textContent")) and
           "街道底图 + 等距投影" in str(ev("document.getElementById('radMapHead').innerText")))

        # —— 点击图钉弹出「单位主要信息」卡 ——
        ev("(function(){var e=document.querySelector('#radPins [data-k]');"
           "e.dispatchEvent(new MouseEvent('click',{bubbles:true}));return true})()")
        info = str(ev("document.getElementById('radPinInfo').innerText"))
        ck("点击图钉显示单位详情/聚合明细",
           ("登记地址" in info or "点击图钉已弹出" in info), info.replace("\n", " ")[:90])
        ck("点击图钉弹出单位信息卡",
           ev("document.getElementById('pinModal').classList.contains('on')") is True)
        card = str(ev("document.getElementById('pinCard').innerText"))
        # 首个图钉可能是聚合点，此时卡片先列多家单位；点其中一家后再校验主要字段
        pi_cnt = ev("document.querySelectorAll('#pinCard [data-pi]').length") or 0
        if pi_cnt > 0:
            ck("聚合点先列多家单位", "该位置共" in card, card.replace("\n", " ")[:80])
            ev("document.querySelector('#pinCard [data-pi]').click();true")
            card = str(ev("document.getElementById('pinCard').innerText"))
        ck("信息卡含单位主要字段",
           all(k in card for k in ("单位主要信息", "机构类别", "行政层级", "所属区划",
                                   "直线距离", "登记地址", "坐标")),
           card.replace("\n", " ")[:100])
        ck("信息卡含单位负责人行",
           "单位负责人" in card and ("公开登记法定代表人" in card or "未列示" in card),
           card.replace("\n", " ")[:120])
        # 业务范围覆盖率约 47%，扫描前若干单点图钉，至少找到一张含「业务范围」的卡
        scope_seen = "业务范围" in card
        if not scope_seen:
            keys = ev("Array.prototype.slice.call(document.querySelectorAll('#radPins [data-k]')).slice(0,14).map(function(e){return e.getAttribute('data-k')})") or []
            for k in keys:
                ev("(function(){var e=document.querySelector('#radPins [data-k=\\\"%s\\\"]');"
                   "if(e)e.dispatchEvent(new MouseEvent('click',{bubbles:true}));return true})()" % k)
                if ev("document.querySelectorAll('#pinCard [data-pi]').length") > 0:
                    ev("document.querySelector('#pinCard [data-pi]').click();true")
                c2 = str(ev("document.getElementById('pinCard').innerText"))
                if "业务范围" in c2:
                    scope_seen = True
                    card = c2
                    break
                ev("document.querySelector('#pinCard [data-close]').click();true")
        ck("至少一张信息卡含业务范围(可折叠)", scope_seen,
           card.replace("\n", " ")[:120])
        ck("信息卡可关闭", (ev("document.querySelector('#pinCard [data-close]').click();"
                             "!document.getElementById('pinModal').classList.contains('on')") is True))
        # 再点一个图钉，截图展示单位主要信息卡（若为聚合点则进一步点入某单位）
        ev("(function(){var e=document.querySelector('#radPins [data-k]');"
           "e.dispatchEvent(new MouseEvent('click',{bubbles:true}));return true})()")
        time.sleep(0.2)
        if ev("document.querySelectorAll('#pinCard [data-pi]').length") > 0:
            ev("document.querySelector('#pinCard [data-pi]').click();true")
        time.sleep(0.3)
        shot(ws, sid, os.path.join(BASE, "_pin_detail_preview.png"))
        ev("document.querySelector('#pinCard [data-close]').click();true")

        ev("document.querySelector('#radFilter .rad-chip[data-cat=\"1\"]').click();true")
        time.sleep(0.3)
        only_red = ev("(function(){var s=new Set();document.querySelectorAll('#radPins path[fill]')"
                      ".forEach(function(e){s.add(e.getAttribute('fill'))});"
                      "document.querySelectorAll('#radPins circle[fill]')"
                      ".forEach(function(e){s.add(e.getAttribute('fill'))});return Array.from(s)})()")
        ck("类别筛选联动地图", isinstance(only_red, list) and "#e05345" in only_red and "#1f9d57" not in only_red,
           str(only_red)[:80])
        ev("document.querySelector('#radFilter .rad-chip[data-cat=\"0\"]').click();true")
        time.sleep(0.3)

        # —— 机关官网现任负责人：带核验时点 + 来源链接（全网检索补充）——
        # 3km 内已补机关为福建省财政厅（郑震，核验时点2026-11）。用关键词精确隔离。
        ev("(function(){var k=document.getElementById('radKeyword');k.value='福建省财政厅';"
           "k.dispatchEvent(new Event('input',{bubbles:true}));return true})()")
        time.sleep(0.8)
        ev("document.getElementById('radViewList').click();true")
        time.sleep(0.3)
        list_txt = str(ev("document.getElementById('radList').innerText"))
        ck("机关负责人已补进清单(全网核验)", "郑震" in list_txt,
           list_txt.replace("\n", " ")[:120])
        ev("document.getElementById('radViewMap').click();true")
        time.sleep(0.3)
        ev("(function(){var e=document.querySelector('#radPins [data-k]');"
           "if(e)e.dispatchEvent(new MouseEvent('click',{bubbles:true}));return true})()")
        time.sleep(0.2)
        if ev("document.querySelectorAll('#pinCard [data-pi]').length") > 0:
            ev("(function(){var ls=document.querySelectorAll('#pinCard [data-pi]');"
               "for(var i=0;i<ls.length;i++){if(ls[i].innerText.indexOf('财政厅')>=0){ls[i].click();break;}}"
               "return true})()")
            time.sleep(0.2)
        card2 = str(ev("document.getElementById('pinCard').innerText"))
        ck("机关卡片标注官网现任+核验时点", "官网现任负责人" in card2 and "核验时点" in card2,
           card2.replace("\n", " ")[:130])
        ck("机关卡片含来源链接", ev("document.querySelectorAll('#pinCard a.pin-card__src').length") > 0,
           str(ev("document.querySelectorAll('#pinCard a.pin-card__src').length")))
        ev("document.querySelector('#pinCard [data-close]').click();true")
        # 清空关键词恢复
        ev("(function(){var k=document.getElementById('radKeyword');k.value='';"
           "k.dispatchEvent(new Event('input',{bubbles:true}));return true})()")
        time.sleep(0.6)

        r_before = ev("parseFloat(document.querySelector('#radG circle.rad-ring').getAttribute('r'))")
        ev("document.getElementById('radMapZoomIn').click();true")
        r_after = ev("parseFloat(document.querySelector('#radG circle.rad-ring').getAttribute('r'))")
        ck("放大按钮生效", isinstance(r_before, (int, float)) and r_after > r_before,
           "%s → %s" % (r_before, r_after))
        ev("document.getElementById('radMapReset').click();true")

        # 街道底图图层开关
        ev("document.getElementById('radMapLayer').click();true")
        ck("街道底图可关闭",
           ev("document.getElementById('radTiles').style.display==='none'") is True and
           "已关闭" in str(ev("document.getElementById('radMapHead').innerText")))
        ev("document.getElementById('radMapLayer').click();true")
        tile_ok2 = 0
        for _ in range(40):
            time.sleep(0.3)
            tile_ok2 = ev("document.querySelectorAll('#radTiles img.ok').length") or 0
            if tile_ok2 >= 3:
                break
        ck("街道底图可重新开启", tile_ok2 >= 3, "成功 %d 张" % tile_ok2)

        ev("document.getElementById('radViewList').click();true")
        ck("清单视图可切回",
           ev("document.getElementById('radList').style.display==='flex' && "
              "document.getElementById('radMapWrap').style.display==='none'") is True,
           "清单条目 %s" % ev("document.querySelectorAll('#radList .rad-item').length"))
        ev("document.getElementById('radViewMap').click();true")
        ck("地图视图可再切回",
           ev("document.getElementById('radMapWrap').style.display!=='none' && "
              "document.querySelectorAll('#radPins [data-k]').length>0") is True)
        ck("查询后视口自动移到地图", (ev("window.scrollY") or 0) > 0,
           "scrollY=%s" % ev("window.scrollY"))

        ev("document.getElementById('radMapWrap').scrollIntoView({block:'start'});true")
        time.sleep(0.6)
        shot(ws, sid, os.path.join(BASE, "_radius_map_preview.png"))
        errs = ev("window.__errs") or []
        ck("无页面 JS 异常", isinstance(errs, list) and len(errs) == 0, str(errs)[:120])

        # —— 降级路径：瓦片代理不可达时如实标注并退回零依赖点位图 ——
        cdp(ws, "Page.navigate", {"url": "http://127.0.0.1:%d/_test_tile_fail.html" % HTTP_PORT}, sid=sid)
        for _ in range(40):
            time.sleep(0.25)
            if ev("location.href.indexOf('_test_tile_fail')>=0 && document.readyState==='complete'") is True:
                break
        ev("window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(String(e.message));});true")
        ck("降级页查询仍可用", run_query())
        degraded = False
        for _ in range(30):
            time.sleep(0.3)
            if "街道底图未就绪" in str(ev("document.getElementById('radMapHead').innerText")):
                degraded = True
                break
        ck("底图不可用时如实降级", degraded and
           ev("document.getElementById('radTiles').style.display==='none'") is True and
           ev("document.querySelectorAll('#radPins [data-k]').length>0") is True,
           str(ev("document.getElementById('radMapHead').innerText")).replace("\n", " ")[:90])

        bad = [n for n, ok in checks if not ok]
        print("\n结果：%d/%d 项通过；截图 _radius_map_preview.png" % (len(checks) - len(bad), len(checks)))
        if bad:
            print("失败项：", ", ".join(bad))
            sys.exit(1)
    finally:
        try:
            if ws:
                ws.close()
        except Exception:
            pass
        try:
            proc.terminate()
        except Exception:
            pass
        try:
            node.terminate()
        except Exception:
            pass
        try:
            srv.shutdown()
        except Exception:
            pass
        for p in (test_page, fail_page):
            try:
                os.remove(p)
            except Exception:
                pass


if __name__ == "__main__":
    main()
