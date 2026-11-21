# -*- coding: utf-8 -*-
"""通用：把某批次负责人写回资料库 DATA 机关表（本地 v7 为基线）。

用法：
  python lib_writeback.py <batch_add.jsonl> <输出xlsx>
口径同 lib_writeback_batch3e.py：公司名称精确+去括号兜底匹配，写法定代表人 + 5 留痕列。
"""
import json
import os
import re
import sys

import openpyxl

BASE = os.path.dirname(os.path.abspath(__file__))
H5 = os.path.normpath(os.path.join(BASE, ".."))
DATA_SRC = os.path.normpath(os.path.join(H5, "..", "data_library_src", "福建浙江温州机关_整合_行政层级_经纬度.xlsx"))


def norm_name(s):
    return re.sub(r"[（(].*?[)）]", "", s or "").strip()


def load_batches(fp):
    rows = {}
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
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    hdr = [c.value for c in ws[1]]
    ci = {h: i for i, h in enumerate(hdr)}
    idx = {}
    for row in ws.iter_rows(min_row=2):
        name = row[ci["公司名称"]].value
        if name is None:
            continue
        idx.setdefault(name, row[0].row)
        idx.setdefault(norm_name(name), row[0].row)
    wb.close()
    return idx


def main():
    batch_fp, out_fp = sys.argv[1], sys.argv[2]
    batches = load_batches(batch_fp)
    if not batches:
        raise SystemExit("批次留痕无 verified 机关记录")
    idx = build_index(DATA_SRC)
    if not idx:
        raise SystemExit("机关表索引为空")
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
    wb.save(out_fp)
    wb.close()
    print(f"写回完成：匹配 {len(matched)} 条，未匹配 {len(missed)} 条")
    if missed:
        print("未匹配：")
        for n in missed:
            print("   -", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
