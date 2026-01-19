from datetime import datetime
import time

def log_perf(operation, message="", user_id=None):
    """Log performance with timestamp for Railway logs"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    user_str = f"[user:{user_id}] " if user_id else ""
    print(f"[PERF] {timestamp} {user_str}{operation} {message}")

def log_perf_start(operation, user_id=None):
    """Log the start of an operation and return start time"""
    log_perf(operation, "START", user_id)
    return time.time()

def log_perf_end(operation, start_time, user_id=None):
    """Log the end of an operation with duration"""
    duration = time.time() - start_time
    log_perf(operation, f"END (duration: {duration:.3f}s)", user_id)
    return duration
