# -*- coding: utf-8 -*-
"""生成微信分享卡片封面图（OG og:image）与可直接发群的卡片物料。
输出：
  share-card.png            600x600 不透明 PNG，用于 og:image（随仓库部署到 GitHub Pages）
  微信群分享卡片.png          750x1180 卡片+二维码，可直接发微信群
"""
import os
import segno
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
URL = "https://cjwx-bot.github.io/fjhx-branch-distance/"

FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"


def font(bold, size):
    path = FONT_BOLD if bold else FONT_REG
    return ImageFont.truetype(path, size, index=0)


def gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        r = y / max(h - 1, 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * r) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return img


def draw_pin(d, cx, cy, scale=1.0, color=(255, 255, 255), hole=(0, 110, 255)):
    """白色定位针：外圆 + 下方三角 + 中心镂空圆点"""
    r = int(46 * scale)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    d.polygon([(cx - int(30 * scale), cy + int(20 * scale)),
               (cx + int(30 * scale), cy + int(20 * scale)),
               (cx, cy + int(86 * scale))], fill=color)
    hr = int(19 * scale)
    d.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=hole)


# ---------- 1) OG 封面图 600x600 ----------
S = 600
img = gradient((S, S), (0, 128, 255), (0, 70, 190))
d = ImageDraw.Draw(img)
# 装饰光斑
d.ellipse([-90, -110, 210, 190], outline=(255, 255, 255, 40), width=2)
d.ellipse([430, 430, 700, 700], outline=(255, 255, 255, 40), width=2)
d.ellipse([470, -70, 650, 110], fill=(255, 255, 255, 18))

d.text((S // 2, 92), "福建海峡银行 · 网点服务", font=font(False, 26), fill=(225, 240, 255), anchor="mm")
draw_pin(d, S // 2, 205, scale=1.05)
d.text((S // 2, 358), "最近网点查询", font=font(True, 62), fill="white", anchor="mm")
d.line([(150, 412), (450, 412)], fill=(180, 215, 255), width=2)
d.text((S // 2, 452), "输入机构名称 · 按真实坐标精确测算", font=font(False, 25), fill=(232, 244, 255), anchor="mm")
d.text((S // 2, 510), "福建全省及浙江温州  ·  91 家网点", font=font(False, 24), fill=(205, 228, 255), anchor="mm")
d.rounded_rectangle([206, 540, 394, 582], radius=20, fill=(56, 158, 255))
d.text((S // 2, 561), "点击即可查询", font=font(True, 21), fill="white", anchor="mm")

cover = os.path.join(BASE, "share-card.png")
img.save(cover, "PNG", optimize=True)
print("cover:", cover, os.path.getsize(cover), "bytes", img.size, img.mode)

# ---------- 2) 群发卡片物料（封面 + 二维码） ----------
W, H = 750, 1180
card = Image.new("RGB", (W, H), (237, 241, 247))
dc = ImageDraw.Draw(card)
# 顶部标题条
dc.rounded_rectangle([30, 30, W - 30, 118], radius=18, fill=(0, 110, 255))
dc.text((W // 2, 74), "最近网点查询 · 微信群分享卡片", font=font(True, 32), fill="white", anchor="mm")

# 主体白色卡片
dc.rounded_rectangle([30, 140, W - 30, 1120], radius=20, fill="white")
# 左侧缩略图（模拟微信卡片）
thumb = img.resize((190, 190), Image.LANCZOS)
card.paste(thumb, (56, 168))
dc.text((266, 205), "最近网点查询", font=font(True, 36), fill=(26, 32, 44), anchor="lm")
dc.text((266, 258), "输入机构名称，按真实经纬度", font=font(False, 23), fill=(110, 122, 140), anchor="lm")
dc.text((266, 292), "精确测算最近的福建海峡银行网点", font=font(False, 23), fill=(110, 122, 140), anchor="lm")
dc.text((266, 340), "cjwx-bot.github.io", font=font(False, 21), fill=(150, 160, 175), anchor="lm")
dc.line([(56, 392), (W - 56, 392)], fill=(230, 234, 241), width=2)

# 二维码
qr_tmp = os.path.join(BASE, "_qr_tmp.png")
segno.make(URL, error="m").save(qr_tmp, scale=10, border=2, dark="#0B3B8C", light="white")
qr = Image.open(qr_tmp).convert("RGB").resize((400, 400), Image.NEAREST)
card.paste(qr, ((W - 400) // 2, 420))
os.remove(qr_tmp)

dc.text((W // 2, 862), "长按识别二维码 · 打开查询页", font=font(True, 30), fill=(26, 32, 44), anchor="mm")
dc.text((W // 2, 910), "或在微信中打开下方链接", font=font(False, 23), fill=(110, 122, 140), anchor="mm")
dc.rounded_rectangle([56, 940, W - 56, 1000], radius=12, fill=(243, 246, 251))
dc.text((W // 2, 970), URL, font=font(False, 19), fill=(0, 90, 210), anchor="mm")
dc.text((W // 2, 1050), "福建海峡银行 · 91 家网点 · 免安装免注册", font=font(False, 22), fill=(140, 150, 165), anchor="mm")

out = os.path.join(ROOT, "微信群分享卡片.png")
card.save(out, "PNG", optimize=True)
print("card:", out, os.path.getsize(out), "bytes", card.size)
