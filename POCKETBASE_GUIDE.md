# PocketBase 实战使用指南

> 本文档基于 `AI WebApp 作品集` 项目踩坑经验整理。目标：**让任何 AI 拿到这份文档后，能直接上手使用 PocketBase，不需要重复试错。**

---

## 1. 一句话介绍 PocketBase

PocketBase 是一个**单文件二进制后端**，自带 SQLite 数据库 + REST API + 管理后台，零依赖、零配置，最适合：

- 给静态网站加一个轻量后端
- 快速做 MVP / Demo
- 不想部署复杂后端、但又需要跨设备共享数据

一句话：**不想写后端时的最优解。**

---

## 2. 当前项目服务器信息

| 项目 | 值 |
|------|------|
| PocketBase 版本 | **v0.39.3** (linux_amd64) |
| 服务地址 | `http://1.15.178.127:8090` |
| 管理后台 | `http://1.15.178.127:8090/_/` |
| 超级管理员邮箱 | `<YOUR_ADMIN_EMAIL>` ← 部署者需替换 |
| 超级管理员密码 | `<YOUR_ADMIN_PASSWORD>` ← 部署者需替换 |
| 当前 collection | `tools`（公开读写） |
| API 根路径 | `http://1.15.178.127:8090/api/collections/tools/records` |

> ⚠️ 上面的邮箱和密码是占位符，**部署者必须替换**。绝对不要把真实密码提交到公开仓库。

---

## 3. 30 秒快速启动（全新环境）

### 3.1 安装并启动

```bash
# 下载（Linux）
wget https://github.com/pocketbase/pocketbase/releases/download/v0.39.3/pocketbase_0.39.3_linux_amd64.zip
unzip pocketbase_0.39.3_linux_amd64.zip
chmod +x pocketbase

# 启动（监听所有网卡，默认端口 8090）
./pocketbase serve --http=0.0.0.0:8090
```

启动后第一次访问 `http://1.15.178.127:8090/_/` 会让你创建超级管理员账号。

### 3.2 验证服务

```bash
curl http://1.15.178.127:8090/api/health
# 预期: {"code":200,"message":"API is healthy.","data":{}}
```

如果返回 `200`，服务正常。

---

## 4. 管理员操作（需要 Token）

### 4.1 登录获取 Token

> ⚠️ **【坑 1】v0.22+ 端点变了**。老教程里写的 `/api/admins/auth-with-password` **已废弃**，新版本必须用 `/api/collections/_superusers/auth-with-password`。

```bash
curl -X POST http://1.15.178.127:8090/api/collections/_superusers/auth-with-password \
  -H "Content-Type: application/json" \
  -d '{"identity":"admin@example.com","password":"your_password"}'
```

**成功响应**：

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "record": { "id": "...", "email": "admin@example.com" }
}
```

**后续所有管理请求都必须带上**：

```bash
-H "Authorization: <token>"
```

> Token 有效期默认 14 天，过期需重新登录。

### 4.2 创建 Collection

```bash
curl -X POST http://1.15.178.127:8090/api/collections \
  -H "Content-Type: application/json" \
  -H "Authorization: <token>" \
  -d '{
    "name": "tools",
    "type": "base",
    "schema": [
      { "name": "name",        "type": "text", "required": true,  "options": { "min": 1, "max": 200 } },
      { "name": "url",         "type": "url",  "required": true,  "options": { "exceptDomains": [], "onlyDomains": [] } },
      { "name": "description", "type": "text", "required": false, "options": { "min": 0, "max": 1000 } }
    ],
    "listRule":   "",
    "viewRule":   "",
    "createRule": "",
    "updateRule": "",
    "deleteRule": ""
  }'
```

### 4.3 API 规则（Access Rules）速查

> ⚠️ **【坑 2】API 规则默认值是 `null`（仅超级管理员可访问），不是 `""`。**
> 想要"公开访问"必须显式设成 `""`（空字符串），否则前端 fetch 会拿到 404。

| Rule 值 | 含义 | 适用场景 |
|---------|------|---------|
| `null` | 仅超级管理员 | 后台私有数据 |
| `""` （空字符串）| **所有人可访问** | 公开数据（推荐公开站用这个） |
| `"id = @request.auth.id"` | 仅记录所有者 | 用户私有数据 |
| `"status = 'public'"` | 自定义条件 | 半公开 |

我们的 `tools` 集合需要让任何人提交和查看，所以全部设为 `""`。

### 4.4 修改已有 Collection

```bash
# 先 GET 拿到当前配置
curl -H "Authorization: <token>" \
  http://1.15.178.127:8090/api/collections/tools

# 再 PATCH 修改
curl -X PATCH http://1.15.178.127:8090/api/collections/<collection_id> \
  -H "Content-Type: application/json" \
  -H "Authorization: <token>" \
  -d '{ "listRule": "" }'
```

### 4.5 删除 Collection

```bash
curl -X DELETE http://1.15.178.127:8090/api/collections/<collection_id> \
  -H "Authorization: <token>"
