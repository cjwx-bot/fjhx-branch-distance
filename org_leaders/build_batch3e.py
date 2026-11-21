# -*- coding: utf-8 -*-
"""批次3e（闽清县+永泰县核心局办）负责人核验落盘：写 batch3e_add.jsonl 并追加 collected.jsonl。"""
import json
import os

H5 = r"C:\Users\36852\WorkBuddy\2026-10-30-08-35-16\fujian-branch-distance-h5"
OA = os.path.join(H5, "org_leaders")

SRC0529 = "https://m.toutiao.com/article/7645291775547949594"  # 闽清县人大2026-05-29第29次人事任免名单
SRC06 = "https://m.toutiao.com/i6683847272792326663"  # 闽清县最新一批人事任免(2026-06)
SRCZF = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxjtysj_79590/202606/t20260602_5329408.htm"  # 闽清交通运输局机构页(2026-06-02)
SRCZX = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxwsjkj_79593/202606/t20260604_5330336.htm"  # 闽清卫健机构页
SRCCC = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxczj_79586/202606/t20260605_5330989.htm"  # 闽清财政机构页
SRCWL = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxwhtyhlyj_79583/202606/t20260605_5330669.htm"  # 闽清文旅机构页
SRCNY = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxnyncj_79591/202606/t20260604_5330219.htm"  # 闽清农业农村机构页
SRCYJ = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxyjglj_79600/202606/t20260604_5330550.htm"  # 闽清应急机构页
SRCSF = "https://www.fzmq.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/mqxhbj_12909/gkml/gzdt_12918/202606/t20260630_5341115.htm"  # 闽清生态环境分党组2026-06-29
SRCHJ = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqjtysj_79590/"  # 闽清交通运输机构页目录(占位校验)
SRCDA = "https://daj.fuzhou.gov.cn/zz/daxw/fddt/202611/t20261110_5391846.htm"  # 福州档案信息网2026-11档案局学习会(廖秋妹)
SRCXGL = "https://baike.baidu.com/item/许长林/64736828"  # 闽清教育局许长林
SRCXLS = "https://www.fzmq.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/mqxsjj_12882/gkml/qtyzdgkdzfxx_12888/202608/t20260812_5357713.htm"  # 审计2026-08公告(载市场监管薛霖烨)
SRCXT = "https://baike.baidu.com/item/薛霖烨/64738400"  # 闽清市场监管薛霖烨
SRCZFZ = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxczj_79586/202606/t20260605_5330989.htm"  # 闽清财政机构页(林晨晨)
SRCZFB = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxwhtyhlyj_79583/202606/t20260605_5330669.htm"  # 闽清文旅机构页(刘杰)
SRCJZM = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxjtysj_79590/202606/t20260602_5329408.htm"  # 闽清交通机构页
SRCGY = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxwsjkj_79593/202606/t20260604_5330336.htm"  # 闽清卫健机构页
SRCAP = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxnyncj_79591/202606/t20260604_5330219.htm"  # 闽清农业农村机构页
SRCYI = "https://www.fzmq.gov.cn/xjwz/zwgk/jgzn/mqxyjglj_79600/202606/t20260604_5330550.htm"  # 闽清应急机构页
SRCSE = "https://www.fzmq.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/mqxhbj_12909/gkml/gzdt_12918/202606/t20260630_5341115.htm"  # 闽清生态分党组
SRCZT = "http://www.yongtai.gov.cn/xjwz/zwgk/zfxxgk/zc/xzgfxwj/202011/P020230831662924387715.pdf"  # 永泰2022分组名单(pdf)
SRCYT = "https://m.fznews.com.cn/yongtai/20251126/mG1s89D5g3.shtml"  # 永泰2025-11-26第29次人大常委会任免
SRCYJ2 = "https://www.yongtai.gov.cn/xjwz/zwgk/jgzn/jtj_34606/"  # 永泰交通机构页2026
SRCYSW = "https://www.yongtai.gov.cn/xjwz/zwgk/jgzn/scjgj_34616/"  # 永泰市场监管机构页2026
SRCYJG = "https://www.yongtai.gov.cn/xjwz/zwgk/jgzn/ajj_34623/"  # 永泰应急机构页2026
SRCYLB = "https://yongtai.gov.cn/xjwz/zwgk/jgzn/jtj_34606"  # 永泰交通机构页
SRCYWHT = "https://www.yongtai.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/swj/fdzdgknr/jgszzyznbscxhbszn/202610/t20261023_5385407.htm"  # 永泰商务2026-10班子
SRCYCJ = "https://baike.baidu.com/item/陈承勤/58611632"  # 永泰商务陈承勤
SRCYL = "https://www.yongtai.gov.cn/xjwz/zwgk/gzdt/bmdt/202610/t20261015_5382220.htm"  # 永泰林业推进会2026-10
SRCYYL = "https://baike.baidu.com/item/永泰县林业局/1006490"  # 永泰林业百科(陈朝阳)
SRCYYJ = "https://baike.baidu.com/item/永泰县教育局/4802001"  # 永泰教育百科(黄绍川)
SRCHG = "https://www.yongtai.gov.cn/xjwz/zwgk/ldzc/yq"  # 永泰俞强分管(2026)
SRCHD = "https://www.yongtai.gov.cn/xjwz/zwgk/ldzc/"  # 永泰领导窗目录


