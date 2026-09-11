# main.py
import builtins
import time
from gevent import monkey
monkey.patch_all()
import sys
import os

# 如果是打包后的 exe，将工作目录切换到 exe 所在目录
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

# ===== 全局 print 添加时间戳 =====
_original_print = builtins.print
def _timestamp_print(*args, **kwargs):
    timestamp = time.strftime('[%Y-%m-%d %H:%M:%S]')
    _original_print(timestamp, *args, **kwargs)
builtins.print = _timestamp_print

from config import Config
from rcon_client import RCONManager
from db import StatsDatabase
from mail_notifier import MailNotifier
from log_monitor import LogMonitor
from performance_monitor import PerformanceMonitor
from sampling_scheduler import SamplingScheduler
from app import create_app
from flask_socketio import SocketIO


if __name__ == '__main__':
    cfg = Config('config.yml')

    # 多服务器 RCON 管理器（内部同时维护一个"聚合客户端"用于统计）
    rcon_manager = RCONManager(cfg.servers)

    # ===== 把 rcon_manager 挂到 __main__ 上，方便 custom_features.py 访问 =====
    import __main__
    __main__.rcon_manager = rcon_manager
    # ==========================================================================

    # 统计数据库（表结构不变）
    db = StatsDatabase(cfg.DB_PATH)

    # 采样器：用聚合客户端，把所有服务器地址的人数加起来写入数据库
    sampler = SamplingScheduler(
        cfg.SAMPLE_INTERVAL_SECONDS,
        rcon_manager.aggregate_client,
        db
    )

    socketio = SocketIO(app=None, cors_allowed_origins="*")
    app = create_app(cfg, rcon_manager, db, socketio)
    socketio.init_app(app, cors_allowed_origins="*")

    # ===== 每台服务器一个 LogMonitor + 可选 MailNotifier =====
    for name, srv_cfg in cfg.servers.items():
        mail_notifier = None
        if srv_cfg.MAIL_ENABLED:
            mail_notifier = MailNotifier(
                keywords=srv_cfg.ALERT_KEYWORDS,
                cooldown_sec=srv_cfg.ALERT_COOLDOWN,
                smtp_server=srv_cfg.MAIL_SMTP_SERVER,
                port=srv_cfg.MAIL_SMTP_PORT,
                user=srv_cfg.MAIL_USER,
                pwd=srv_cfg.MAIL_PASSWORD,
                from_addr=srv_cfg.MAIL_FROM,
                to_addr=srv_cfg.MAIL_TO,
                subject=srv_cfg.MAIL_SUBJECT,
                body=srv_cfg.MAIL_BODY,
                crash_commands=srv_cfg.CRASH_RECOVERY_COMMANDS,
                scheduler=sampler,
                crash_reports_dir=srv_cfg.CRASH_REPORTS_DIR,
                crash_confirm_delay=srv_cfg.CRASH_CONFIRM_DELAY
            )

        log_monitor = LogMonitor(
            server_name=name,
            log_path=srv_cfg.LATEST_LOG,
            filter_keywords=cfg.FILTER_KEYWORDS,
            socketio_instance=socketio,
            notifier=mail_notifier,
            anticheat_keywords=cfg.ANTICHEAT_KEYWORDS,
            anticheat_log_path=srv_cfg.ANTICHEAT_LOG
        )
        log_monitor.start()

    sampler.start()
    performance_monitor = PerformanceMonitor(socketio, interval=1.0)
    performance_monitor.start()

    print("=" * 60)
    print(f"服务启动: http://{cfg.HOST}:{cfg.PORT}/main_console_rcon.html  密码: {cfg.ADMIN_PASSWORD}")
    print(f"管理服务器: {list(cfg.servers.keys())}")
    print(f"聚合统计地址: {rcon_manager.all_addresses}")
    print("=" * 60)
    socketio.run(app, host=cfg.HOST, port=cfg.PORT, debug=False)