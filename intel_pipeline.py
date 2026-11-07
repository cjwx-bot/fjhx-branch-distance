# -*- coding: utf-8 -*-
"""资料库校验与注入流水线（前端零 Key · 技能全网检索补齐）。

职责：
1. 校验 intel/org_intel.json 的字段完整性、状态合法性、来源可追溯性、坐标合理性、
   占位符与禁用词；任一不合规即拒绝构建，防止把未经核验的内容带入公开页面。
2. 生成 intel/verify_report.md 校验报告（覆盖统计、逐机构字段状态、来源清单）。
3. 供 build_index.py 调用 load_validated() 取得可直接内联的公开级资料库。

会话侧内部资料库（含自然人姓名）位于工作区根目录 intel/org_intel_local.json，
不在本目录、不参与构建、不随页面发布。
"""
import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
INTEL_PATH = os.path.join(BASE, "intel", "org_intel.json")
REPORT_PATH = os.path.join(BASE, "intel", "verify_report.md")

REQUIRED_FIELDS = [
    "fullName", "orgType", "creditCode", "address", "district", "postcode",
    "phone", "functions", "innerOrgs", "superiors", "subordinates", "leadersStatus"
]
VALID_STATUS = {"verified", "cross", "partial", "conflict", "unverified"}
BANNED_WORDS = [
    "福州分行", "国际业务部", "资金营运中心", "资产负债管理部",
    "比邻星", "苏银豆", "江苏银行", "华创远智公众号",
    "党费收缴", "科技贷", "科创金融"
]
PLACEHOLDERS = ["TODO", "待补充", "XXX", "xxx", "undefined", "NaN", "{{", "}}"]
# 福建省及浙江温州大致经纬度包围盒
LAT_RANGE = (23.4, 28.7)
LNG_RANGE = (116.7, 121.3)


class IntelError(Exception):
    pass


def _walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for x in node:
            for s in _walk_strings(x):
                yield s
    elif isinstance(node, dict):
        for k, v in node.items():
            if k in ("u", "src"):
                continue
            for s in _walk_strings(v):
                yield s


def validate(data):
    errors = []
    if data.get("schema") != "fjhx-org-intel/v1":
        errors.append("schema 版本不匹配")
    orgs = data.get("orgs") or []
    if not orgs:
        errors.append("资料库为空")
    stats = {
        "orgs": len(orgs), "fields": 0, "verified": 0, "cross": 0,
        "partial": 0, "conflict": 0, "unverified": 0, "sources": 0,
        "conflicts": 0, "perOrg": []
    }
    seen_ids = set()
    for org in orgs:
        oid = org.get("id", "")
        name = org.get("name", "")
        if not oid or not name:
            errors.append("机构缺少 id 或 name")
        if oid in seen_ids:
            errors.append("机构 id 重复：%s" % oid)
        seen_ids.add(oid)
        if org.get("visibility") != "public":
            errors.append("%s：visibility 必须为 public（本文件可被注入公开页面）" % name)
        if not org.get("verifiedAt"):
            errors.append("%s：缺少核验日期 verifiedAt" % name)

        geo = org.get("geo") or {}
        lat, lng = geo.get("lat"), geo.get("lng")
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            errors.append("%s：geo 经纬度缺失或类型错误" % name)
        elif not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LNG_RANGE[0] <= lng <= LNG_RANGE[1]):
            errors.append("%s：geo 经纬度超出福建 / 温州范围：%s,%s" % (name, lat, lng))
        for sk in (geo.get("src") or []):
            if sk not in (org.get("sources") or {}):
                errors.append("%s：geo 引用了未登记来源 %s" % (name, sk))

        sources = org.get("sources") or {}
        for sk, sv in sources.items():
            stats["sources"] += 1
            u = sv.get("u", "")
            if not re.match(r"^https?://", u):
                errors.append("%s：来源 %s 的 URL 不可追溯：%s" % (name, sk, u))
            if not sv.get("t") or not sv.get("d"):
                errors.append("%s：来源 %s 缺少标题或日期" % (name, sk))

        fields = org.get("fields") or {}
        cnt = {"verified": 0, "cross": 0, "partial": 0, "conflict": 0, "unverified": 0}
        for fk in REQUIRED_FIELDS:
            if fk not in fields:
                errors.append("%s：缺少字段 %s" % (name, fk))
                continue
            f = fields[fk]
            s = f.get("s")
            v = f.get("v")
            src = f.get("src") or []
            stats["fields"] += 1
            if s not in VALID_STATUS:
                errors.append("%s.%s：状态非法 %s" % (name, fk, s))
                continue
            cnt[s] += 1
            stats[s] += 1
            if s == "unverified":
                if v not in ("", None, []):
                    errors.append("%s.%s：标注未核验却写入了值" % (name, fk))
            elif not v:
                errors.append("%s.%s：状态 %s 但值为空" % (name, fk, s))
            if s in ("verified", "cross", "partial", "conflict") and not src:
                errors.append("%s.%s：已核验字段缺少来源" % (name, fk))
            for sk in src:
                if sk not in sources:
                    errors.append("%s.%s：引用了未登记来源 %s" % (name, fk, sk))

        for conflict in (org.get("conflicts") or []):
            stats["conflicts"] += 1
            if not isinstance(conflict, str) or not conflict.strip():
                errors.append("%s：口径差异说明为空" % name)

        for s in _walk_strings(fields):
            for w in BANNED_WORDS:
                if w in s:
                    errors.append("%s：命中禁用词「%s」" % (name, w))
            for p in PLACEHOLDERS:
                if p in s:
                    errors.append("%s：残留占位符「%s」" % (name, p))

        stats["perOrg"].append({
            "id": oid, "name": name, "verifiedAt": org.get("verifiedAt"),
            "sources": len(sources), "conflicts": len(org.get("conflicts") or []),
            "lat": lat, "lng": lng,
            "fields": cnt, "aliases": len(org.get("aliases") or [])
        })

    if errors:
        raise IntelError("资料库校验未通过（%d 项）：\n  - %s" % (len(errors), "\n  - ".join(errors)))
    return stats


