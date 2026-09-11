# rcon_client.py
import gevent
from mcrcon import MCRcon
from gevent import Timeout
from mcstatus import JavaServer


class RCONClient:
    def __init__(self, host, port, password, server_addresses):
        self.host = host
        self.port = port
        self.password = password
        if isinstance(server_addresses, str):
            server_addresses = [server_addresses]
        self.server_addresses = [a for a in (server_addresses or []) if a and str(a).strip()]
        self._conn = None
        self._lock = gevent.lock.Semaphore()

    def _connect(self):
        try:
            with Timeout(5, RuntimeError("RCON连接超时")):
                conn = MCRcon(self.host, self.password, port=self.port)
                conn.connect()
                return conn
        except Exception as e:
            print(f"[RCON] 连接失败: {e}")
            return None

    def get_connection(self):
        with self._lock:
            if self._conn is None:
                self._conn = self._connect()
            return self._conn

    def send_command(self, cmd):
        conn = self.get_connection()
        if conn is None:
            return None
        try:
            with self._lock:
                with Timeout(10, RuntimeError("命令执行超时")):
                    resp = conn.command(cmd)
                return resp
        except Exception as e:
            print(f"[RCON] 命令失败 ({e})，尝试重连...")
            with self._lock:
                try:
                    if self._conn:
                        self._conn.disconnect()
                except Exception:
                    pass
                self._conn = None
                try:
                    new_conn = self._connect()
                    if new_conn is None:
                        return None
                    self._conn = new_conn
                    resp = self._conn.command(cmd)
                    return resp
                except Exception as e2:
                    print(f"[RCON] 重连失败: {e2}")
                    return None

    def _query_single(self, address):
        for attempt in range(2):
            try:
                with Timeout(10):
                    server = JavaServer.lookup(address)
                    status = server.status()
                    return status.players.online
            except Exception as e:
                print(f"[RCON] 获取在线人数尝试 {attempt + 1} 失败 ({address}): {e}")
                if attempt == 0:
                    gevent.sleep(0.5)
                else:
                    return None

    def get_online_detail(self):
        if not self.server_addresses:
            print("[RCON] 未配置 public_server_addresses，无法获取在线人数")
            return None

        jobs = [gevent.spawn(self._query_single, addr) for addr in self.server_addresses]
        gevent.joinall(jobs)

        servers = []
        for addr, job in zip(self.server_addresses, jobs):
            online = job.value
            if online is None:
                print(f"[RCON] 服务器 {addr} 在线人数获取失败")
            else:
                print(f"[RCON] 服务器 {addr} 在线人数: {online}")
            servers.append({'address': addr, 'online': online})

        ok_values = [s['online'] for s in servers if s['online'] is not None]
        if not ok_values:
            return None
        total = sum(ok_values)
        print(f"[RCON] 总在线人数: {total}（共 {len(servers)} 台服务器，成功 {len(ok_values)} 台）")
        return {'total': total, 'servers': servers}

    def get_online_count(self):
        detail = self.get_online_detail()
        if detail is None:
            return None
        return detail['total']


class RCONManager:
    """多服务器 RCON 管理器。
    - 每个服务器一个 RCONClient，用于各自发命令。
    - 另外维护一个"聚合客户端"，其 server_addresses = 所有服务器地址的并集，
      专门用于统计（查人数、加总、写入数据库）。
    """

    def __init__(self, server_configs):
        self.clients = {}
        self.all_addresses = []

        for name, cfg in server_configs.items():
            self.clients[name] = RCONClient(
                cfg.rcon_host, cfg.rcon_port, cfg.rcon_password,
                cfg.PUBLIC_SERVER_ADDRESSES
            )
            for addr in cfg.PUBLIC_SERVER_ADDRESSES:
                if addr not in self.all_addresses:
                    self.all_addresses.append(addr)

        # 聚合客户端：只用它的 server_addresses 做统计查询，
        # RCON 连接信息随便用第一台（get_online_detail 用不到 RCON 连接）
        if self.all_addresses:
            first_cfg = next(iter(server_configs.values()))
            self.aggregate_client = RCONClient(
                first_cfg.rcon_host, first_cfg.rcon_port, first_cfg.rcon_password,
                self.all_addresses
            )
        else:
            self.aggregate_client = None

        print(f"[RCON] 已加载 {len(self.clients)} 台服务器，"
              f"聚合统计地址共 {len(self.all_addresses)} 个: {self.all_addresses}")

    def send_command(self, server_name, cmd):
        client = self.clients.get(server_name)
        return client.send_command(cmd) if client else None

    def get_online_detail(self, server_name):
        client = self.clients.get(server_name)
        return client.get_online_detail() if client else None

    def get_online_count(self, server_name):
        detail = self.get_online_detail(server_name)
        return detail['total'] if detail else None

    # ===== 聚合统计（所有服务器地址一起查、加总） =====
    def get_all_online_detail(self):
        if self.aggregate_client is None:
            return None
        return self.aggregate_client.get_online_detail()

    def get_all_online_count(self):
        detail = self.get_all_online_detail()
        return detail['total'] if detail else None