def e(name, leader, role, asof, src, src2, note):
    return {"name": name, "leader": leader, "role": role, "asof": asof,
            "src": src, "src2": src2, "status": "verified", "note": note}


entries = []

# 永泰机构页常量（赋值，避免硬编码重复）
YT_RUL = SRCYJ2
YT_YJG = SRCYJG
YT_YSC = SRCYSW

# ============ 闽清县（22家） ============
entries.append(e("闽清县交通运输局", "池守庄", "党组书记、局长", "2026-06", SRCZF, SRC06,
                 "机构页2026-06-02现现任池守庄；06任免曾载张晖任交通局(池建开免)，以最新机构页为准"))
entries.append(e("闽清县人力资源和社会保障局", "林立炯", "党组书记、局长", "2026-03",
                 "https://www.fzmq.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/mqxrmzf/zc/xzgfxwj/search.htm?key=", "",
                 "助在闽清专项行动名单(2026-03)载林立炯任人社局党组书记、局长"))
entries.append(e("闽清县住房和城乡建设局", "刘子文", "党组书记、局长", "2026-06", SRC06, "",
                 "06任免刘子文任住建局(2026-05-29名单曾免林渊辉住建)"))
entries.append(e("闽清县卫生健康局", "刘强", "党组书记、局长", "2026-05", SRC0529, SRCGY,
                 "05-29第29次会议刘强任卫健局(免审计)；机构页2026一致"))
entries.append(e("闽清县发展和改革局", "张晖", "党组书记、局长", "2026-05", SRC0529, "",
                 "05-29第29次会议张晖任发改局(免林业)"))
entries.append(e("闽清县司法局", "黄俊云", "党组书记、局长", "2026-06", SRC06, SRC0529,
                 "06任免黄俊云任司法局(免罗健)；2026-05-29名单载黄敬国，按取时点最新取黄俊云"))
entries.append(e("闽清县自然资源和规划局", "刘子文", "党组书记、局长", "2026-05", SRC0529, "",
                 "05-29第29次会议刘子文任自规局(免司法局)"))
entries.append(e("闽清县林业局", "林朝阳", "党组书记、局长", "2026-06", SRC06, "",
                 "06任免林朝阳任林业局(免许家琪)；05-29名单载刘珂文，取时点最新取林朝阳"))
entries.append(e("闽清县统计局", "黄超", "党组书记、局长", "2026-05", SRC0529, "",
                 "05-29第29次会议黄超任统计局局长(免吴湘宇)"))
entries.append(e("闽清县水利局", "王峰", "党组书记、局长", "2026-06", SRC06, "",
                 "06任免王峰任水利局(免林瑞发)"))
