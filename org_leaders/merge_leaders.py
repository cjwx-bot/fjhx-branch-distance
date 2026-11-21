# -*- coding: utf-8 -*-
"""把 org_leaders/collected.jsonl 中已核验的机关负责人合并进 nearby_data 分片。

口径（强制）：
  - 仅覆盖机关（c==1）且现有负责人（r[8]）为空的记录；不覆盖数据源自带的法定代表人。
  - 写入 r[8]=负责人姓名；来源/时点另存 r[10]（JSON 字符串：{n:姓名,r:职务,t:时点,s:来源}），
    供前端详情卡按「官网现任负责人（截至 YYYY-MM，附来源）」如实标注，与法定代表人口径区分。
  - 名称须精确匹配（去括号别名后仍精确）；不做模糊匹配，避免张冠李戴。
  - 每行记录 asof 时点；前端展示「核验时点」，不宣称"当前现任"（快照会过期）。
  - 合并前先备份 c*.js 到 org_leaders/backup/；幂等可重跑（按 name 覆盖写入）。
"""
import json
import os
import re
import shutil
import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
H5 = os.path.normpath(os.path.join(BASE, ".."))
NEARBY = os.path.join(H5, "nearby_data")
BACKUP = os.path.join(BASE, "backup")
COLL = os.path.join(BASE, "collected.jsonl")


def load_leaders():
    out = {}
    if not os.path.isfile(COLL):
        return out
    with open(COLL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("status") != "verified" or not r.get("leader"):
                continue
            out[r["name"]] = r
    return out


def norm_name(s):
    """去括号别名用于匹配：福州市教育局（中共…）→ 福州市教育局。"""
    return re.sub(r"[（(].*?[)）]", "", s or "").strip()


def main():
    leaders = load_leaders()
    if not leaders:
        raise SystemExit("collected.jsonl 无 verified 记录，未做改动")
    # 建立「原名 + 去括号名」双键索引
    lmap = {}
    for k, v in leaders.items():
        lmap[k] = v
        lmap.setdefault(norm_name(k), v)
    os.makedirs(BACKUP, exist_ok=True)
    today = datetime.date.today().isoformat()
    merged = overwritten = 0
    hit_names = set()
    for i in range(10):
        fp = os.path.join(NEARBY, "c%d.js" % i)
        if not os.path.isfile(fp):
            continue
        # 备份（仅首次）
        bk = os.path.join(BACKUP, "c%d.js.%s" % (i, today))
        if not os.path.isfile(bk):
            shutil.copy2(fp, bk)
        s = open(fp, encoding="utf-8").read()
        head, body = s.split("]=", 1)
        body = body.strip().rstrip(";").strip()
        rows = json.loads(body)
        changed = False
        for r in rows:
            # r=[name,cat,lvl,dist,addr,lat,lng,extra,head,scope,...]
            if len(r) < 9 or r[1] != 1:  # 仅机关
                continue
            info = lmap.get(r[0]) or lmap.get(norm_name(r[0]))
            if not info:
                continue
            old = r[8]
            # 权威核验值优先：即便数据源已有法定代表人也覆盖（数据源工商登记可能错配，
            # 如福州市交通运输局被误标蔡文，实为自然资源局局长）。覆盖仅在本次核验明确时执行。
            # corrected 为显式错配纠正标记，保证幂等重跑时 ov 不丢失（因 old 已被首次写入核验值）。
            corrected = bool(info.get("corrected"))
            if (old and old != info["leader"]) or corrected:
                overwritten += 1
            r[8] = info["leader"]
            if len(r) <= 10:
                r += [""] * (11 - len(r))
            r[10] = json.dumps({
                "n": info["leader"], "r": info.get("role", ""),
                "t": info.get("asof", ""), "s": info.get("src", ""),
                "s2": info.get("src2", ""),
                "ov": corrected or bool(old and old != info["leader"]),
            }, ensure_ascii=False, separators=(",", ":"))
            merged += 1
            hit_names.add(info["name"] if "name" in info else r[0])
            changed = True
        if changed:
            js = head + "]=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n"
            with open(fp, "w", encoding="utf-8", newline="\n") as f:
                f.write(js)
    print("合并完成：写入 %d 条机关负责人（其中覆盖数据源错配 %d 条）" % (merged, overwritten))
    miss = set(leaders) - hit_names
    if miss:
        print("未命中分片（名称不匹配或已有法定代表人）：%d 条" % len(miss))
        for n in sorted(miss)[:20]:
            print("   -", n)
    # 进度留痕
    pp = os.path.join(BASE, "progress.json")
    pr = json.load(open(pp, encoding="utf-8")) if os.path.isfile(pp) else {}
    pr["collected"] = len(leaders)
    pr["merged"] = merged
    pr["updated"] = today
    pr.setdefault("batches", []).append({"date": today, "new": len(leaders), "merged": merged})
    json.dump(pr, open(pp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
