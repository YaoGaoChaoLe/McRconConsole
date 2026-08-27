# mail_notifier.py
import time
import os
import subprocess
import smtplib
from email.mime.text import MIMEText
import gevent

class MailNotifier:
    def __init__(self, keywords, cooldown_sec, smtp_server, port, user, pwd,
                 from_addr, to_addr, subject, body, crash_commands=None, scheduler=None,
                 crash_reports_dir=None, crash_confirm_delay=3):
        self.keywords = keywords
        self.cooldown = cooldown_sec
        self.smtp_server = smtp_server
        self.port = port
        self.user = user
        self.pwd = pwd
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.subject = subject
        self.body = body
        self.last_time = 0
        self._lock = gevent.lock.Semaphore()
        self.crash_commands = crash_commands or []
        self.scheduler = scheduler
        self.crash_reports_dir = crash_reports_dir
        self.crash_confirm_delay = crash_confirm_delay

    def contains_keyword(self, text):
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.keywords)

    def _check_crash_report_recent(self, seconds=30):
        """检查 crash-reports 目录下是否有最近 seconds 秒内创建/修改的 .txt 文件"""
        if not self.crash_reports_dir:
            print("[CRASH] crash_reports_dir 为空，无法检查")
            return False
        if not os.path.isdir(self.crash_reports_dir):
            print(f"[CRASH] 目录不存在: {self.crash_reports_dir}")
            return False
        now = time.time()
        try:
            files = os.listdir(self.crash_reports_dir)
            if not files:
                print(f"[CRASH] 目录 {self.crash_reports_dir} 为空")
                return False
            for filename in files:
                if not filename.endswith('.txt'):
                    continue
                filepath = os.path.join(self.crash_reports_dir, filename)
                mtime = os.path.getmtime(filepath)
                age = now - mtime
                if age <= seconds:
                    print(f"[CRASH] 发现新的崩溃报告: {filepath} (修改时间差 {age:.1f}秒)")
                    return True
            print(f"[CRASH] 未找到 {seconds} 秒内修改的 .txt 文件")
            return False
        except Exception as e:
            print(f"[CRASH] 检查崩溃报告目录失败: {e}")
            return False

    def _send_mail(self):
        msg = MIMEText(self.body, 'plain', 'utf-8')
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr
        msg['Subject'] = self.subject
        try:
            if self.port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.port)
                server.starttls()
            server.login(self.user, self.pwd)
            server.send_message(msg)
            server.quit()
            print("[MAIL] 邮件发送成功")
        except Exception as e:
            print(f"[MAIL] 发送失败: {e}")

    def _run_recovery_commands(self):
        if self.scheduler:
            self.scheduler.force_sample_now()
        if not self.crash_commands:
            return
        gevent.sleep(2)
        print("[RECOVERY] 开始执行崩溃恢复命令...")
        for idx, cmd in enumerate(self.crash_commands):
            try:
                if idx == len(self.crash_commands) - 1:
                    gevent.sleep(1)
                subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[RECOVERY] 已启动命令: {cmd}")
            except Exception as e:
                print(f"[RECOVERY] 启动命令失败: {cmd} -> {e}")

    def try_send(self, line):
        # 聊天线程相关日志不触发告警
        if "[Not Secure]" in line or "[Async Chat Thread]" in line:
            return
        if not self.contains_keyword(line):
            return

        # 延迟确认：等待 3 秒后检查崩溃报告文件
        def delayed_confirm():
            # 先等待初始延迟
            gevent.sleep(self.crash_confirm_delay)
            # 循环重试，最多尝试 5 次，每次间隔 3 秒，总共覆盖约 15 秒
            for attempt in range(5):
                if self._check_crash_report_recent(seconds=30):  # 检查最近30秒内文件
                    now = time.time()
                    with self._lock:
                        if now - self.last_time >= self.cooldown:
                            self.last_time = now
                            gevent.spawn(self._send_mail)
                            gevent.sleep(0)
                            gevent.spawn(self._run_recovery_commands)
                            print(f"[TRIGGER] 确认真崩溃（第{attempt+1}次检查）: {line[:200]}")
                            return
                gevent.sleep(3)  # 等待3秒后重试
            print(f"[IGNORE] 等待 {self.crash_confirm_delay + 3*5} 秒后仍未发现崩溃报告，忽略本次触发: {line[:200]}")

        gevent.spawn(delayed_confirm)