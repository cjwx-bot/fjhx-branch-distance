import zlib, struct

W = H = 200
BLUE = (0x00, 0x6E, 0xFF)   # 腾讯地图蓝
WHITE = (255, 255, 255)

def sign(px, py, ax, ay, bx, by):
    return (px - bx) * (ay - by) - (ax - bx) * (py - by)

def in_tri(px, py):
    # 顶点：尖端(100,162) 左上(68,84) 右上(132,84)
    ax, ay, bx, by, cx, cy = 100, 162, 68, 84, 132, 84
    d1 = sign(px, py, ax, ay, bx, by)
    d2 = sign(px, py, bx, by, cx, cy)
    d3 = sign(px, py, cx, cy, ax, ay)
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)

def d2(x, y, cx, cy):
    return (x - cx) ** 2 + (y - cy) ** 2

raw = bytearray()
for y in range(H):
    raw.append(0)  # filter type 0
    for x in range(W):
        col = BLUE                      # 方形蓝底（不透明，缩略图兼容好）
        if d2(x, y, 100, 82) <= 36 * 36:   # 白色圆头
            col = WHITE
        if in_tri(x, y):                  # 白色针尖三角
            col = WHITE
        if d2(x, y, 100, 82) <= 18 * 18:  # 蓝色中心孔
            col = BLUE
        raw += bytes((col[0], col[1], col[2]))

def chunk(typ, data):
    c = typ + data
    return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)

sig = b"\x89PNG\r\n\x1a\n"
ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)  # 8-bit RGB
idat = zlib.compress(bytes(raw), 9)
png = sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
with open("icon.png", "wb") as f:
    f.write(png)
print("icon.png written, bytes =", len(png))
