# -*- coding: utf-8 -*-
"""批次3f（平潭综合实验区核心政府组成部门/局办）负责人核验落盘：写 batch3f_add.jsonl 并追加 collected.jsonl。"""
import json
import os

H5 = r"C:\Users\36852\WorkBuddy\2026-10-30-08-35-16\fujian-branch-distance-h5"
OA = os.path.join(H5, "org_leaders")

# 平潭综合实验区官方机构页（pingtan.gov.cn 政府机构栏目）
SRC1 = "https://www.pingtan.gov.cn/zwgk/zzjg/202603/t20260303_105406.htm"        # 社会事业局机构页2026-03
SRC2 = "https://www.pingtan.gov.cn/zwgk/zzjg/202010/t20201016_23116.htm"          # 综合执法与应急管理局机构页
SRC3 = "https://www.pingtan.gov.cn/zwgk/zzjg/202206/t20220610_34345.htm"          # 公安局机构页
SRC4 = "https://www.pingtan.gov.cn/zwgk/zzjg/202003/t20200325_20022.htm"          # 经济发展局机构页
SRC5 = "https://www.pingtan.gov.cn/zwgk/zzjg/202111/t20211124_29160.htm"          # 财政金融局机构页2026-09-10
SRC6 = "https://www.pingtan.gov.cn/zwgk/zzjg/202003/t20200330_20082.htm"          # 旅游与文化体育局机构页2026-08-20
SRC7 = "https://www.pingtan.gov.cn/zwgk/zzjg/202003/t20200331_20103.htm"          # 交通与建设局机构页2026-02-24
SRC8 = "https://www.pingtan.gov.cn/zwgk/zzjg/202211/t20221104_38429.htm"          # 自然资源与生态环境局机构页
SRC9 = "https://www.pingtan.gov.cn/zwgk/zzjg/202003/t20200313_19889.htm"          # 行政审批局机构页2025-02-10


def e(name, leader, role, asof, src, src2, note):
    return {"name": name, "leader": leader, "role": role, "asof": asof,
            "src": src, "src2": src2, "status": "verified", "note": note}


entries = []

# 平潭综合实验区核心组成部门/局办（9家，均为区管委会工作部门，正职取行政主官）
entries.append(e("平潭综合实验区社会事业局", "王浩", "党组书记、局长", "2026-03", SRC1, "",
                 "机构页2026-03载王浩党组书记、局长（主持局党组、局务全面工作）"))
entries.append(e("平潭综合实验区综合执法与应急管理局", "林传国", "党委书记、局长", "2020", SRC2, "",
                 "机构页（未更新，取最新可得值）：林传国党委书记、局长，主持局全面工作"))
entries.append(e("平潭综合实验区公安局", "陈建生", "党委书记、局长、督察长", "2025-04", SRC3, "",
                 "机构页2025-04载陈建生党委书记、局长、督察长（正职行政主官）"))
entries.append(e("平潭综合实验区经济发展局", "林润", "局长", "2025-02", SRC4, "",
                 "机构页载林润局长（主要负责人贾尉斌主持党组）；取行政主官为负责人"))
entries.append(e("平潭综合实验区财政金融局", "陈伟明", "党组书记、局长", "2026-09", SRC5, "",
                 "机构页2026-09-10载陈伟明党组书记、局长（兼平潭县财政金融局局长）"))
entries.append(e("平潭综合实验区旅游与文化体育局", "魏长春", "党组书记、局长", "2026-08", SRC6, "",
                 "机构页2026-08-20载魏长春党组书记、局长（主持局党组、局全面工作）"))
entries.append(e("平潭综合实验区交通与建设局", "林郁川", "党组书记、局长", "2026-02", SRC7, "",
                 "机构页2026-02-24载林郁川党组书记、局长（主持局党组、行政全面工作）"))
entries.append(e("平潭综合实验区自然资源与生态环境局", "王天军", "党组书记、局长", "2025", SRC8, "",
                 "机构页载王天军党组书记、局长（机构信息负责人同）"))
entries.append(e("平潭综合实验区行政审批局", "林良明", "党组书记、局长", "2025-02", SRC9, "",
                 "机构页2025-02-10载林良明党组书记、局长（主持区行政审批局全面工作）"))

# 写出 batch3f_add.jsonl
with open(os.path.join(OA, "batch3f_add.jsonl"), "w", encoding="utf-8") as f:
    for r in entries:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# 追加 collected.jsonl
with open(os.path.join(OA, "collected.jsonl"), "a", encoding="utf-8") as f:
    for r in entries:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("batch3f_add.jsonl entries:", len(entries))
print("collected after:", sum(1 for _ in open(os.path.join(OA, "collected.jsonl"), encoding="utf-8")))
