# AI WebApp 作品集

一个展示和分享 AI Web 应用的轻量社区站。用户可以浏览精选应用，也可以提交自己发现的好站，所有人可见。

## 特性

- 🔍 搜索 + 分类筛选
- 📤 提交作品（所有人可见，跨设备同步）
- 🌓 明暗主题切换
- 📱 响应式设计

## 技术栈

- 前端：原生 HTML + JavaScript + Tailwind CSS（CDN）
- 后端：[PocketBase](https://pocketbase.io)（单文件 SQLite 后端）

## 快速开始

```bash
# 1. 启动静态服务
python -m http.server 8000

# 2. 浏览器打开
http://localhost:8000
```

## 项目结构

```
.
├── index.html            # 主应用（单文件，自包含）
├── POCKETBASE_GUIDE.md   # PocketBase 后端使用文档
└── setup_pb.py           # PocketBase 初始化脚本
```

## 部署说明

前端：把 `index.html` 丢到任何静态服务器即可（Netlify / Vercel / Nginx / GitHub Pages 都行）。

后端：部署 PocketBase 并配置 `tools` collection。

## 许可

MIT
