# **注意：本仓库 包含 两个项目**
---
# 次要项目——离线日志分析

如果您**只分析日志**，这个会适合你：

- https://yaogaochaole.github.io/McRconConsole/
- 选择你的服务器日志文件 `latest.log`，即可分析日志。
---

# 主要项目——McRconConsole 实时在线控制台

## 主要功能：
<img width="2313" height="8116" alt="1" src="https://github.com/user-attachments/assets/c768491d-c85f-4749-833e-1dac9ae0177d" />

## 其它功能：
- 服务器崩溃处理 – 自动检查服务器是否崩溃。崩溃后可以发送邮件进行提示、执行预设的批处理脚本（例如自动重启服务器）
- 扩展代码 – `custom_features.py` 允许你注入自己的新代码。

## 下载并使用

1. 下载: [点我下载](https://github.com/YaoGaoChaoLe/McRconConsole/releases)

2. 打开 服务器的配置文件 `server.properties`:
   - 将默认的 `enable-rcon=false` 改成 `enable-rcon=true`
   - 将默认为空的 `rcon.password` 随便设一个密码，确保它不是空的。
   - 如果需要管理多个服务器：请确保 各个服务器配置中的`rcon.port`端口号不能一样。

3. 打开 本项目的 `config.yml`，填写正确的配置。

4. 运行 `McRconConsole.exe`。
## 一切准备就绪，祝您使用愉快！

## 补充：扩展代码

本项目的 `custom_features.py`，每次有新日志行出现，都会调用其中的 `扩展_自定义功能(line)` 函数。你可以在此函数中实现任何自定义逻辑，例如：

- 自动封禁触发敏感词的玩家
- 根据时间段或在线人数执行 `/transfer` 转移玩家
- and more...


---
## 开发者 —— 从源码部署
```
# 创建虚拟环境
{{你的python位置}}\python.exe -m venv myenv
# D:\_Project\Python\python_x64\python.exe -m venv myenv

# 激活/进入虚拟环境
myenv\Scripts\activate

# 安装环境
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --only-binary=gevent
```

使用cmd打包
```
pyinstaller -F -n McRconConsole ^
  --collect-all gevent ^
  --collect-all engineio ^
  --collect-all flask_socketio ^
  --hidden-import engineio.async_drivers.gevent ^
  --hidden-import engineio.async_drivers.threading ^
  main.py
```
发行文件目录需要包含：
```
 McRconConsole.exe + vendor
 config.yml
 custom_features.py
 main_console_rcon.html
```
[MIT 许可证](LICENSE)。

如有好的建议或功能需求，请通过 GitHub 反馈。

本项目代码完全由 deepseek v4 生成，个人定制自用，请自行检查代码。
