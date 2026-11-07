#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""两阶段编制交互的浏览器端回归测试（Edge CDP，仅用标准库）。

验证链路：录入机构名称 → 查询网点 → 点击「编制并查看参阅材料」→
进度层出现并按阶段推进 → 完成后弹出最终参阅材料全文。
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
        time.sleep(4.5)
        hero = ev("document.getElementById('hero').innerText") or ""
        ck("查询反馈最近网点", "福建海峡银行" in hero, hero.replace("\n", " ")[:70])
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
                  "return {len:d.innerHTML.length, t:d.innerText};})()")
        if isinstance(info, dict):
            body = info.get("t", "") or ""
            ck("全文字数达标", info.get("len", 0) > 15000, str(info.get("len")))
            ck("含官方核验直达入口", "（七）官方核验直达入口" in body)
            ck("含在线复核字段", "页面在线复核（编制时）" in body)
            ck("含在线复核区划代码", "350102" in body or "未取得结果" in body)
            ck("含密级标识", "行内参考 请勿外传" in body)
            ck("状态改为已生成", ev("document.getElementById('briefPill').textContent") == "已生成")
            print("  在线复核结果：", "成功取得行政区划数据" if "350102" in body else "未取得，已如实降级")
        else:
            ck("全文内容读取", False, str(info)[:150])
        shot(ws, sid, os.path.join(ROOT, "_pipeline_final.png"))

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
