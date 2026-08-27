# main.py
from gevent import monkey
monkey.patch_all()
import os

from config import Config
from rcon_client import RCONClient
from db import StatsDatabase
from mail_notifier import MailNotifier
from log_monitor import LogMonitor
from performance_monitor import PerformanceMonitor
from sampling_scheduler import SamplingScheduler
from app import create_app
from flask_socketio import SocketIO

if __name__ == '__main__':
    cfg = Config('config.yml')
    rcon_host, rcon_port, rcon_pass = cfg.parse_server_properties()
    cfg.API_PASSWORD = rcon_pass

    rcon_client = RCONClient(rcon_host, rcon_port, rcon_pass, cfg.PUBLIC_SERVER_ADDRESSES)
    db = StatsDatabase(cfg.DB_PATH)
    sampler = SamplingScheduler(cfg.SAMPLE_INTERVAL_SECONDS, rcon_client, db)

    mail_notifier = None
    if cfg.MAIL_ENABLED:
        # 构建 crash-reports 目录路径：log_dir 的父目录下的 crash-reports
        crash_reports_dir = os.path.join(os.path.dirname(cfg.LOG_DIR), 'crash-reports')
        mail_notifier = MailNotifier(
            keywords=cfg.ALERT_KEYWORDS, cooldown_sec=cfg.ALERT_COOLDOWN,
            smtp_server=cfg.MAIL_SMTP_SERVER, port=cfg.MAIL_SMTP_PORT,
            user=cfg.MAIL_USER, pwd=cfg.MAIL_PASSWORD,
            from_addr=cfg.MAIL_FROM, to_addr=cfg.MAIL_TO,
            subject=cfg.MAIL_SUBJECT, body=cfg.MAIL_BODY,
            crash_commands=cfg.CRASH_RECOVERY_COMMANDS,
            scheduler=sampler,
            crash_reports_dir=crash_reports_dir,
            crash_confirm_delay=cfg.CRASH_CONFIRM_DELAY
        )

    socketio = SocketIO(app=None, cors_allowed_origins="*")
    app = create_app(cfg, rcon_client, db, mail_notifier, socketio)
    socketio.init_app(app, cors_allowed_origins="*")

    log_monitor = LogMonitor(cfg.LATEST_LOG, cfg.FILTER_KEYWORDS, socketio, mail_notifier,anticheat_keywords=cfg.ANTICHEAT_KEYWORDS)
    log_monitor.start()
    sampler.start()
    performance_monitor = PerformanceMonitor(socketio, interval=1.0)
    performance_monitor.start()

    print("=" * 60)
    print(f"服务启动: http://{cfg.HOST}:{cfg.PORT}/main_console_rcon.html  密码: {cfg.API_PASSWORD}")
    print("=" * 60)
    socketio.run(app, host=cfg.HOST, port=cfg.PORT, debug=False)