```

---

## 5. 公共 API（无需 Token，公开读写）

> 前提：对应 Rule 已设为 `""`。

### 5.1 列出所有记录

```bash
GET /api/collections/tools/records?perPage=200&sort=-id
```

**查询参数**：

| 参数 | 作用 | 示例 |
|------|------|------|
| `perPage` | 每页条数（默认 30，最大 500）| `?perPage=200` |
| `page` | 第几页 | `?page=2` |
| `sort` | 排序字段，加 `-` 表示倒序 | `?sort=-id` （按 id 倒序）|
| `filter` | 过滤表达式 | `?filter=name='ChatGPT'` |
| `fields` | 指定返回字段 | `?fields=id,name,url` |

**返回结构**：

```json
{
  "items": [
    {
      "id": "abc123def",
      "collectionId": "tools",
      "collectionName": "tools",
      "name": "ChatGPT",
      "url": "https://chatgpt.com",
      "description": "OpenAI 推出的...",
      "created": "2024-01-01T00:00:00.000Z",
      "updated": "2024-01-01T00:00:00.000Z"
    }
  ],
  "page": 1,
  "perPage": 200,
  "totalItems": 6,
  "totalPages": 1
}
```

### 5.2 获取单条记录

```bash
GET /api/collections/tools/records/<id>
```

### 5.3 创建记录

```bash
POST /api/collections/tools/records
Content-Type: application/json

{
  "name": "ChatGPT",
  "url": "https://chatgpt.com",
  "description": "OpenAI 推出的对话式 AI 助手"
}
```

### 5.4 更新记录

```bash
PATCH /api/collections/tools/records/<id>
Content-Type: application/json

{ "description": "新的描述" }
```

### 5.5 删除记录

```bash
DELETE /api/collections/tools/records/<id>
```

---

## 6. 前端集成（JavaScript Fetch 模板）

### 6.1 拉取列表

```javascript
const PB = "http://1.15.178.127:8090";

async function loadTools() {
  const r = await fetch(`${PB}/api/collections/tools/records?perPage=200&sort=-id`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const data = await r.json();
  return data.items || [];
}
```

### 6.2 提交记录

```javascript
async function submitTool({ name, url, description }) {
  const r = await fetch(`${PB}/api/collections/tools/records`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, url, description: description || "" })
  });
  if (!r.ok) {
    const txt = await r.text();
    throw new Error(`HTTP ${r.status}: ${txt}`);
  }
  return await r.json();
}
```

### 6.3 完整使用流程

```javascript
// 1. 页面加载时拉取
const tools = await loadTools();
renderUI(tools);

// 2. 用户提交表单
try {
  await submitTool({ name: "MyApp", url: "https://my.app", description: "..." });
  // 3. 提交成功后重新拉取（保证列表最新）
  const updated = await loadTools();
  renderUI(updated);
} catch (err) {
  alert("提交失败: " + err.message);
}
```

---

## 7. Python 自动化脚本模板

`setup_pb.py`（项目根目录）就是我们的实战模板，**直接复用即可**：

```python
#!/usr/bin/env python3
import sys, json, urllib.request, urllib.error

PB_URL = "http://1.15.178.127:8090"

def request(method, path, data=None, headers=None):
    url = f"{PB_URL}{path}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    h = {"Content-Type": "application/json"}
    if headers: h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

# 1. 登录
status, data = request("POST", "/api/collections/_superusers/auth-with-password",
    {"identity": "admin@example.com", "password": "your_password"})
assert status == 200, data
token = data["token"]
auth = {"Authorization": token}

# 2. 创建 collection
request("POST", "/api/collections", {
    "name": "my_collection",
    "type": "base",
    "schema": [
        {"name": "title", "type": "text", "required": True, "options": {"min": 1, "max": 200}},
        {"name": "content", "type": "text", "required": False, "options": {"min": 0, "max": 10000}}
    ],
    "listRule": "", "viewRule": "", "createRule": "", "updateRule": "", "deleteRule": ""
}, headers=auth)

