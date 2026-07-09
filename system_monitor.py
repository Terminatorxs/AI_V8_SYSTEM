try:
    import psutil
except:
    psutil = None


def get_system_info():
    if psutil is None:
        return {
            "cpu": 0,
            "memory": 0,
            "disk": 0
        }

    return {
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent
    }