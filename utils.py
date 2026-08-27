# utils.py
import os

def should_keep_log_line(line: str, filter_keywords) -> bool:
    line_lower = line.lower()
    for kw in filter_keywords:
        if kw.lower() in line_lower:
            return False
    if line.lstrip().startswith("at "):
        return False
    return True


# 全局缓存：key为文件路径，value为 (mtime, lines列表)
_log_cache = {}

def get_filtered_lines(log_path: str, filter_keywords: list, force_refresh: bool = False) -> list:
    """获取过滤后的日志行（带文件修改时间缓存）"""
    current_mtime = os.path.getmtime(log_path)
    cached_mtime, cached_lines = _log_cache.get(log_path, (0, None))
    
    if force_refresh or cached_lines is None or current_mtime != cached_mtime:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [
                line.rstrip('\n\r') for line in f
                if should_keep_log_line(line.rstrip('\n\r'), filter_keywords)
            ]
        _log_cache[log_path] = (current_mtime, lines)
        return lines
    return cached_lines