# 3. 验证
status, data = request("GET", "/api/collections/my_collection/records")
print(status, data)
```

---

## 8. 完整错误排查清单（踩过的坑）

| # | 症状 | 真实原因 | 正确做法 |
|---|------|---------|---------|
| 1 | 登录返回 404 `resource not found` | 端点写成了 `/api/admins/auth-with-password` | v0.22+ 改成 `/api/collections/_superusers/auth-with-password` |
| 2 | 创建 collection 成功但字段是空的 | 用错了字段名 | v0.22+ 用 `schema`（数组），不是 `fields` |
| 3 | 前端 fetch 报 `{"message":"Missing collection context.","status":404}` | 还没创建任何 collection | 先创建 collection 再访问 |
| 4 | 前端 fetch 报 401/403 | API Rule 默认是 `null`（仅管理员）| 公开访问必须设成 `""`（空字符串）|
| 5 | 前端 fetch 报 CORS 错误 | 没配置 CORS（少见）| PocketBase 默认允许所有 origin，无需配置 |
| 6 | `node --check xxx.js` 报 `SyntaxError: Unexpected identifier 'div'` | 压缩后的 JS 文件本身被损坏（编码错乱）| 重新打包 JS，或重写为源码 |
| 7 | PowerShell 跑 Python 报 `UnicodeEncodeError: 'gbk' codec` | Windows cmd 默认 GBK 编码 | 脚本里加 `sys.stdout.reconfigure(encoding='utf-8')` 或文件用 UTF-8 with BOM |
| 8 | `perPage` 太大拿不到数据 | 默认上限是 500 | 想拿全量用 `filter` 分页，或者用 500 + 多页 |
| 9 | 提交后字段值变成 `null` | 字段名拼错，或 schema 没声明 | 严格按 schema 里的 `name` 提交 |
| 10 | 浏览器一直报旧 JS 文件错误 | 浏览器缓存 | **强制刷新** `Ctrl+Shift+R`，或开无痕模式 |

---

## 9. 调试技巧

### 9.1 用 curl 验证（最可靠）

```bash
# 健康检查
curl http://1.15.178.127:8090/api/health

# 列出 collection
curl http://1.15.178.127:8090/api/collections

# 公开拉取数据
curl http://1.15.178.127:8090/api/collections/tools/records

# 详细日志（开 PocketBase 时加 --debug）
./pocketbase serve --http=0.0.0.0:8090 --debug
```

### 9.2 浏览器开发者工具看具体报错

F12 → Console / Network，**实际请求和响应体**比看代码靠谱一万倍。

### 9.3 自检清单（前端写完跑一遍）

- [ ] 拉取列表能拿到数据
- [ ] 提交表单返回 200 并生成新记录
- [ ] 再次拉取能看到刚提交的数据
- [ ] 关闭浏览器再打开，数据还在（验证持久化）
- [ ] 换一台电脑/手机访问，数据一样在（验证共享）

---

## 10. 常见场景速查

### 场景 1：公开留言板

```javascript
// listRule: "", createRule: "" 即可
await fetch(`${PB}/api/collections/messages/records`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: "hello" })
});
```

### 场景 2：用户私有数据（需要登录）

```javascript
// listRule: "user = @request.auth.id"
const r = await fetch(`${PB}/api/collections/notes/records`, {
  headers: { "Authorization": userToken }
});
```

### 场景 3：实时订阅（WebSocket）

```javascript
import PocketBase from 'pocketbase';
const pb = new PocketBase(PB);
pb.collection('tools').subscribe('*', (e) => {
  console.log('change:', e.action, e.record);
});
```

> 这个需要前端打包 PocketBase SDK（`npm i pocketbase`），约 30KB。

### 场景 4：上传文件

PocketBase 自带文件存储。schema 字段类型用 `file`，上传时用 `multipart/form-data`：

```bash
curl -X POST http://1.15.178.127:8090/api/collections/posts/records \
  -F "title=My Post" \
  -F "image=@./photo.jpg"
```

返回 URL 形如：`http://1.15.178.127:8090/api/files/<collection_id>/<record_id>/<filename>`

---

## 11. 数据备份

```bash
# 整个 PB 数据目录都在 pb_data/ 下，复制走就是备份
tar czf pb_backup_$(date +%Y%m%d).tar.gz pb_data/

# 恢复
tar xzf pb_backup_xxx.tar.gz
```

---

## 12. 总结：何时选 PocketBase

✅ **适合**：
- 个人项目 / Demo / MVP
- 静态网站 + 简单后端
- 不希望运维复杂后端
- 单人 / 小团队使用

❌ **不适合**：
- 高并发生产环境（SQLite + 单进程）
- 需要复杂权限模型
- 多节点分布式部署
- 大数据量分析

如果需要更复杂的能力，**Supabase**（基于 PostgreSQL）是更强大的替代品，但运维复杂度也高一个量级。

---

## 附录 A：本项目最小可用前端模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>PB Demo</title>
</head>
<body>
  <div id="app">加载中...</div>
  <script>
    const PB = "http://1.15.178.127:8090";
    const app = document.getElementById("app");

    async function load() {
      const r = await fetch(`${PB}/api/collections/tools/records?perPage=200`);
      const { items } = await r.json();
      app.innerHTML = items.map(t =>
        `<div><a href="${t.url}" target="_blank">${t.name}</a>: ${t.description || ''}</div>`
      ).join("");
    }

    load().catch(e => app.innerHTML = "加载失败: " + e.message);
  </script>
</body>
</html>
```

把这个文件存为 `index.html`，用 `python -m http.server 8000` 起一个静态服务，浏览器访问 `http://localhost:8000`，**10 行代码就能跨设备看到 PB 里的数据**。

---

**文档结束。** 如果你正在构建的应用需要"轻量、零运维、能存点数据"，直接用 PocketBase 就对了，参照本文档第 3-6 节即可上手。
