# db.py
import time
import sqlite3
import gevent

class StatsDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = gevent.lock.Semaphore()
        self._init_db()

    def _init_db(self):
        with self._lock:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.execute('''
                CREATE TABLE IF NOT EXISTS hourly_stats (
                    hour_timestamp INTEGER PRIMARY KEY,
                    online_count INTEGER NOT NULL
                )
            ''')
            self._conn.commit()

    def record_snapshot(self, timestamp, count):
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO hourly_stats (hour_timestamp, online_count) VALUES (?, ?)",
                (timestamp, count)
            )
            self._conn.commit()

    def get_hourly_stats(self, range_days=None):
        with self._lock:
            if range_days is None:
                rows = self._conn.execute(
                    "SELECT hour_timestamp, online_count FROM hourly_stats ORDER BY hour_timestamp ASC"
                ).fetchall()
            else:
                cutoff = time.time() - range_days * 86400
                rows = self._conn.execute(
                    "SELECT hour_timestamp, online_count FROM hourly_stats WHERE hour_timestamp >= ? ORDER BY hour_timestamp ASC",
                    (cutoff,)
                ).fetchall()
            return rows

    def get_last_snapshot_time(self):
        with self._lock:
            row = self._conn.execute("SELECT MAX(hour_timestamp) FROM hourly_stats").fetchone()
            return row[0] if row and row[0] is not None else None