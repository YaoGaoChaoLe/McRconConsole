## Minecraft 服务器日志监控与RCON控制台

日志实时查看、RCON 远程命令、在线人数统计、系统性能监控、崩溃告警与自动恢复一体的 Minecraft 服务端管理面板。

**离线分析版：** https://yaogaochaole.github.io/minecraftServerLogAnalysis/

## 🚀 主要功能

- **实时日志** – 推送日志，支持高亮规则、关键词过滤、自动滚动与换行。
- **RCON 远程命令** – 发送任意游戏命令，支持历史记录（上下键）。
- **在线人数趋势** – 定时采样并绘制人数曲线图
- **系统性能监控** – 实时展示CPU各核心使用率、内存占用、网络上下行速率。
- **玩家登录 IP 记录** – 通过 `logged in` 文本解析日志，按 IP 分组显示登录历史，支持批量查询 IP 归属地。
- **反作弊日志** – 自动提取含 `anticheat_keywords` 的行及 `[Server]` 消息，集中展示。(本项目以GrimAnticheat为例配置)
- **崩溃告警 & 自动恢复** – 检测到 `alert_keywords` 后，检查 `crash-reports` 目录，确认真崩溃后发送邮件告警+执行预设恢复命令（如重启服务器）。
- **离线日志分析** – 无需连接后端，直接上传 `latest.log` 文件或粘贴内容即可浏览历史日志（支持完整加载）。
- **高亮规则可配置** – 通过 `config.yml` 自定义关键词颜色，支持多级优先级。
- **扩展代码** – `custom_features.py` 允许你注入自定义逻辑。

---


## 📦 安装与部署

### 1. 环境准备
- Python 3.8 或更高版本（推荐64位）
- Windows / Linux / macOS 均可

### 2. 创建虚拟环境（推荐）
```bash
# 使用系统 Python 创建虚拟环境
python -m venv myenv

# 激活虚拟环境
# Windows:
myenv\Scripts\activate
# Linux / macOS:
source myenv/bin/activate
```

### 3. 安装依赖
```bash
# 升级打包工具
python -m pip install --upgrade pip setuptools wheel

# 安装核心依赖（国内可使用清华镜像加速）
pip install flask flask-socketio flask-compress mcrcon pyyaml psutil -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 安装 gevent（强制使用预编译二进制，避免编译失败）
pip install setuptools==58.0.0
pip install gevent --only-binary gevent -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

> **注意**：`gevent` 依赖 `setuptools` 特定版本，请务必按上述顺序安装。

---

## ⚙️ 配置文件 `config.yml`

文件 `config.yml` 是主配置，所有设置在此修改。关键字段说明如下：

| 字段 | 说明 |
|------|------|
| `host` / `port` | Web 服务监听地址和端口（默认 `127.0.0.1:5000`） |
| `log_dir` | 服务器日志目录，必须包含 `latest.log` |
| `server_properties_path` | `server.properties` 绝对路径，用于读取 RCON 配置 |
| `filter_keywords` | 包含这些词的日志行将**不显示**在前端 |
| `alert_keywords` | 触发邮件告警的关键词（如 `crash`, `shutdown`） |
| `crash_recovery_commands` | 崩溃确认后执行的系统命令（例如重启脚本） |
| `email` 部分 | 启用后需配置 SMTP 服务器、授权码、收件人等 |
| `highlight_rules` | 前端高亮规则，按优先级排列 |
| `anticheat_keywords` | 包含这些词的日志会单独归入“反作弊日志”标签页 |
| `sample_interval_seconds` | 在线人数采样间隔（秒），默认 300 秒 |
| `crash_confirm_delay_seconds` | 检测到告警关键词后，等待此秒数再检查崩溃报告 |

> **重要**：`server.properties` 中必须设置 `enable-rcon=true` 并设置 `rcon.password`（该密码同时用作 API 访问令牌）。

---

## 🚀 运行
### 首次启动
1. 确保 `config.yml` 已正确配置。
2. 确保服务器配置 `server.properties` 已正确配置(令`enable-rcon=true`、为`rcon.password`设定一个强密码。)。
3. 运行后控制台将输出访问地址和密码（即 `rcon.password`）。
4. 浏览器打开 `http://127.0.0.1:5000/main_console_rcon.html`，输入密码登录。
5. 如有需要，自行内网穿透。

### 方式一：直接运行 Python
```bash
python main.py
```

### 方式二：使用一键启动脚本（Windows）
双击 `start 一键启动.bat`（自动激活虚拟环境并运行 `main.py`）。

---

---

## 🧬 自定义扩展
项目提供了 `custom_features.py`，每次有新日志行被处理时都会调用其中的 `扩展_自定义功能(line)` 函数。你可以在此函数中实现任何自定义逻辑，例如：

- 自动封禁触发敏感词的玩家
- 根据时间段或在线人数执行 `/transfer` 转移玩家
- 统计特定事件并记录到外部文件
- and more...

**示例代码**已包含在文件中（基于关键词 `Meteor on Crack` 封禁玩家），可根据需求修改。

---

## 📁 文件结构

```
├── app.py                     # Flask 应用与路由
├── config.py                  # 配置加载类
├── config.yml                 # 主配置文件（用户修改）
├── custom_features.py         # 自定义扩展入口
├── db.py                      # SQLite 数据库操作
├── log_monitor.py             # 日志尾随与分发
├── mail_notifier.py           # 邮件告警与崩溃恢复
├── main.py                    # 启动入口
├── performance_monitor.py     # 系统性能采集
├── rcon_client.py             # RCON 客户端（带重连机制）
├── sampling_scheduler.py      # 在线人数采样调度器
├── utils.py                   # 工具函数（日志过滤、缓存）
├── main_console_rcon.html     # 前端单页应用（所有交互）
├── start 一键启动.bat         # Windows 快速启动脚本
├── stats.db                   # 自动生成的 SQLite 数据库（采样数据）
└── AntiCheatLog.txt           # 自动生成的反作弊日志存档
```

---

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)，允许自由使用、修改和分发，但需保留版权声明。
如有好的建议或功能需求，请通过 GitHub 反馈。代码100%由ai生成，完全个人定制自用 :)

---
