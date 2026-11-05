# 福建海峡银行最近网点查询 —— 实时后端代理

在 H5 录入模糊机构名称时，实时调用**企查查 / 天眼查**返回机构**全称、统一社会信用代码、注册地址、所属地区**，
结合内置的福建海峡银行 91 家网点库，计算并下发距离最近的网点。

> 为什么需要后端？微信内打开的 H5 是纯静态页，无法在浏览器端直连企业库（无密钥、跨域受限）。
> 本后端作为代理：H5 → 本服务 → 企查查/天眼查官方 API → 返回结构化结果。

---

## 一、目录结构
```
server/
├── server.js              # HTTP 服务（含轻量 .env 加载、CORS、路由、缓存）
├── package.json
├── .env.example           # 环境变量模板（复制为 .env 后填真实值）
├── core/index.js          # 距离/行政区划中心/机构类型研判/最近网点
├── providers/lookup.js    # 数据提供方：qcc / tyc / mock
└── data/                  # 从 H5 抽取的权威数据（regions / province / 91 家网点）
```

## 二、本地运行（无密钥，mock 模式先跑通）
```bash
cd server
node server.js
# 或 npm start
```
- 默认 `DATA_PROVIDER=mock`，不调用任何外部 API，仅用名称识别区县 + 内置网点算最近网点，用于验证全链路。
- 健康检查：`GET http://localhost:3000/api/health`
- 查询示例：`GET http://localhost:3000/api/org?name=福建省财政厅&type=government`

## 三、接入真实密钥（企查查 / 天眼查）
1. 复制模板：`cp .env.example .env`
2. 编辑 `.env`：
   - `DATA_PROVIDER=qcc`（或 `tyc`）
   - 填 `QCC_APP_KEY` / `QCC_APP_SECRET`（企查查开放平台申请）
     或 `TYC_TOKEN`（天眼查开放平台申请）
   - 可选 `MAP_KEY`：腾讯地图 WebService 密钥，启用后按"注册地址"精确地理编码，最近网点更准
3. 重启服务。

> ⚠️ **字段映射可能需微调**：qcc/tyc 不同订阅产品的返回字段名不完全一致。
> 映射逻辑集中在 `providers/lookup.js` 的 `lookupQcc` / `lookupTyc` 中（注释已标明）。
> 若返回 `found:false` 或字段为空，请对照你实际 API 文档调整对应取值路径。

## 四、接口
`GET /api/org?name=<机构名>&type=<government|public|group>`
返回（示例）：
```json
{
  "found": true,
  "query": "福建省财政厅",
  "org": {
    "fullName": "福建省财政厅",
    "creditCode": "11350000003591213N",
    "typeKey": "government", "typeLabel": "党政机关",
    "address": "福州市鼓楼区中山路5号",
    "province": "福建省", "city": "福州市", "district": "鼓楼区",
    "lat": 26.0885, "lng": 119.292, "coordSource": "district-center"
  },
  "nearest": [ { "name": "...", "type": "...", "address": "...", "phone": "...", "distText": "328 米", "distM": 328 } ],
  "branchCount": 91
}
```
- `found:false`：企业库未匹配（名称需更完整，或该机构未收录）→ 前端自动回退本地估算。
- 内置 24h 结果缓存，降低按次计费与限频压力。

## 五、部署后端（公网可达，H5 才能调用）
后端需部署到**公网可访问**的地址（H5 设置卡片中填入该地址）。
可选方式：
- 自有服务器 / 云主机：`node server.js` 并配置反向代理（Nginx）与 HTTPS。
- 云函数：腾讯云 SCF / 阿里云 FC / Railway / Render 等，将 `server/` 作为 Node 服务部署（注意设置环境变量）。
- 无需数据库，无外部依赖（Node ≥ 18 内置 fetch）。

## 六、H5 接入实时查询
1. H5 已内置"实时查询设置（可选）"卡片。
2. 在卡片中填入你的后端公网地址（如 `https://your-domain.com`），点"保存后端地址"。
3. 此后在"机构名称"录入模糊名称并查询，即走实时接口；保存的地址仅存本设备 localStorage。
4. 不填则使用本机离线估算（按行政区划中心）。

## 七、安全与计费
- **密钥不入库**：仅放在后端 `.env`，切勿提交到代码仓库或写进 H5。
- **按次计费**：企查查/天眼查官方 API 均为按次收费，请关注配额；缓存已尽量降低重复调用。
- 网点坐标为公开位置信息，距离为直线距离估算；机构数据以企业库返回为准，仅供政务合作位置参考，不含行内内部经营数据。