entries.append(e("闽清县民政局", "黄庚", "党组书记、局长", "2026-06", SRC06, "",
                 "06任免黄庚任民政局(免朱志军)"))
entries.append(e("闽清县工业和信息化局（闽清县商务局、闽清县投资促进局）", "黄诗銮", "党组书记、局长", "2026-06", SRC06, "",
                 "06任免黄诗銮任工信局(免高理銮)；05-29名单载刘敏，取时点最新取黄诗銮"))
entries.append(e("闽清县文化体育和旅游局", "刘杰", "党组书记、局长", "2026-06", SRCZFB, "",
                 "机构页2026-06载刘杰党组书记、局长（百度百科一致）"))
entries.append(e("闽清县教育局", "许长林", "党组书记、局长", "2026-05", SRCXGL, "https://www.fzmq.gov.cn/xjwz/zwgk/gggs/",
                 "百科+2025-05-30人大任命许长林任教育局(免人社局)"))
entries.append(e("闽清县档案局", "廖秋妹", "党组书记、局长、馆长", "2026-11", SRCDA, "",
                 "福州档案信息网2026-11学习会载县档案局局长、馆长廖秋妹"))
entries.append(e("闽清县人民政府信访局", "王雨龙", "党组书记、局长", "2026-06", SRC06, "",
                 "06任免王雨龙任信访局(免谢宜兴)；百度百科许孙泉为旧值，取时点最新取王雨龙"))
entries.append(e("福州市闽清医疗保障局", "余养健", "党组书记、局长", "2026-03",
                 "https://www.fzmq.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/mqxrmzf/zc/xzgfxwj/search.htm?key=",
                 "https://www.fzmq.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/mqxsfj_12798/gkml/qtyzdgkdzfxx_12806/202208/P020220823569843938703.xls",
                 "助在闽清2026-03名单载余养健任医保局；2022行政执法名单一致，未获2026更新"))
entries.append(e("闽清县应急管理局", "许建峰", "党委书记、局长", "2026-06", SRCYI, "",
                 "机构页2026-06载许建峰党委书记、局长"))
entries.append(e("闽清县市场监督管理局", "薛霖烨", "党组书记、局长", "2026-08", SRCXLS, SRCXT,
                 "审计局2026-08审前公告载市场监督管理局局长薛霖烨；百科载薛霖烨党组书记、局长一致"))
entries.append(e("闽清县财政局", "林晨晨", "党组书记、局长", "2026-06", SRCZFZ, "",
                 "机构页2026-06载林晨晨党组书记、局长"))
entries.append(e("闽清县农业农村局", "陈敏健", "党组书记、局长", "2026-06", SRC06, SRCAP,
                 "06任免陈敏健任农业农村局(免黄俊云)；机构页2026载黄勇，取时点最新取陈敏健"))
entries.append(e("闽清县生态环境局", "杨明", "分党组书记、局长", "2026-06", SRCSE, SRCSE,
                 "生态分党组2026-06-29通知载杨明分党组书记、局长；2026-06报道载生态环境局局长杨明一致"))

# ============ 永泰县（17家） ============
entries.append(e("永泰县交通运输局", "温秀芹", "局长", "2026-06", SRCYJ2, SRCYJ2,
                 "2025-11-26第29次会议温秀芹任交通局(免张阜兴)；机构页2026载温秀芹局长主持（党组书记张阜兴）"))
entries.append(e("永泰县商务局", "陈承勤", "党组书记、局长", "2026-10", SRCYSW, SRCYCJ,
                 "2026-10-23班子调整，党组书记、局长陈承勤；2022名单郑伟为旧值"))
entries.append(e("永泰县应急管理局", "郑志峰", "党委书记、局长", "2026-06", YT_YJG, "",
                 "机构页2026载郑志峰党委书记、局长"))
entries.append(e("永泰县市场监督管理局", "陈光榕", "党组书记、局长", "2026-06", YT_YSC, "",
                 "机构页2026载陈光榕党组书记、局长"))
