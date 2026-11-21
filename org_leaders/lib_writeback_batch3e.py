# -*- coding: utf-8 -*-
"""批次3e：将 collected.jsonl 已核验的机关负责人同步写回资料库 DATA 机关表。

口径：
  - 以本地 v7 机关表（data_library_src/福建浙江温州机关_整合_行政层级_经纬度.xlsx）为写回基线；
  - 按「公司名称精确 + 去括号名兜底」匹配 39 条批次3e（闽清 22 + 永泰 17）；
  - 写入字段：法定代表人（权威核验值）+ 5 个留痕列
    （核验负责人(官网现任)/核验时点/核验来源/核验职务/核验说明）；
  - 只写机关行（保留既有结构，不改动其他列）；与 merge_leaders.py 口径一致——权威核验值覆盖数据源错配；
  - 输出：写回 xlsx（默认 机关表_写回前_20261118.xlsx），供 upload_drive_file.py 覆盖上传回 node。
"""
import json
import os
import re
import sys

import openpyxl

BASE = os.path.dirname(os.path.abspath(__file__))
H5 = os.path.normpath(os.path.join(BASE, ".."))
DATA_SRC = os.path.normpath(os.path.join(H5, "..", "data_library_src", "福建浙江温州机关_整合_行政层级_经纬度.xlsx"))
OUT = os.path.join(BASE, "机关表_写回前_20261118.xlsx")
BATCH3E = os.path.join(BASE, "batch3e_add.jsonl")


def norm_name(s):
    return re.sub(r"[（(].*?[)）]", "", s or "").strip()


def load_batches():
    """只取批次3e 留痕（39 条），按 name → verified 记录。"""
    rows = {}
    fp = BATCH3E
    if not os.path.isfile(fp):
        return rows
    for line in open(fp, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("status") != "verified" or not r.get("leader"):
            continue
        rows[r["name"]] = r
    return rows


def build_index(path):
    """公司名称精确 + 去括号名 → 表行实际 Excel 行号索引。"""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    hdr = [c.value for c in ws[1]]
    c_i = {h: i for i, h in enumerate(hdr)}
    idx = {}
    for row in ws.iter_rows(min_row=2):
        name = row[c_i["公司名称"]].value
        if name is None:
            continue
        idx.setdefault(name, row[0].row)  # row[0].row 为实际 Excel 行号
        idx.setdefault(norm_name(name), row[0].row)
    wb.close()
    return idx


def main():
    batches = load_batches()
    if not batches:
        raise SystemExit("collected.jsonl 无 verified 机关记录，未做写回")
    idx = build_index(DATA_SRC)
    if not idx:
        raise SystemExit("机关表索引为空")

    # 读表头定位列
    wb = openpyxl.load_workbook(DATA_SRC, data_only=True)
    ws = wb.active
    hdr = [c.value for c in ws[1]]
    ci = {h: i for i, h in enumerate(hdr)}

    matched, missed = [], []
    for name, info in batches.items():
        row_no = idx.get(name) or idx.get(norm_name(name))
        if row_no is None:
            missed.append(name)
            continue
        vals = {
            "法定代表人": info["leader"],
            "核验负责人(官网现任)": info["leader"],
            "核验时点": info.get("asof", ""),
            "核验来源": info.get("src", ""),
            "核验职务": info.get("role", ""),
            "核验说明": info.get("note", ""),
        }
        for h, v in vals.items():
            if h in ci:
                ws.cell(row=row_no, column=ci[h] + 1, value=v)
        matched.append(name)
    wb.save(OUT)
    wb.close()
    print(f"写回完成：匹配 {len(matched)} 条，未匹配 {len(missed)} 条")
    if missed:
        print("未匹配：")
        for n in missed:
            print("   -", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
