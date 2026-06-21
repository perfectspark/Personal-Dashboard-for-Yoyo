# Personal Dashboard for Yoyo

个人首页仪表盘 — 一站式工作台，集成薪酬分析、知识库管理、健康追踪和日常工具。

## Features

| 模块 | 功能 |
|------|------|
| 💰 **薪酬总览** | Excel 数据驱动，月度趋势图、收入构成饼图、年度/月度明细表，支持上传 .xlsx 更新 |
| 📚 **ima 知识库** | 实时同步腾讯 ima 知识库，笔记内容在线查看（标题、段落、高亮、代码块等格式渲染） |
| ⚖️ **体重管理** | 日历视图，每日体重追踪，统计最新/最低/最高/变化 |
| 🕐 **时钟日历** | 实时数字时钟 + 日期星期 |
| 🔗 **常用链接** | DeepSeek、智谱、MiniMax、GitHub 等快捷入口，支持自定义增删 |
| ✅ **待办事项** | 简洁任务清单，可勾选完成，数据持久化到 localStorage |

## Quick Start

```bash
# 1. 浏览器直接打开
open index.html

# 2. 如需 ima 知识库同步，启动本地代理（一次性安装，开机自启）
bash install_proxy_service.sh
```

## Tech Stack

- 纯前端：HTML + CSS + JavaScript，零依赖
- 图表：Canvas 原生绘制（无第三方库）
- 数据：localStorage 持久化 + Excel 文件解析（SheetJS CDN）
- 代理：Python HTTP Server → ima OpenAPI
- 部署：任意静态文件服务器或浏览器直接打开

## Project Structure

```
.
├── index.html                  # 主页面（全部功能）
├── ima_proxy.py                # ima API 本地代理
├── install_proxy_service.sh    # LaunchAgent 一键安装
├── .gitignore
└── README.md
```

## ima 知识库同步

1. 获取凭证：[ima.qq.com/agent-interface](https://ima.qq.com/agent-interface)
2. 运行 `bash install_proxy_service.sh`（安装后台服务）
3. 在 Dashboard 的 ima 卡片中填入 Client ID 和 API Key
4. 点击 🔄 同步即可拉取知识库内容

## License

MIT
