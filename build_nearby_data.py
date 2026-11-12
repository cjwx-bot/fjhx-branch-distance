# -*- coding: utf-8 -*-
"""由资料库 DATA 文件夹四份清单生成「网点辐射查询」前端分片数据。

数据来源（用户资料库 /space/d/Df67QzHHevCHIsl4LBor7C）：
  1. 福建浙江温州机关_整合_行政层级_经纬度.xlsx            → 机关清单
  2. 福建浙江温州事业单位_整合_行政层级_经纬度_20261110.xlsx → 事业单位清单
  3. 福建温州公办民办非企业学校_整合_经纬度_行政层级_20261110.xlsx → 学校清单
  4. 福建海峡银行_91.xlsx                                  → 仅作网点总数核对，圆心取 server/data/branches.json

口径：
  - 三份清单「经纬度」列均为「经度,纬度」GCJ-02；机关/学校另有独立「经度」「纬度」列，优先取独立列。
  - 只提取业务所需最小字段，不落法定代表人、联系电话、统一社会信用代码等到前端页面。
  - 跨表重复主体按统一社会信用代码（缺失时按 名称+市+区县）合并，类别位或叠加。
  - 按地市切片，前端依查询圆外接矩形与市域包围盒相交情况按需加载，避免一次性下载全量数据。
"""
import json
import math
import os
import re
import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(BASE, "..", "data_library_src"))
OUT = os.path.join(BASE, "nearby_data")

CITY_ORDER = ["福州市", "厦门市", "泉州市", "漳州市", "莆田市",
              "宁德市", "龙岩市", "三明市", "南平市", "温州市"]
CITY_ALIAS = {
    "福州": "福州市", "厦门": "厦门市", "泉州": "泉州市", "漳州": "漳州市",
    "莆田": "莆田市", "宁德": "宁德市", "龙岩": "龙岩市", "三明": "三明市",
    "南平": "南平市", "温州": "温州市", "平潭": "福州市",
}
# 市中心（用于把「市=福建」等异常值按最近中心归档，仅作兜底）
CITY_CENTER = {
    "福州市": (26.074, 119.296), "厦门市": (24.480, 118.089),
    "泉州市": (24.874, 118.676), "漳州市": (24.513, 117.647),
    "莆田市": (25.454, 119.008), "宁德市": (26.665, 119.548),
    "龙岩市": (25.091, 117.030), "三明市": (26.264, 117.639),
    "南平市": (26.642, 118.178), "温州市": (27.994, 120.699),
}
CAT_BIT = {"机关": 1, "事业单位": 2, "学校": 4}
LEVEL_CODE = {"中央级": 1, "省属": 2, "市属": 3, "区县属": 4, "街镇属": 5}
LEVEL_LABEL = {"0": "未标明", "1": "中央级", "2": "省属", "3": "市属", "4": "区县属", "5": "街镇属"}
CAT_LABEL = {"1": "机关", "2": "事业单位", "4": "学校", "3": "机关·事业单位",
             "5": "机关·学校", "6": "事业单位·学校", "7": "机关·事业单位·学校"}
SCHOOL_TYPE = {"幼儿园": "幼儿园", "学前教育": "幼儿园", "小学": "小学",
               "中学": "中学", "初中": "中学", "高中": "高中", "高校": "高校"}

SOURCES = [
    ("福建浙江温州机关_整合_行政层级_经纬度.xlsx", "机关清单", "机关"),
    ("福建浙江温州事业单位_整合_行政层级_经纬度_20261110.xlsx", "事业单位清单", "事业单位"),
    ("福建温州公办民办非企业学校_整合_经纬度_行政层级_20261110.xlsx", "学校清单", "学校"),
]

# 业务覆盖范围：福建全省 + 浙江温州行政区（GCJ-02）。
# 福建约 23.5—28.3N / 115.8—120.5E，温州约 27.0—28.5N / 119.5—121.2E；
# 上下留 0.2—0.3 度余量以容纳边界乡镇，越界者判为地理编码跨省误匹配，予以剔除。
# 注意：不按「到市中心距离」剔除——南平浦城、温州泰顺等辖区边缘距市中心逾 120km 仍属真实。
LAT_MIN, LAT_MAX = 23.3, 28.6
LNG_MIN, LNG_MAX = 115.8, 121.3

