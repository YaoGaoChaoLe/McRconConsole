# performance_monitor.py
import psutil
import gevent

class PerformanceMonitor:
    def __init__(self, socketio_instance, interval=1.0):
        self.socketio = socketio_instance
        self.interval = interval
        self.last_net = None
        self._greenlet = None

    def start(self):
        self._greenlet = gevent.spawn_later(0, self._loop)

    def _loop(self):
        while True:
            self._send_performance_data()
            gevent.sleep(self.interval)

    def _send_performance_data(self):
        cpu_per_core = psutil.cpu_percent(interval=0, percpu=True)   # 每个核心的列表  <<<
        cpu_percent = sum(cpu_per_core) / len(cpu_per_core) if cpu_per_core else 0  # 总平均  <<<
        mem = psutil.virtual_memory()
        mem_percent = mem.percent

        net = psutil.net_io_counters()
        if self.last_net is not None:
            elapsed = self.interval
            upload_rate = (net.bytes_sent - self.last_net.bytes_sent) * 8 / elapsed / 1_000_000
            download_rate = (net.bytes_recv - self.last_net.bytes_recv) * 8 / elapsed / 1_000_000

        else:
            upload_rate = 0
            download_rate = 0

        self.last_net = net

        self.socketio.emit('performance_update', {
            'cpu': cpu_percent,
            'cpu_per_core': cpu_per_core,   # 新增  <<<
            'memory': mem_percent,
            'upload': upload_rate,
            'download': download_rate
        })