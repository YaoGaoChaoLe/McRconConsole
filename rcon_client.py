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
        # 兼容单个字符串地址，统一转为列表
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
                # 加上超时
                with Timeout(10, RuntimeError("命令执行超时")):
                    resp = conn.command(cmd)
                return resp
        except Exception as e:
            print(f"[RCON] 命令失败 ({e})，尝试重连...")
            with self._lock:
                try:
                    if self._conn:
                        self._conn.disconnect()
                except:
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
        """使用 mcstatus 查询单个服务器的在线人数，尝试两次，总超时3秒"""
        for attempt in range(2):
            try:
                with Timeout(3):   # 控制整个查询在3秒内完成
                    server = JavaServer.lookup(address)
                    status = server.status()
                    return status.players.online
            except Exception as e:
                print(f"[RCON] 获取在线人数尝试 {attempt+1} 失败 ({address}): {e}")
                if attempt == 0:
                    gevent.sleep(0.5)   # 等待0.5秒后重试
                else:
                    return None

    def get_online_detail(self):
        """并发查询所有配置服务器的在线人数，返回各服务器明细与总人数"""
        if not self.server_addresses:
            print("[RCON] 未配置 public_server_addresses，无法获取在线人数")
            return None

        # 并发查询所有服务器（gevent 协程）
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
            # 全部失败：返回 None 表示无法获取（采样将记录为 -1）
            return None
        total = sum(ok_values)
        print(f"[RCON] 总在线人数: {total}（共 {len(servers)} 台服务器，成功 {len(ok_values)} 台）")
        return {'total': total, 'servers': servers}

    def get_online_count(self):
        """获取所有服务器在线人数之和"""
        detail = self.get_online_detail()
        if detail is None:
            return None
        return detail['total']