# 「坐标—登记区划」一致性：以项目自有 95 个区县中心（server/data/regions.json）为参照，
# 记录坐标若距其登记市任一区县中心均超过 80km，判为地理编码跨区误匹配，不纳入测算。
# 该判据不会误杀浦城、泰顺等辖区边缘机构（其本市中心点已在参照表内）。
REGION_FILE = os.path.join(BASE, "server", "data", "regions.json")
MATCH_MAX_KM = 80.0


def haversine(lat1, lng1, lat2, lng2):
    p = math.pi / 180
    dlat, dlng = (lat2 - lat1) * p, (lng2 - lng1) * p
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin(dlng / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def load_city_points():
    with open(REGION_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    pts = {}
    for city, dists in raw.items():
        target = "福州市" if city == "平潭综合实验区" else city
        pts.setdefault(target, [])
        for pair in dists.values():
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                pts[target].append((float(pair[0]), float(pair[1])))
    return pts


CITY_POINTS = load_city_points()


def matches_city(lat, lng, city):
    pts = CITY_POINTS.get(city)
    if not pts:
        return True  # 无参照点时不做臆断剔除
    return min(haversine(lat, lng, p[0], p[1]) for p in pts) <= MATCH_MAX_KM


def norm_text(v, limit=None):
    s = "" if v is None else str(v).strip()
    s = s.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    s = re.sub(r"\s+", " ", s).strip()
    if s in ("-", "--", "None", "nan"):
        s = ""
    if limit and len(s) > limit:
        s = s[:limit]
    return s


def parse_coord(row, idx):
    """统一返回 (lat, lng)；三份表的「经纬度」为 经度,纬度。"""
    lat = lng = None
    if "经度" in idx and "纬度" in idx:
        try:
            lng = float(row[idx["经度"]])
            lat = float(row[idx["纬度"]])
        except (TypeError, ValueError):
            lat = lng = None
    if lat is None and "经纬度" in idx:
        raw = norm_text(row[idx["经纬度"]])
        m = re.findall(r"-?\d+(?:\.\d+)?", raw)
        if len(m) >= 2:
            try:
                lng, lat = float(m[0]), float(m[1])
            except ValueError:
                return None
    if lat is None or lng is None:
        return None
    if not (LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX):
        return None
    return round(lat, 6), round(lng, 6)


def norm_city(raw, lat, lng):
    c = norm_text(raw)
    if c in CITY_ALIAS:
        return CITY_ALIAS[c]
    if c in CITY_ORDER:
        return c
    # 兜底：按坐标归入最近的地市中心（如「市=福建」等异常值）
    best, bd = None, 1e18
    for city, (clat, clng) in CITY_CENTER.items():
        d = (lat - clat) ** 2 + (lng - clng) ** 2
        if d < bd:
            best, bd = city, d
    return best


def level_code(raw):
    s = norm_text(raw)
    for k, v in LEVEL_CODE.items():
        if s.startswith(k):
            return v
    return 0


def load_rows():
    import openpyxl  # 延迟导入，避免构建页面时依赖 Excel 库
    merged = {}
    stats = {}
    for fname, sheet, cat in SOURCES:
        p = os.path.join(SRC, fname)
        if not os.path.isfile(p):
            raise SystemExit("缺少数据源：" + p + "\n请先把资料库 DATA 文件夹四份 xlsx 放到：" + SRC)
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        ws = wb[sheet]
        it = ws.iter_rows(values_only=True)
        hdr = list(next(it))
        idx = {h: i for i, h in enumerate(hdr) if h}
        n = excluded = mismatch = 0
        for row in it:
            if not row or len(row) < 2:
                continue
            name = norm_text(row[1], 80)
            if not name:
                continue
            n += 1
            coord = parse_coord(row, idx)
            if not coord:
                # 无坐标、伪坐标或地理编码跨省误匹配（超出福建+温州范围）均不参与测算
                excluded += 1
                continue
            lat, lng = coord
            credit = norm_text(row[idx.get("统一社会信用代码", 3)]) if "统一社会信用代码" in idx else ""
            city = norm_city(row[idx["市"]] if "市" in idx else "", lat, lng)
            if not matches_city(lat, lng, city):
                mismatch += 1
                continue
            district = norm_text(row[idx["区县"]] if "区县" in idx else "", 20)
            key = credit if len(credit) >= 15 else (name + "|" + city + "|" + district)
            addr = norm_text(row[idx["地址（注册地址）"]] if "地址（注册地址）" in idx else "", 60)
            lvl = level_code(row[idx["行政层级"]] if "行政层级" in idx else "")
            extra = ""
            if cat == "学校":
                st = SCHOOL_TYPE.get(norm_text(row[idx["学校类型"]]) if "学校类型" in idx else "", "")
                own = norm_text(row[idx["办学性质"]]) if "办学性质" in idx else ""
                extra = ("公办" if own == "公办" else "民办" if own == "民办" else "") + ("-" + st if st else "")
            rec = merged.get(key)
            if rec is None:
                merged[key] = {
                    "n": name, "c": CAT_BIT[cat], "l": lvl, "d": district,
                    "a": addr, "y": lat, "x": lng, "e": extra, "city": city,
                }
            else:
                rec["c"] |= CAT_BIT[cat]
                if len(addr) > len(rec["a"]):
                    rec["a"] = addr
                if lvl and (not rec["l"] or lvl < rec["l"]):
                    rec["l"] = lvl
                if extra and not rec["e"]:
                    rec["e"] = extra
        stats[cat] = {"rows": n, "excluded": excluded, "mismatch": mismatch}
        wb.close()
    return merged, stats


def main():
    merged, stats = load_rows()
    buckets = {c: [] for c in CITY_ORDER}
    for rec in merged.values():
        buckets[rec["city"]].append([
            rec["n"], rec["c"], rec["l"], rec["d"], rec["a"], rec["y"], rec["x"], rec["e"]
        ])

    os.makedirs(OUT, exist_ok=True)
    cities = []
    total_bytes = 0
    for i, city in enumerate(CITY_ORDER):
        rows = buckets[city]
        rows.sort(key=lambda r: r[0])
        lats = [r[5] for r in rows]
        lngs = [r[6] for r in rows]
        bbox = [min(lats), max(lats), min(lngs), max(lngs)] if rows else [0, 0, 0, 0]
        js = ("window.NEARBY_CHUNK=window.NEARBY_CHUNK||{};"
              "window.NEARBY_CHUNK[%d]=%s;\n" %
              (i, json.dumps(rows, ensure_ascii=False, separators=(",", ":"))))
        fp = os.path.join(OUT, "c%d.js" % i)
        with open(fp, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        total_bytes += len(js.encode("utf-8"))
        cities.append({
            "i": i, "name": city, "file": "c%d.js" % i,
            "count": len(rows), "bbox": [round(v, 6) for v in bbox],
        })

    manifest = {
        "generated": datetime.date.today().isoformat(),
        "source": "资料库 DATA 文件夹：机关 / 事业单位 / 学校三份含经纬度清单（启信宝公开登记信息整合）",
        "coordSystem": "GCJ-02",
        "total": len(merged),
        "sourceStats": stats,
        "scope": {"lat": [LAT_MIN, LAT_MAX], "lng": [LNG_MIN, LNG_MAX],
                  "cityMatchMaxKm": MATCH_MAX_KM,
                  "note": "仅保留福建全省与浙江温州行政区范围内的坐标，并以项目自有 95 个区县中心"
                          "校验坐标与登记市一致性（阈值 %g km）；无坐标、伪坐标及跨区误匹配记录"
                          "不参与测算，不臆造坐标。" % MATCH_MAX_KM},
        "dedup": "跨表重复主体按统一社会信用代码合并（缺失时按 名称+市+区县），类别叠加。",
        "cities": cities,
        "levelLabels": LEVEL_LABEL,
        "catLabels": CAT_LABEL,
        "disclaimer": "仅列示公开登记的机构名称、类别、行政层级、区划、注册地址与经纬度；"
                      "地址以登记地址为准，坐标部分来自公开地图地理编码（含少量粗粒度定位），"
                      "距离为经纬度直线距离估算，仅供行内政务合作位置参考。",
    }
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))

    print("数据源统计：")
    for cat, s in stats.items():
        print("  %-6s 行=%6d 剔除(无坐标/越界)=%4d 跨区误匹配=%4d" %
              (cat, s["rows"], s["excluded"], s["mismatch"]))
    print("去重合并后主体数：%d" % len(merged))
    print("分片文件合计：%.2f MB" % (total_bytes / 1024 / 1024))
    for c in cities:
        print("  c%-2d %-5s %6d 条  bbox=%s" %
              (c["i"], c["name"], c["count"], [round(v, 3) for v in c["bbox"]]))
    print("输出目录：" + OUT)


if __name__ == "__main__":
    main()
