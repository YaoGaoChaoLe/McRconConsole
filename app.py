# app.py
import os
import time
import sys
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import emit
from flask_compress import Compress
from utils import get_filtered_lines


def create_app(config, rcon_manager, db, socketio_instance):
    app = Flask(__name__)
    Compress(app)
    app.config['SECRET_KEY'] = config.ADMIN_PASSWORD

    # ===== 获取 exe 所在目录（打包后）或源码所在目录（开发时） =====
    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # ================================================================

    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.headers.get('Authorization')
            if not auth or not auth.startswith('Bearer '):
                return jsonify({'error': 'Missing token'}), 401
            token = auth.split(' ')[1]
            if token != config.ADMIN_PASSWORD:
                return jsonify({'error': 'Invalid token'}), 401
            return f(*args, **kwargs)
        return decorated

    def _get_server_from_query():
        server_name = request.args.get('server')
        srv = config.servers.get(server_name) if server_name else None
        return server_name, srv

    # ============================================================
    # 基础接口
    # ============================================================
    @app.route('/')
    def index():
        return "Not Found", 404

    @app.route('/main_console_rcon.html')
    def main_console():
        return send_from_directory(BASE_DIR, 'main_console_rcon.html')

    @app.route('/api/auth')
    def auth_check():
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'success': False}), 401
        if auth.split(' ')[1] != config.ADMIN_PASSWORD:
            return jsonify({'success': False}), 401
        return jsonify({'success': True})

    @app.route('/api/servers')
    def get_servers():
        return jsonify(list(config.servers.keys()))

    @app.route('/api/highlight_rules')
    def get_highlight_rules():
        return jsonify(config.HIGHLIGHT_RULES)

    @app.route('/api/anticheat_keywords')
    def get_anticheat_keywords():
        return jsonify(config.ANTICHEAT_KEYWORDS)

    # ============================================================
    # 屏幕截图（系统级，与服务器无关）
    # ============================================================
    @app.route('/api/screen', methods=['GET'])
    @require_auth
    def screen_capture():
        """截取服务器屏幕，返回Base64图片"""
        import subprocess
        import base64
        import tempfile
        import os as _os

        tmp_dir = tempfile.gettempdir()
        img_path = _os.path.join(tmp_dir, 'mcscreen_capture.png')
        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$code = @'
using System;
using System.Runtime.InteropServices;
public class DpiHelper {{
    [DllImport("user32.dll")]
    public static extern bool SetProcessDPIAware();
}}
'@
Add-Type -TypeDefinition $code
[DpiHelper]::SetProcessDPIAware()
$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$jpegCodec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object {{ $_.MimeType -eq 'image/jpeg' }}
$encoderParams = New-Object System.Drawing.Imaging.EncoderParameters(1)
$encoderParams.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, 50)
$bmp.Save("{img_path}", $jpegCodec, $encoderParams)
$g.Dispose()
$bmp.Dispose()
"""
        try:
            subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=10, check=True
            )
            with open(img_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            _os.remove(img_path)
            print(f"获取屏幕")
            return jsonify({'success': True,
                            'image_base64': f'data:image/jpeg;base64,{img_data}'})
        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'error': '截图超时'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': f'截图失败: {str(e)}'}), 500

    # ============================================================
    # 日志接口（按 server 区分）
    # ============================================================
    @app.route('/api/latest_raw')
    @require_auth
    def get_latest_raw():
        server_name, srv = _get_server_from_query()
        if not srv:
            return "服务器不存在", 404
        if not os.path.exists(srv.LATEST_LOG):
            return "日志文件不存在", 404
        filtered = get_filtered_lines(srv.LATEST_LOG, config.FILTER_KEYWORDS)
        return '\n'.join(filtered), 200, {'Content-Type': 'text/plain; charset=utf-8'}

    @app.route('/api/log/total_lines')
    @require_auth
    def log_total_lines():
        server_name, srv = _get_server_from_query()
        if not srv:
            return jsonify({'error': '服务器不存在'}), 404
        if not os.path.exists(srv.LATEST_LOG):
            return jsonify({'error': '日志文件不存在'}), 404
        filtered = get_filtered_lines(srv.LATEST_LOG, config.FILTER_KEYWORDS)
        return jsonify({'total': len(filtered)})

    @app.route('/api/log/range')
    @require_auth
    def log_range():
        server_name, srv = _get_server_from_query()
        if not srv:
            return jsonify({'error': '服务器不存在'}), 404
        start = request.args.get('start', 0, type=int)
        count = request.args.get('count', 500, type=int)
        if not os.path.exists(srv.LATEST_LOG):
            return jsonify({'error': '日志文件不存在'}), 404
        filtered = get_filtered_lines(srv.LATEST_LOG, config.FILTER_KEYWORDS)
        total = len(filtered)
        end = min(start + count, total)
        return jsonify({
            'lines': filtered[start:end],
            'start': start,
            'end': end,
            'total': total
        })

    # ============================================================
    # RCON 接口（按 server 区分）
    # ============================================================
    @app.route('/api/rcon', methods=['POST'])
    @require_auth
    def rcon_command():
        data = request.get_json()
        server_name = data.get('server')
        cmd = data.get('command', '').strip()
        if not server_name or server_name not in config.servers:
            return jsonify({'success': False, 'output': '服务器不存在'}), 400
        if not cmd:
            return jsonify({'success': False, 'output': '命令为空'}), 400
        resp = rcon_manager.send_command(server_name, cmd)
        if resp is None:
            return jsonify({'success': False, 'output': 'RCON 执行失败'}), 500
        return jsonify({'success': True, 'output': resp.strip()})

    # ============================================================
    # 统计接口（全部服务器地址合并、加总，写同一条曲线）
    # ============================================================
    @app.route('/api/stats/online')
    @require_auth
    def stats_online():
        range_param = request.args.get('range', '7d')
        days_map = {'1d': 1, '3d': 3, '7d': 7, '15d': 15, '30d': 30, 'all': None}
        days = days_map.get(range_param, 7)
        rows = db.get_hourly_stats(days)
        if not rows:
            return jsonify({'success': True,
                            'data': {'times': [], 'counts': [], 'missingRanges': []}})
        timestamps = [ts for ts, _ in rows]
        counts_raw = [cnt if cnt != -1 else None for _, cnt in rows]
        times_str = [time.strftime('%m-%d %H:%M', time.localtime(ts)) for ts in timestamps]

        missing_ranges = []
        valid_indices = [i for i, cnt in enumerate(counts_raw) if cnt is not None]
        for i in range(len(valid_indices) - 1):
            idx_curr = valid_indices[i]
            idx_next = valid_indices[i + 1]
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
        """实时查询所有服务器地址的在线人数，返回明细与总人数（合并加总）"""
        detail = rcon_manager.get_all_online_detail()
        if detail is None:
            return jsonify({
                'success': True,
                'data': {
                    'total': None,
                    'servers': [{'address': a, 'online': None}
                                for a in rcon_manager.all_addresses]
                }
            })
        return jsonify({'success': True, 'data': detail})

    # ============================================================
    # WebSocket
    # ============================================================
    @socketio_instance.on('connect')
    def handle_connect():
        token = request.args.get('token')
        if not token or token != config.ADMIN_PASSWORD:
            print(f"[WS] Unauthorized connection attempt from {request.sid}, token={token}")
            return False
        print(f"[WS] Client authenticated: {request.sid}")
        emit('connected', {'status': 'ok'})

    @socketio_instance.on('disconnect')
    def handle_disconnect():
        print(f"[WS] Client disconnected: {request.sid}")

    return app