# app.py
import os
import time
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_socketio import emit
from flask_compress import Compress   # 新增
from utils import get_filtered_lines


def create_app(config, rcon_client, db, mail_notifier, socketio_instance):
    app = Flask(__name__)
    Compress(app)
    app.config['SECRET_KEY'] = config.API_PASSWORD

    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.headers.get('Authorization')
            if not auth or not auth.startswith('Bearer '):
                return jsonify({'error': 'Missing token'}), 401
            token = auth.split(' ')[1]
            if token != config.API_PASSWORD:
                return jsonify({'error': 'Invalid token'}), 401
            return f(*args, **kwargs)
        return decorated

    @app.route('/')
    def index():
        return redirect('/main_console_rcon.html')
    
    @app.route('/main_console_rcon.html')
    def main_console():
        return send_from_directory('.', 'main_console_rcon.html')

    @app.route('/api/highlight_rules')
    def get_highlight_rules():
        return jsonify(config.HIGHLIGHT_RULES)
    
    @app.route('/api/anticheat_keywords')
    def get_anticheat_keywords():
        return jsonify(config.ANTICHEAT_KEYWORDS)

    @app.route('/api/latest_raw')
    @require_auth
    def get_latest_raw():
        if not os.path.exists(config.LATEST_LOG):
            return "日志文件不存在", 404
        filtered = get_filtered_lines(config.LATEST_LOG, config.FILTER_KEYWORDS)
        return '\n'.join(filtered), 200, {'Content-Type': 'text/plain; charset=utf-8'}

    @app.route('/api/log/total_lines')
    @require_auth
    def log_total_lines():
        if not os.path.exists(config.LATEST_LOG):
            return jsonify({'error': '日志文件不存在'}), 404
        filtered = get_filtered_lines(config.LATEST_LOG, config.FILTER_KEYWORDS)
        return jsonify({'total': len(filtered)})

    @app.route('/api/log/range')
    @require_auth
    def log_range():
        start = request.args.get('start', 0, type=int)
        count = request.args.get('count', 500, type=int)
        if not os.path.exists(config.LATEST_LOG):
            return jsonify({'error': '日志文件不存在'}), 404
        filtered = get_filtered_lines(config.LATEST_LOG, config.FILTER_KEYWORDS)
        total = len(filtered)
        end = min(start + count, total)
        return jsonify({
            'lines': filtered[start:end],
            'start': start,
            'end': end,
            'total': total
        })

    @app.route('/api/rcon', methods=['POST'])
    @require_auth
    def rcon_command():
        data = request.get_json()
        cmd = data.get('command', '').strip()
        if not cmd:
            return jsonify({'success': False, 'output': '命令为空'}), 400
        resp = rcon_client.send_command(cmd)
        if resp is None:
            return jsonify({'success': False, 'output': 'RCON 执行失败'}), 500
        return jsonify({'success': True, 'output': resp.strip()})

    @app.route('/api/stats/online')
    @require_auth
    def stats_online():
        range_param = request.args.get('range', '7d')
        days_map = {'1d': 1, '3d': 3, '7d': 7, 'all': None}
        days = days_map.get(range_param, 7)
        rows = db.get_hourly_stats(days)
        if not rows:
            return jsonify({'success': True, 'data': {'times': [], 'counts': [], 'missingRanges': []}})
        timestamps = [ts for ts, _ in rows]
        counts_raw = [cnt if cnt != -1 else None for _, cnt in rows]
        times_str = [time.strftime('%m-%d %H:%M', time.localtime(ts)) for ts in timestamps]

        missing_ranges = []
        valid_indices = [i for i, cnt in enumerate(counts_raw) if cnt is not None]
        for i in range(len(valid_indices) - 1):
            idx_curr = valid_indices[i]
            idx_next = valid_indices[i+1]
            if idx_next - idx_curr > 1:
                missing_ranges.append({'startIdx': idx_curr, 'endIdx': idx_next})
        return jsonify({
            'success': True,
            'data': {
                'times': times_str,
                'counts': counts_raw,
                'missingRanges': missing_ranges
            }
        })

    @app.route('/api/online/detail')
    @require_auth
    def online_detail():
        """实时查询各服务器在线人数，返回明细与总人数"""
        detail = rcon_client.get_online_detail()
        if detail is None:
            return jsonify({
                'success': True,
                'data': {
                    'total': None,
                    'servers': [{'address': a, 'online': None} for a in rcon_client.server_addresses]
                }
            })
        return jsonify({'success': True, 'data': detail})

    @socketio_instance.on('connect')
    def handle_connect():
        token = request.args.get('token')
        if not token or token != config.API_PASSWORD:
            print(f"[WS] Unauthorized connection attempt from {request.sid}, token={token}")
            return False
        print(f"[WS] Client authenticated: {request.sid}")
        emit('connected', {'status': 'ok'})

    @socketio_instance.on('disconnect')
    def handle_disconnect():
        print(f"[WS] Client disconnected: {request.sid}")
    return app