# sampling_scheduler.py
import time
import gevent

class SamplingScheduler:
    def __init__(self, interval_sec, rcon_client, db):
        self.interval = interval_sec
        self.rcon = rcon_client
        self.db = db
        self._greenlet = None

    def force_sample_now(self):
        now = time.time()
        ts = int(now)
        count = self.rcon.get_online_count()
        if count is None:
            count = -1
            print("[STATS] 强制采样失败（崩溃标记）")
        else:
            print(f"[STATS] 强制采样在线人数: {count}")
        self.db.record_snapshot(ts, count)

    def _sample(self):
        try:
            now = time.time()
            ts = int(now)
            count = self.rcon.get_online_count()
            if count is None:
                count = -1
                print("[STATS] 采样失败")
            else:
                print(f"[STATS] 采样在线人数: {count}")
            self.db.record_snapshot(ts, count)
        except BaseException as e:
            print(f"[STATS] 采样异常: {e}")
        finally:
            self._greenlet = gevent.spawn_later(self.interval, self._sample)

    def start(self):
        last_ts = self.db.get_last_snapshot_time()
        now = time.time()
        if last_ts is None:
            delay = self.interval
        else:
            elapsed = now - last_ts
            if elapsed >= self.interval:
                delay = 0
            else:
                delay = self.interval - elapsed
        print(f"[STATS] 采样调度: 首次执行延迟 {delay:.0f} 秒")
        if delay == 0:
            gevent.spawn(self._sample)
        else:
            self._greenlet = gevent.spawn_later(delay, self._sample)