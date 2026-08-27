# log_monitor.py
import os
import gevent
from utils import should_keep_log_line
from custom_features import 扩展_自定义功能  # 自定义功能 custom_features.py

class LogMonitor:
    def __init__(self, log_path, filter_keywords, socketio_instance, notifier=None, anticheat_keywords=None):
        self.log_path = log_path
        self.filter_keywords = filter_keywords
        self.socketio = socketio_instance
        self.notifier = notifier
        self.anticheat_keywords = anticheat_keywords or []
        self.running = True
        self.greenlet = None

    def start(self):
        self.greenlet = gevent.spawn(self._tail)
        print("[MONITOR] 日志监控已启动")

    def _tail(self):
        # ===== 偷懒改动第 1 处：外层死循环 + 兜底异常捕获（绝不让协程死掉） =====
        while self.running:
            try:
                while not os.path.exists(self.log_path) and self.running:
                    gevent.sleep(1)
                
                with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, os.SEEK_END)
                    while self.running:
                        # ===== 偷懒改动第 2 处：一行代码检测日志轮转（文件被替换/截断） =====
                        # 原理：如果当前读取指针位置 > 磁盘上的文件大小，说明文件被重写了，直接跳出内层循环，外层循环会自动重新 open
                        if f.tell() > os.path.getsize(self.log_path):
                            break

                        line = f.readline()
                        if not line:
                            gevent.sleep(0.1)
                            continue
                        
                        line = line.rstrip('\n\r')
                        if not should_keep_log_line(line, self.filter_keywords):
                            continue
                        
                        # 原有推送逻辑
                        self.socketio.emit('new_log', line, namespace='/')
                        if self.notifier:
                            self.notifier.try_send(line)

                        # ===== 自定义功能（注意：如果这里崩了，外层 try 照样能兜底） =====
                        扩展_自定义功能(line)

                        # ===== 保存反作弊日志 + [Server] 信息 =====
                        if (self.anticheat_keywords and any(kw in line for kw in self.anticheat_keywords)) or "] [Server thread/INFO]: [Server] " in line:
                            try:
                                with open('AntiCheatLog.txt', 'a', encoding='utf-8') as f_out:
                                    f_out.write(line + '\n')
                            except Exception as e:
                                print(f"[AntiCheatLog] 写入失败: {e}")

                        gevent.sleep(0)
            except Exception as e:
                # 偷懒绝招：不管什么错（文件锁、权限、自定义功能炸了），统统吞掉并重启循环
                print(f"[MONITOR] 异常重启({type(e).__name__}): {e}")
                gevent.sleep(1)  # 给系统 1 秒喘息，避免死循环占满 CPU