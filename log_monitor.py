# log_monitor.py
import os
import gevent
from utils import should_keep_log_line
from custom_features import 扩展_自定义功能  # 自定义功能 custom_features.py


class LogMonitor:
    def __init__(self, server_name, log_path, filter_keywords, socketio_instance,
                 notifier=None, anticheat_keywords=None, anticheat_log_path=None):
        self.server_name = server_name
        self.log_path = log_path
        self.filter_keywords = filter_keywords
        self.socketio = socketio_instance
        self.notifier = notifier
        self.anticheat_keywords = anticheat_keywords or []
        self.anticheat_log_path = anticheat_log_path or f'AntiCheatLog_{server_name}.txt'
        self.running = True
        self.greenlet = None

    def start(self):
        self.greenlet = gevent.spawn(self._tail)
        print(f"[MONITOR] [{self.server_name}] 日志监控已启动")

    def _tail(self):
        while self.running:
            try:
                while not os.path.exists(self.log_path) and self.running:
                    gevent.sleep(1)

                with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, os.SEEK_END)
                    while self.running:
                        # 检测日志轮转
                        if f.tell() > os.path.getsize(self.log_path):
                            break

                        line = f.readline()
                        if not line:
                            gevent.sleep(0.1)
                            continue

                        line = line.rstrip('\n\r')
                        if not should_keep_log_line(line, self.filter_keywords):
                            continue

                        # 推送消息带上服务器名
                        self.socketio.emit(
                            'new_log',
                            {'server': self.server_name, 'line': line},
                            namespace='/'
                        )
                        if self.notifier:
                            self.notifier.try_send(line)

                        # 自定义功能
                        扩展_自定义功能(line, self.server_name)

                        # 保存反作弊日志 + [Server] 信息（每台服务器独立文件）
                        if (self.anticheat_keywords and any(kw in line for kw in self.anticheat_keywords)) \
                                or "] [Server thread/INFO]: [Server] " in line:
                            try:
                                with open(self.anticheat_log_path, 'a', encoding='utf-8') as f_out:
                                    f_out.write(line + '\n')
                            except Exception as e:
                                print(f"[AntiCheatLog-{self.server_name}] 写入失败: {e}")

                        gevent.sleep(0)
            except Exception as e:
                print(f"[MONITOR-{self.server_name}] 异常重启({type(e).__name__}): {e}")
                gevent.sleep(1)