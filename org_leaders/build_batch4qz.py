# -*- coding: utf-8 -*-
"""批次4qz（泉州市直核心政府组成部门）负责人核验落盘：写 batch4qz_add.jsonl 并追加 collected.jsonl。

口径：以泉州市人大 2026-10-23 第十七届第四十三次会议完整任免名单为权威主源（时点最新，覆盖8家核心局办），
交叉泉州市政府门户/泉州网报道。存疑不落盘（如民政局新任未在名单列明，不纳入）。
正职取行政主官（局/主任）。
"""
import json
import os

H5 = r"C:\Users\36852\WorkBuddy\2026-10-30-08-35-16\fujian-branch-distance-h5"
OA = os.path.join(H5, "org_leaders")

# 主源：泉州市人大 2026-10-23 第四十三次会议任免名单
SRC1 = "http://qzrd.gov.cn/xjrm/202610/t20261026_3338646.htm"
# 交叉：泉州网转载同一任免名单
SRC2 = "https://www.qzwb.com/gb/content/2026-10/24/content_9258440.htm"
# 另据 2026-04 第三十八次会议（苏延辉任副市长等，交通/农业新任以10月名单为准）


def e(name, leader, role, asof, src, src2, note):
    return {"name": name, "leader": leader, "role": role, "asof": asof,
            "src": src, "src2": src2, "status": "verified", "note": note}


entries = []

# 1 交通运输局：陈沙龙（任命，2026-10；2026-04 免去刘德旺，取时点最新）
entries.append(e("泉州市交通运输局", "陈沙龙", "局长", "2026-10", SRC1, SRC2,
                 "泉州市人大2026-10-23第四十三次会议任命陈沙龙任交通运输局局长（免去2026-04第三十八次会议的刘德旺，取时点最新）"))
# 2 农业农村局：王洪龙（任命，2026-10；2026-04 免去蔡龙群，取时点最新）
entries.append(e("泉州市农业农村局", "王洪龙", "局长", "2026-10", SRC1, SRC2,
                 "泉州市人大2026-10-23第四十三次会议任命王洪龙任农业农村局局长（免去2026-04第三十八次会议的蔡龙群，取时点最新）"))
# 3 文化广电和旅游局：蔡英殿（任命，2026-10；免去吕秀家，取时点最新）
entries.append(e("泉州市文化广电和旅游局", "蔡英殿", "局长", "2026-10", SRC1, SRC2,
                 "泉州市人大2026-10-23第四十三次会议任命蔡英殿任文化广电和旅游局局长（免去吕秀家，取时点最新）"))
# 4 卫生健康委员会：曾惠彬（任命，2026-10；免去苏松炎，取时点最新；职能为主任）
entries.append(e("泉州市卫生健康委员会", "曾惠彬", "主任", "2026-10", SRC1, SRC2,
                 "泉州市人大2026-10-23第四十三次会议任命曾惠彬任卫生健康委员会主任（免去苏松炎，取时点最新）"))
# 5 审计局：林添盛（任命，2026-10；免去骆振军，取时点最新）
entries.append(e("泉州市审计局", "林添盛", "局长", "2026-10", SRC1, SRC2,
                 "泉州市人大2026-10-23第四十三次会议任命林添盛任审计局局长（免去骆振军，取时点最新）"))
# 6 司法局：杨华民（任命，2026-10；免去林强，取时点最新）
entries.append(e("泉州市司法局", "杨华民", "局长", "2026-10", SRC1, SRC2,
                 "泉州市人大2026-10-23第四十三次会议任命杨华民任司法局局长（免去林强，取时点最新）"))
# 7 民族与宗教事务局：韩卫华（任命，2026-10）
entries.append(e("泉州市民族与宗教事务局", "韩卫华", "局长", "2026-10", SRC1, SRC2,
                 "泉州市人大2026-10-23第四十三次会议任命韩卫华任民族与宗教事务局局长"))
# 8 人民政府信访局：陈雄松（任命，2026-10）
entries.append(e("泉州市人民政府信访局", "陈雄松", "局长", "2026-10", SRC1, SRC2,
                 "泉州市人大2026-10-23第四十三次会议任命陈雄松任泉州市人民政府信访局局长"))

# 写出 batch4qz_add.jsonl
with open(os.path.join(OA, "batch4qz_add.jsonl"), "w", encoding="utf-8") as f:
    for r in entries:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# 追加 collected.jsonl
with open(os.path.join(OA, "collected.jsonl"), "a", encoding="utf-8") as f:
    for r in entries:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("batch4qz_add.jsonl entries:", len(entries))
print("collected after:", sum(1 for _ in open(os.path.join(OA, "collected.jsonl"), encoding="utf-8")))
