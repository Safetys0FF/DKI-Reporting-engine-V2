
import time
import threading

# Sandbox heartbeat toggle
RUN_HEARTBEAT = True

# Send output every 55 seconds to prevent sandbox timeout
HEARTBEAT_INTERVAL = 55

def heartbeat():
    while True:
        if RUN_HEARTBEAT:
            print("[SANDBOX HEARTBEAT] Python environment is still active.", flush=True)
        time.sleep(HEARTBEAT_INTERVAL)

if __name__ == "__main__":
    print("[INIT] Heartbeat monitor started.", flush=True)
    # Run heartbeat in a non-blocking background thread
    threading.Thread(target=heartbeat, daemon=True).start()

    # Keep script idle to prevent termination
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[SHUTDOWN] Heartbeat monitor terminated.", flush=True)
