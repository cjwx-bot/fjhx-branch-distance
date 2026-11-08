#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""两阶段编制交互的浏览器端回归测试（Edge CDP，仅用标准库）。

验证链路：录入机构名称 → 命中技能全网检索核验资料库并按真实坐标反馈最近网点 →
点击「编制并查看参阅材料」→ 五阶段进度层（前端零 Key、编制阶段无外部网络请求）→
完成后弹出以已核验事实为主体的最终参阅材料全文；另验证未收录机构经同源后端定位
失败后的如实降级路径，以及注入模拟 /api/geo 响应时的实时真实定位与结果区分度。
"""
import base64
import io
import json
import os
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request
import http.server
import socket
import tempfile
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
sys.path.insert(0, ROOT)
from html2pdf_cdp_edge import WS, cdp  # noqa: E402  复用 stdlib WebSocket 客户端

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
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"}, sid=sid)
    if r and "result" in r and "data" in r["result"]:
        with open(path, "wb") as f:
            f.write(base64.b64decode(r["result"]["data"]))
        return True
    return False


def main():
    os.chdir(BASE)
    CDP_PORT, HTTP_PORT = free_port(), free_port()
    URL = "http://127.0.0.1:%d/index.html" % HTTP_PORT
    srv = Server(("127.0.0.1", HTTP_PORT), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    # 独立临时配置目录：避免复用残留实例导致导航失效
    ud = tempfile.mkdtemp(prefix="fjhx_cdp_")
    proc = subprocess.Popen(
        [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--remote-debugging-port=%d" % CDP_PORT, "--user-data-dir=" + ud],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ws = None
    try:
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
        # 微信端为手机竖屏视口，按 390x844 CSS px 复现
        cdp(ws, "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True}, sid=sid)

        def ev(expr):
            r = cdp(ws, "Runtime.evaluate",
                    {"expression": expr, "returnByValue": True}, sid=sid)
            if not r or "error" in r:
                return {"__error": str(r)}
            res = r.get("result", {})
            if "exceptionDetails" in res:
                return {"__exception": str(res["exceptionDetails"])[:300]}
            return res.get("result", {}).get("value")

        for _ in range(40):
            if ev("document.readyState") == "complete":
                break
            time.sleep(0.25)

        checks = []

        def ck(name, cond, extra=""):
            checks.append((name, bool(cond), extra))
            print("  %-32s %s %s" % (name, "通过" if cond else "失败", extra))

        ev("window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(String(e.message));});")
        print("\n浏览器端两阶段编制实跑：")
        ck("页面加载", ev("document.title.indexOf('最近网点')>=0"), str(ev("document.title")))

        # ① 查询阶段：录入机构名称并点击查询
        ev("document.getElementById('orgName').value='福州市民族与宗教事务局';"
           "document.getElementById('searchBtn').click();true")
        time.sleep(0.8)   # 资料库命中为同步本地计算，不发起定位请求
        hero = ev("document.getElementById('hero').innerText") or ""
        badge = ev("document.getElementById('orgBadge').innerText") or ""
        ck("查询反馈最近网点", "福建海峡银行" in hero, hero.replace("\n", " ")[:70])
        ck("按资料库真实坐标测算", "福州华林支行" in hero, hero.replace("\n", " ")[:70])
        ck("命中技能核验资料库", "已命中技能全网检索核验资料库" in badge, badge[:90])
        ck("查询阶段材料为待编制", ev("document.getElementById('briefPill').textContent") == "待编制")
        ck("查询阶段未预生成全文",
           ev("document.getElementById('briefPreview').innerHTML.length") == 0)

        # ② 点击参阅材料按钮：进度层应出现
        ev("document.getElementById('viewBrief').click();true")
        time.sleep(1.2)
        ck("进度层已显示", ev("document.getElementById('progMask').classList.contains('show')") is True)
        ck("阶段清单为 5 项", ev("document.getElementById('progStages').getElementsByTagName('li').length") == 5)
        ck("五阶段均在可视区（手机视口）", ev("(function(){var sc=document.querySelector('#progSheet .prog__scroll').getBoundingClientRect(),"
           "ls=document.getElementById('progStages').getElementsByTagName('li');"
           "return ls.length===5 && ls[4].getBoundingClientRect().bottom<=sc.bottom+1;})()") is True)
        ck("取消按钮常驻可见", ev("(function(){var sh=document.getElementById('progSheet').getBoundingClientRect(),"
           "b=document.getElementById('cancelProg').getBoundingClientRect();"
           "return b.height>0 && b.bottom<=sh.bottom+1;})()") is True)
        pct_mid = ev("document.getElementById('progPct').textContent")
        ck("进度百分比已推进", pct_mid is not None and pct_mid not in ("0%", None), str(pct_mid))
        shot(ws, sid, os.path.join(ROOT, "_pipeline_progress.png"))

        # ③ 完成后应弹出最终材料
        done = False
        for _ in range(40):
            time.sleep(0.5)
            if ev("document.getElementById('briefMask').classList.contains('show')") is True:
                done = True
                break
        ck("编制完成后弹出全文", done)
        ck("进度层已关闭", ev("document.getElementById('progMask').classList.contains('show')") is False)
        info = ev("(function(){var d=document.getElementById('briefPreview');"
                  "return {len:d.innerHTML.length, t:d.innerText, h:d.innerHTML};})()")
        if isinstance(info, dict):
            body = info.get("t", "") or ""
            html_body = info.get("h", "") or ""
            ck("全文字数达标", info.get("len", 0) > 15000, str(info.get("len")))
            ck("含官方核验直达入口", "（七）官方核验直达入口" in body)
            ck("含资料库命中标注", "技能全网检索核验资料库" in body and "已命中" in body)
            ck("含已核验机构事实", "113501007380396651" in body and "福飞路井尾5号" in body)
            ck("含真实内设机构", "宗教事务三处" in body and "政策法规处" in body)
            ck("含真实下属单位", "福州市民族宗教事务服务中心" in body)
            ck("含证据索引与官方来源", "（八）全网检索证据索引" in body and "fuzhou.gov.cn" in html_body)
            ck("含核验状态与未核验标注", "官方页面直接载明" in body and "未检索到公开可核验信息" in body)
            ck("无旧在线复核口径", "页面在线复核（编制时）" not in body and "腾讯位置服务地点建议接口" not in body)
            ck("不含内部级领导姓名", "张清泉" not in body)
            ck("含前端零 Key 声明", "前端零 Key" in body)
            ck("旧零授权口径已清除", "零 API 授权" not in body)
            ck("含密级标识", "行内参考 请勿外传" in body)
            ck("状态改为已生成", ev("document.getElementById('briefPill').textContent") == "已生成")
            print("  资料库命中结果：已以公开渠道核验事实生成第三章并附证据索引")
        else:
            ck("全文内容读取", False, str(info)[:150])
        shot(ws, sid, os.path.join(ROOT, "_pipeline_final.png"))

        # ④ 未收录机构：如实降级，不以模板内容冒充核验结果
        ev("document.getElementById('closeBrief').click();"
           "document.getElementById('refreshBtn').click();"
           "document.getElementById('orgName').value='鼓楼区某未收录单位';"
           "document.getElementById('searchBtn').click();true")
        time.sleep(1.2)   # 同源 /api/geo 返回 404 后经 catch 降级
        badge2 = ev("document.getElementById('orgBadge').innerText") or ""
        hero2 = ev("document.getElementById('hero').innerText") or ""
        ck("未收录机构如实提示", "资料库未收录" in badge2, badge2[:80])
        ck("未收录机构仍反馈近似网点", "福建海峡银行" in hero2, hero2.replace("\n", " ")[:70])
        ck("无后端时如实标注降级原因", "实时定位服务不可用" in badge2 or "行政区划中心近似" in badge2)

        # ⑤ 注入模拟 /api/geo 响应：验证实时真实定位路径与结果区分度
        fixtures = {
            "福州市鼓楼区教育局": {"lat": 26.0912, "lng": 119.2981},
            "福建省教育厅": {"lat": 26.0755, "lng": 119.3075}
        }
        ev("window.__geoFixtures=" + json.dumps(fixtures, ensure_ascii=False) + ";" +
           "window.fetch=function(u){return Promise.resolve({ok:true,json:function(){" +
           "var m=/name=([^&]+)/.exec(String(u));var n=m?decodeURIComponent(m[1]):'';" +
           "var c=window.__geoFixtures[n];" +
           "return Promise.resolve(c?{found:true,query:n,geo:{lat:c.lat,lng:c.lng,title:n," +
           "address:'福州市公开办公地址',province:'福建省',city:'福州市',district:'鼓楼区'," +
           "source:'amap-place-text'},provider:'高德地图开放平台（Web服务 API）'," +
           "coordSystem:'GCJ-02',verifiedAt:'2026-11-07'}" +
           ":{found:false,reason:'no-poi',message:'公开地图未匹配'});}});};true")

        def qhero(nm):
            ev("document.getElementById('refreshBtn').click();" +
               "document.getElementById('orgName').value=" + json.dumps(nm, ensure_ascii=False) + ";" +
               "document.getElementById('searchBtn').click();true")
            time.sleep(0.6)
            return ((ev("document.getElementById('hero').innerText") or "").replace("\n", " "),
                    ev("document.getElementById('orgBadge').innerText") or "")

        hg1, bg1 = qhero("福州市鼓楼区教育局")
        hg2, bg2x = qhero("福建省教育厅")
        ck("实时定位路径命中", "已取得实时真实坐标" in bg1 and "高德地图" in bg1, bg1[:90])
        ck("实时定位仍反馈最近网点", "福建海峡银行" in hg1, hg1[:70])
        ck("同区两机构结果不再雷同", hg1 != hg2, hg1[:45] + " | " + hg2[:45])

        errs = ev("window.__errs") or []
        ck("无运行时脚本错误", len(errs) == 0, str(errs)[:160])

        failed = [n for n, ok, _ in checks if not ok]
        print("\n结论：%d/%d 项通过%s" % (len(checks) - len(failed), len(checks),
              "；失败：" + "、".join(failed) if failed else ""))
        if failed:
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
            srv.shutdown()
        except Exception:
            pass
        try:
            shutil.rmtree(ud, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