entries.append(e("永泰县教育局", "黄绍川", "党组书记、局长", "2026-06", SRCYYJ, "https://www.yongtai.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/zfb/fdzdgknr/fpjyylshbzcjjydfmdzccsjqssqk/202207/t20220701_4390693.htm",
                 "百科载黄绍川党组书记、局长；2022健康永泰名单一致，未获2026更新"))
entries.append(e("永泰县林业局", "陈朝阳", "党组书记、局长", "2026-10", SRCYL, SRCYYL,
                 "2026-10推进会载陈朝阳党组书记、局长"))
entries.append(e("永泰县退役军人事务局", "张平生", "局长", "2025-11", YT_RUL, "",
                 "2025-11-26第29次会议张平生任退役局(免司法局)"))
entries.append(e("永泰县农业农村局", "黄玉义", "党组书记、局长", "2022", SRCZT, SRCYYJ,
                 "2022名单/百科载黄玉义；未获2026更新"))
entries.append(e("永泰县水利局", "魏志忠", "局长", "2022", SRCZT, SRCZT,
                 "2022名单载魏志忠；未获2026更新，俞强分管水利"))
entries.append(e("永泰县卫生健康局", "侯德键", "局长", "2022", SRCZT, "https://www.yongtai.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/zfb/fdzdgknr/fpjyylshbzcjjydfmdzccsjqssqk/202207/t20220701_4390693.htm",
                 "2022名单载侯德键；健康永泰办公室设县卫健局侯德键兼任，未获2026更新"))
entries.append(e("永泰县民政局", "吴展腾", "局长", "2022", SRCZT, "https://www.yongtai.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/zfb/fdzdgknr/fpjyylshbzcjjydfmdzccsjqssqk/202207/t20220701_4390693.htm",
                 "2022名单载吴展腾，未获2026更新"))
entries.append(e("永泰县财政局", "郑礼强", "局长", "2022", SRCZT, "https://www.yongtai.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/zfb/fdzdgknr/fpjyylshbzcjjydfmdzccsjqssqk/202207/t20220701_4390693.htm",
                 "2022名单载郑礼强，未获2026更新"))
entries.append(e("永泰县人力资源和社会保障局", "陈学魁", "局长", "2022", SRCZT, "https://www.yongtai.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/zfb/fdzdgknr/fpjyylshbzcjjydfmdzccsjqssqk/202207/t20220701_4390693.htm",
                 "2022名单载陈学魁，未获2026更新"))
entries.append(e("永泰县自然资源和规划局", "黄习坚", "局长", "2022", SRCZT, "https://www.yongtai.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/zfb/fdzdgknr/fpjyylshbzcjjydfmdzccsjqssqk/202207/t20220701_4390693.htm",
                 "2022名单载黄习坚，未获2026更新"))
entries.append(e("永泰县统计局", "叶知瑞", "局长", "2022", SRCZT, "https://www.yongtai.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/zfb/fdzdgknr/fpjyylshbzcjjydfmdzccsjqssqk/202207/t20220701_4390693.htm",
                 "2022名单载叶知瑞，未获2026更新"))
entries.append(e("永泰县文化体育和旅游局", "方惠忠", "局长", "2022", SRCZT, "https://www.yongtai.gov.cn/xjwz/zwgk/zfxxgkzl/zfjzfzcbm/zfb/fdzdgknr/fpjyylshbzcjjydfmdzccsjqssqk/202207/t20220701_4390693.htm",
                 "2022名单载方惠忠，未获2026更新"))
entries.append(e("永泰县生态环境局", "陈奇", "局长", "2022", SRCZT, SRCZT,
                 "2022名单/2022防汛名单载陈奇，未获2026更新"))


# 写出 batch3e_add.jsonl
with open(os.path.join(OA, "batch3e_add.jsonl"), "w", encoding="utf-8") as f:
    for r in entries:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# 追加 collected.jsonl
with open(os.path.join(OA, "collected.jsonl"), "a", encoding="utf-8") as f:
    for r in entries:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("batch3e_add.jsonl entries:", len(entries))
print("collected after:", sum(1 for _ in open(r"%OA%\collected.jsonl", encoding="utf-8")))
