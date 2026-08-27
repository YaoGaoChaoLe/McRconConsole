# config.py
import os
import sys
import yaml

class Config:
    def __init__(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)

        self.HOST = cfg.get('host', '127.0.0.1')
        self.PORT = cfg.get('port', 5000)
        self.LOG_DIR = cfg['log_dir']
        self.LATEST_LOG = os.path.join(self.LOG_DIR, 'latest.log')
        self.SERVER_PROPERTIES_PATH = cfg['server_properties_path']

        # API 访问密码：与 server.properties 中的 rcon.password 一致（由 main.py 设置）
        self.API_PASSWORD = None

        self.SAMPLE_INTERVAL_SECONDS = cfg['sample_interval_seconds']

        self.FILTER_KEYWORDS = cfg.get('filter_keywords', [])
        self.ALERT_KEYWORDS = cfg.get('alert_keywords', ['shutdown', 'crash'])
        self.ALERT_COOLDOWN = cfg.get('alert_cooldown_seconds', 20)
        self.PUBLIC_SERVER_ADDRESS = cfg.get('public_server_address', '')
        # 支持多个公网服务器地址。优先读取列表配置 public_server_addresses；
        # 若未配置列表，则回退到旧的单地址配置 public_server_address（向后兼容）。
        addrs = cfg.get('public_server_addresses', [])
        if isinstance(addrs, str):
            addrs = [addrs]
        if not addrs and self.PUBLIC_SERVER_ADDRESS:
            addrs = [self.PUBLIC_SERVER_ADDRESS]
        self.PUBLIC_SERVER_ADDRESSES = [a for a in addrs if a and str(a).strip()]
        self.CRASH_CONFIRM_DELAY = cfg.get('crash_confirm_delay_seconds', 3)

        self.CRASH_RECOVERY_COMMANDS = cfg.get('crash_recovery_commands', [])

        self.DB_PATH = cfg.get('db_path')
        if not self.DB_PATH:
            self.DB_PATH = os.path.join(os.path.dirname(__file__), 'stats.db')

        self.HIGHLIGHT_RULES = cfg.get('highlight_rules', [])
        self.ANTICHEAT_KEYWORDS = cfg.get('anticheat_keywords', [])
        if not self.HIGHLIGHT_RULES:
            self.HIGHLIGHT_RULES = [
                {"keyword": "error", "color": "#ff4343"},
                {"keyword": "warn", "color": "#ffcc00"},
                {"keyword": "触发了", "color": "#00ccff"},
                {"keyword": "反作弊", "color": "#00ccff"},
                {"keyword": "logged in with entity id", "color": "#888888"},
                {"keyword": "lost connection", "color": "#888888"},
                {"keyword": "left the game", "color": "#888888"},
                {"keyword": "joined the game", "color": "#888888"},
                {"keyword": "info", "color": "#ffffff"},
            ]

        email_cfg = cfg.get('email', {})
        self.MAIL_ENABLED = email_cfg.get('enabled', False)
        if self.MAIL_ENABLED:
            self.MAIL_SMTP_SERVER = email_cfg['smtp_server']
            self.MAIL_SMTP_PORT = email_cfg['smtp_port']
            self.MAIL_USER = email_cfg['user']
            self.MAIL_PASSWORD = email_cfg['password']
            self.MAIL_FROM = email_cfg['from']
            self.MAIL_TO = email_cfg['to']
            self.MAIL_SUBJECT = email_cfg['subject']
            self.MAIL_BODY = email_cfg['body']
        else:
            self.MAIL_SMTP_SERVER = self.MAIL_SMTP_PORT = self.MAIL_USER = self.MAIL_PASSWORD = None
            self.MAIL_FROM = self.MAIL_TO = self.MAIL_SUBJECT = self.MAIL_BODY = None

    def parse_server_properties(self):
        if not os.path.exists(self.SERVER_PROPERTIES_PATH):
            print(f"错误: server.properties 文件不存在: {self.SERVER_PROPERTIES_PATH}")
            sys.exit(1)
        props = {}
        with open(self.SERVER_PROPERTIES_PATH, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    props[k.strip()] = v.strip()
        enable_rcon = props.get('enable-rcon', 'false').lower() == 'true'
        if not enable_rcon:
            print("错误: server.properties 中 enable-rcon 未设置为 true")
            sys.exit(1)
        rcon_port = int(props.get('rcon.port', 25575))
        rcon_password = props.get('rcon.password')
        if not rcon_password:
            print("错误: server.properties 中未设置 rcon.password")
            sys.exit(1)
        server_ip = props.get('server-ip', '').strip()
        rcon_host = server_ip if server_ip and server_ip != '0.0.0.0' else '127.0.0.1'
        return rcon_host, rcon_port, rcon_password