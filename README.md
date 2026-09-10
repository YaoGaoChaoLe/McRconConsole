## 主要功能

- **实时日志** – 实时推送 latest.log 日志，高亮日志行、过滤某些日志行。
- **远程命令** – 通过rcon发送任意mc Server游戏命令。
- **在线人数统计** – 自动绘制人数曲线图。
- **性能监控** – 实时展示CPU各核心使用率、内存占用、网络上下行速率。
- **玩家IP记录** – 可视化进过服务器的玩家IP，快捷查询ip地址，以及通过ip辨别那些玩家开小号。
- **反作弊日志** – 自动提取含 `anticheat_keywords` 的行及 `[Server]` 消息，集中展示。(本项目以GrimAnticheat为例配置)
- **服务器崩溃处理** – 自动检查服务器是否崩溃。崩溃后可以发送邮件进行提示、执行预设的批处理脚本（例如自动重启服务器）
- **扩展代码** – `custom_features.py` 允许你注入自己的新代码。

---


## 通过源码部署

### 1. 环境要求
- Python 3.8+
- 互联网连接
- Windows / Linux / macOS
  (本项目基于 window10专业版 开发，其它系统可能会出现小问题。)

### 2. 创建、进入 虚拟环境（可选）（推荐）
```bash
# Windows：
python -m venv myenv
myenv\Scripts\activate

# Linux / macOS；
python -m venv myenv
source myenv/bin/activate
```

### 3. 安装依赖
```bash
# 安装依赖：
pip install -r requirements.txt --only-binary=gevent

# 如果中国大陆网络安装很慢，那就用这个：
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ --only-binary=gevent
```


### 4.写好配置文件 & 运行
1. 确保 本项目的 `config.yml` 已正确配置。
2. 确保 服务器配置 `server.properties` 已正确配置：
   - 将默认的`enable-rcon=false` 改成 `enable-rcon=true`
   - 将默认为空的 `rcon.password` 设定一个**强密码**
3. 启动程序：运行 `python main.py`，或者 运行`start 一键启动.bat` 。
4. 如有需要，自行内网穿透。

## 补充：扩展代码
本项目的 `custom_features.py`，每次有新日志行出现，都会调用其中的 `扩展_自定义功能(line)` 函数。你可以在此函数中实现任何自定义逻辑，例如：

- 自动封禁触发敏感词的玩家
- 根据时间段或在线人数执行 `/transfer` 转移玩家
- 统计特定事件并记录到外部文件
- and more...


---

[MIT 许可证](LICENSE)。
如有好的建议或功能需求，请通过 GitHub 反馈。
本项目代码完全由 deepseek v4 生成，个人定制自用，请自行检查代码。

**另一个项目：** https://yaogaochaole.github.io/McRconConsole/
  选择本地服务器日志，然后进行日志分析。
---
