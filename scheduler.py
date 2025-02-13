import os
import qbittorrentapi
import schedule
import time

def read_secret_or_env(env_var, file_var, default=None):
    secret_path = os.getenv(file_var)
    if secret_path:
        try:
            with open(secret_path, 'r') as secret_file:
                return secret_file.read().strip()
        except FileNotFoundError:
            pass
    return os.getenv(env_var, default)

# Load environment variables
QBITTORRENT_URL = os.getenv("QBITTORRENT_URL", "http://localhost:8080")
USERNAME = read_secret_or_env("USERNAME", "USERNAME_FILE", "admin")
PASSWORD = read_secret_or_env("PASSWORD", "PASSWORD_FILE", "adminadmin")
TZ = os.getenv("TZ", "UTC")
WEEKDAY_START = os.getenv("WEEKDAY_START", "18:00")
WEEKDAY_STOP = os.getenv("WEEKDAY_START", "00:00")
WEEKEND_START = os.getenv("WEEKEND_START", "10:00")
WEEKEND_STOP = os.getenv("WEEKEND_START", "00:00")

def get_client():
    client = qbittorrentapi.Client(host=QBITTORRENT_URL, username=USERNAME, password=PASSWORD)
    try:
        client.auth_log_in()
        print("Connected to qBittorrent API.")
        return client
    except qbittorrentapi.LoginFailed as e:
        print(f"Login failed: {e}")
        raise

def enable_alt_speed():
    client = get_client()
    speed_mode = int(client.transfer.speed_limits_mode)
    if client and speed_mode == 0:
        print("Enabling alternative speed limits.")
        client.transfer.set_speed_limits_mode(True) # 0/False = Global speed mode; 1/True = Alt Speed Mode
    elif client and speed_mode == 1:
        print("Alt speed already toggled On")

def disable_alt_speed():
    client = get_client()
    speed_mode = int(client.transfer.speed_limits_mode)
    if client and speed_mode == 1:
        print("Disabling alternative speed limits.")
        client.transfer.set_speed_limits_mode(False) # 0/False = Global speed mode; 1/True = Alt Speed Mode
    elif client and speed_mode == 0:
        print("Alt speed already toggled Off")

# Define schedule for weekdays (Monday to Friday)
for day in [schedule.every().monday, schedule.every().tuesday, schedule.every().wednesday, schedule.every().thursday, schedule.every().friday]:
    day.at(WEEKDAY_START, TZ).do(enable_alt_speed)
    day.at(WEEKDAY_STOP, TZ).do(disable_alt_speed)

# Define schedule for weekends (Saturday and Sunday)
for day in [schedule.every().saturday, schedule.every().sunday]:
    day.at(WEEKEND_START, TZ).do(enable_alt_speed)
    day.at(WEEKEND_STOP, TZ).do(disable_alt_speed)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        # disable_alt_speed()
        # enable_alt_speed()
        time.sleep(60)
