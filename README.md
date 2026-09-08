## Minecraft 服务器日志监控与RCON控制台

日志实时查看、RCON 远程命令、在线人数统计、系统性能监控、崩溃告警与自动恢复一体的 Minecraft 服务端管理面板。

**离线分析版：** https://yaogaochaole.github.io/McRconConsole/

## 🚀 主要功能

- **实时日志** – 实时推送 latest.log 日志，高亮日志行、过滤某些日志行。
- **RCON 远程命令** – 发送任意mc游戏命令。
- **在线人数趋势** – 定时采样并绘制人数曲线图
- **系统性能监控** – 实时展示CPU各核心使用率、内存占用、网络上下行速率。
- **玩家登录 IP 记录** – 通过 `logged in` 文本解析日志，按 IP 分组显示登录历史，支持批量查询 IP 归属地。
- **反作弊日志** – 自动提取含 `anticheat_keywords` 的行及 `[Server]` 消息，集中展示。(本项目以GrimAnticheat为例配置)
- **崩溃告警 & 自动恢复** – 检测到 `alert_keywords` 后，检查 `crash-reports` 目录，确认真崩溃后发送邮件告警+执行预设恢复命令（如重启服务器）。
- **离线日志分析** – 无需连接后端，直接上传 `latest.log` 就能分析。https://yaogaochaole.github.io/McRconConsole/
- **扩展代码** – `custom_features.py` 允许你注入自定义逻辑。

---


## 📦 安装与部署

### 1. 环境准备
- Python 3.8+
- Windows / Linux / macOS

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

文件 `config.yml` 是主配置，所有设置在此文件中修改，各个参数说明已在文件中注释，这里不再赘述。
> **重要**：服务器配置文件 `server.properties` 必须设置 `enable-rcon=true` 并设置 `rcon.password`。

---

## 🚀 运行
### 首次启动
1. 确保 `config.yml` 已正确配置。
2. 确保服务器配置 `server.properties` 已正确配置：令`enable-rcon=true`、为`rcon.password`设定一个强密码。
3. 运行 python main.py，或者 运行`start 一键启动.bat` 启动程序。控制台将输出访问地址和密码（即 `rcon.password`）
4. 浏览器打开 `http://127.0.0.1:5000/main_console_rcon.html`，输入`rcon.password`密码登录。
5. 如有需要，自行内网穿透。


## 🧬 自定义扩展
项目提供了 `custom_features.py`，每次有新日志行被处理时都会调用其中的 `扩展_自定义功能(line)` 函数。你可以在此函数中实现任何自定义逻辑，例如：

- 自动封禁触发敏感词的玩家
- 根据时间段或在线人数执行 `/transfer` 转移玩家
- 统计特定事件并记录到外部文件
- and more...


---

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)，允许自由使用、修改和分发，但需保留版权声明。
如有好的建议或功能需求，请通过 GitHub 反馈。代码100%由ai生成，完全个人定制自用 :)

---