def load_validated(path=INTEL_PATH):
    with io.open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    stats = validate(data)
    return data, stats


def write_report(data, stats, path=REPORT_PATH):
    L = [
        "# 机构公开资料库 · 校验报告",
        "",
        "- 生成方式：%s" % data.get("method", ""),
        "- 生成日期：%s" % data.get("generatedAt", ""),
        "- 收录口径：%s" % (data.get("policy", {}).get("rule", "")),
        "- 分级口径：%s" % (data.get("policy", {}).get("visibility", "")),
        "",
        "## 汇总",
        "",
        "| 指标 | 数值 |",
        "| --- | --- |",
        "| 收录机构 | %d 家 |" % stats["orgs"],
        "| 字段总数 | %d 项 |" % stats["fields"],
        "| 官方直接载明 verified | %d 项 |" % stats["verified"],
        "| 多源交叉 cross | %d 项 |" % stats["cross"],
        "| 原文摘录 partial | %d 项 |" % stats["partial"],
        "| 口径冲突 conflict | %d 项 |" % stats["conflict"],
        "| 未检索到 unverified | %d 项 |" % stats["unverified"],
        "| 证据来源 | %d 条 |" % stats["sources"],
        "| 口径差异说明 | %d 条 |" % stats["conflicts"],
        "",
        "> 未检索到的字段一律留空并在材料中标注「未检索到公开可核验信息」，不以同类机构通行架构填充。",
        "",
        "## 逐机构明细",
        "",
        "| 机构 | 核验日期 | 证据数 | 别名数 | 坐标 | verified/cross/partial/unverified |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for o in stats["perOrg"]:
        c = o["fields"]
        L.append("| %s | %s | %d | %d | %s, %s | %d/%d/%d/%d |" % (
            o["name"], o["verifiedAt"], o["sources"], o["aliases"],
            o["lat"], o["lng"], c["verified"], c["cross"], c["partial"], c["unverified"]))
    L += ["", "## 来源清单", ""]
    for org in data.get("orgs", []):
        L.append("### %s" % org["name"])
        L.append("")
        for sk, sv in (org.get("sources") or {}).items():
            L.append("- `%s` ｜ %s ｜ %s ｜ [%s](%s)" % (sk, sv["k"], sv["d"], sv["t"], sv["u"]))
        L.append("")
        for c in (org.get("conflicts") or []):
            L.append("- 口径差异：%s" % c)
        L.append("")
    L += [
        "## 自动校验项",
        "",
        "字段完整性 / 状态合法性 / 来源 URL 可追溯 / 坐标位于福建与温州包围盒 / 无占位符 / 无禁用词 / visibility=public / 无重复 id，全部通过。",
        "",
        "会话侧内部资料库（含自然人姓名）另存于工作区根目录 `intel/org_intel_local.json`，不参与本构建、不随页面发布。",
        ""
    ]
    with io.open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return path


if __name__ == "__main__":
    d, s = load_validated()
    p = write_report(d, s)
    print("OK: %d orgs, %d fields, %d sources, %d unverified" % (
        s["orgs"], s["fields"], s["sources"], s["unverified"]))
    print("report:", p)
