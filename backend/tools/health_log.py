logs = []

def log_action(action, detail):
    from datetime import datetime
    logs.append({"time": datetime.now().isoformat(), "action": action, "detail": detail})

def get_logs():
    if not logs:
        return "No health records found."
    return "\n".join([f"{l['time']}: [{l['action']}] {l['detail']}" for l in logs])