import psutil
import time
import threading
import collections

# Store the last network I/O data for delta calculation
last_net_io = psutil.net_io_counters()
last_time = time.time()

# Historical CPU and RAM usage, stored for live plotting (e.g. 60 seconds)
cpu_history = collections.deque(maxlen=60)
ram_history = collections.deque(maxlen=60)

def collect_data():
    """
    Collect CPU and RAM usage every second and store them in rolling queues.
    Intended to be run in a background thread.
    """
    while True:
        cpu_history.append(psutil.cpu_percent())
        ram_history.append(psutil.virtual_memory().percent)
        time.sleep(1)

def start_data_thread():
    """
    Launch the data collection in a background thread (non-blocking).
    Automatically marked as daemon so it doesn't hang on app exit.
    """
    t = threading.Thread(target=collect_data, daemon=True)
    t.start()

def get_temperatures():
    """
    Attempt to get system temperature data using psutil.
    On many systems this will return 'Temp: N/A' unless sensor access is supported.
    Could be extended with OpenHardwareMonitor or py-cpuinfo for richer data.
    """
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                for entry in entries:
                    if entry.current:
                        return f"{name}: {entry.current}°C"
    except:
        return "Temp: N/A"
    return "Temp: N/A"

def format_bytes(size):
    """
    Convert bytes to human-readable format (e.g. KB, MB, GB).
    Useful for displaying RAM/disk/network speeds.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

def get_network_speed():
    """
    Calculate upload/download speed since the last check.
    Uses psutil.net_io_counters and system time deltas.
    Returns speeds in bytes per second.
    """
    global last_net_io, last_time

    current_io = psutil.net_io_counters()
    current_time = time.time()
    duration = current_time - last_time

    # Calculate byte difference per second
    upload_speed = (current_io.bytes_sent - last_net_io.bytes_sent) / duration
    download_speed = (current_io.bytes_recv - last_net_io.bytes_recv) / duration

    # Update last known values
    last_net_io = current_io
    last_time = current_time

    return upload_speed, download_speed
