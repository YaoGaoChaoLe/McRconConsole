# config.py
import os
import sys
import yaml

def _fatal_error(msg):
    print(msg)
    print()
    input("按回车键退出程序...")
    sys.exit(1)

class ServerConfig:
    """单个服务器的配置"""

    def __init__(self, cfg, global_cfg):
        self.name = cfg['name']
        self.SERVER_PROPERTIES_PATH = cfg['server_properties_path']
        self.LOG_DIR = os.path.join(os.path.dirname(self.SERVER_PROPERTIES_PATH), 'logs')
        self.LATEST_LOG = os.path.join(self.LOG_DIR, 'latest.log')
        self.CRASH_REPORTS_DIR = os.path.join(os.path.dirname(self.LOG_DIR), 'crash-reports')
        # 每台服务器独立的反作弊日志文件
        self.ANTICHEAT_LOG = f'AntiCheatLog_{self.name}.txt'

        # 公网地址（用于查询在线人数）
        addrs = cfg.get('public_server_addresses', [])
        if isinstance(addrs, str):
            addrs = [addrs]
        self.PUBLIC_SERVER_ADDRESSES = [a for a in addrs if a and str(a).strip()]

        # 崩溃恢复命令
        self.CRASH_RECOVERY_COMMANDS = cfg.get('crash_recovery_commands', [])

        # 崩溃告警关键词与冷却，可从全局继承
        self.ALERT_KEYWORDS = cfg.get('alert_keywords',
                                      global_cfg.get('alert_keywords', ['shutdown', 'crash']))
        self.ALERT_COOLDOWN = cfg.get('alert_cooldown_seconds',
                                      global_cfg.get('alert_cooldown_seconds', 20))
        self.CRASH_CONFIRM_DELAY = cfg.get('crash_confirm_delay_seconds',
                                           global_cfg.get('crash_confirm_delay_seconds', 10))

        # 邮件配置：服务器可覆盖全局
        email_cfg = cfg.get('email', global_cfg.get('email', {})) or {}
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
            self.MAIL_SMTP_SERVER = None
            self.MAIL_SMTP_PORT = None
            self.MAIL_USER = None
            self.MAIL_PASSWORD = None
            self.MAIL_FROM = None
            self.MAIL_TO = None
            self.MAIL_SUBJECT = None
            self.MAIL_BODY = None

        # RCON 信息从 server.properties 解析
        self.rcon_host, self.rcon_port, self.rcon_password = self._parse_server_properties()

    def _parse_server_properties(self):
        if not os.path.exists(self.SERVER_PROPERTIES_PATH):
            _fatal_error(f"错误: [{self.name}] 服务器配置文件server.properties 不存在: {self.SERVER_PROPERTIES_PATH}")

        props = {}
        with open(self.SERVER_PROPERTIES_PATH, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    props[k.strip()] = v.strip()

        if props.get('enable-rcon', 'false').lower() != 'true':
            _fatal_error(f"错误: [{self.name}] 服务器配置文件server.properties 中的 enable-rcon 未设置为 true")

        try:
            rcon_port = int(props.get('rcon.port', 25575))
        except ValueError:
            _fatal_error(f"错误: [{self.name}] 服务器配置文件server.properties 中的 rcon.port 不是合法数字: {props.get('rcon.port')}，你应该设置0 ~ 65535范围内的一个数字")

        rcon_password = props.get('rcon.password')
        if not rcon_password:
            _fatal_error(f"错误: [{self.name}] 服务器配置文件server.properties 中的 rcon.password 是空的.请在里面 随意设定一个纯英文的密码")

        server_ip = props.get('server-ip', '').strip()
        rcon_host = server_ip if server_ip and server_ip != '0.0.0.0' else '127.0.0.1'
        return rcon_host, rcon_port, rcon_password


class Config:
    def __init__(self, config_path):
        if not os.path.exists(config_path):
            _fatal_error(f"错误: 配置文件不存在: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
        except yaml.YAMLError as e:
            _fatal_error(f"错误: config.yml 格式错误: {e}")

        if not isinstance(cfg, dict):
            _fatal_error("错误: config.yml 内容为空或格式不正确")

        self.HOST = cfg.get('host', '127.0.0.1')
        self.PORT = cfg.get('port', 5000)
        self.ADMIN_PASSWORD = cfg.get('admin_password', '')
        # 兼容部分旧代码里可能仍在使用 API_PASSWORD 的地方
        self.API_PASSWORD = self.ADMIN_PASSWORD

        self.DB_PATH = cfg.get('db_path') or os.path.join(os.path.dirname(__file__), 'stats.db')
        self.SAMPLE_INTERVAL_SECONDS = cfg.get('sample_interval_seconds', 300)

        self.FILTER_KEYWORDS = cfg.get('filter_keywords', [])
        self.ANTICHEAT_KEYWORDS = cfg.get('anticheat_keywords', [])

        self.HIGHLIGHT_RULES = cfg.get('highlight_rules', [])
        if not self.HIGHLIGHT_RULES:
            self.HIGHLIGHT_RULES = [
                {"keyword": "error", "color": "#ff4343"},
                {"keyword": "warn", "color": "#ffcc00"},
                {"keyword": "触发了", "color": "#00ccff"},
                {"keyword": "反作弊", "color": "#00ccff"},
                {"keyword": "info", "color": "#ffffff"},
            ]

        self.servers = {}
        for srv_cfg in cfg.get('servers', []):
            srv = ServerConfig(srv_cfg, cfg)
            if srv.name in self.servers:
                _fatal_error(f"错误: 服务器名重复: {srv.name}")
            self.servers[srv.name] = srv

        if not self.servers:
            _fatal_error("错误: config.yml 中没有配置任何 servers")

        # ===== 多服务器下的 RCON 端口冲突检查 =====
        if len(self.servers) > 1:
            port_map = {}
            for name, srv in self.servers.items():
                port = srv.rcon_port
                if port in port_map:
                    _fatal_error(
                        f"⚠️ 警告: 检测到 RCON 端口冲突！\n"
                        f"服务器 [{port_map[port]}] 和 [{name}] 都使用了同一个端口 rcon.port = {port}\n"
                        f"请修改任意一个服务器 server.properties 中的 rcon.port，确保端口是独一无二的，且范围在0 ~ 65535的一个数字。"
                    )
                port_map[port] = name