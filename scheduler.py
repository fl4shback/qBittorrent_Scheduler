import datetime
import logging
import os
import qbittorrentapi
import schedule
import time

# Read docker secrets (failover to env if not present)
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
TZ = os.getenv("TZ", "Europe/Paris")
WEEKDAY_START = os.getenv("WEEKDAY_START", "18:00")
WEEKDAY_STOP = os.getenv("WEEKDAY_STOP", "00:00")
WEEKEND_START = os.getenv("WEEKEND_START", "10:00")
WEEKEND_STOP = os.getenv("WEEKEND_STOP", "00:00")
LOG_LEVEL = os.getenv("LOG_LEVEL")

# Init logger and setup log level
log = logging.getLogger("qbt_scheduler")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
if LOG_LEVEL == "DEBUG":
    logging.getLogger().setLevel(logging.DEBUG)

# Connect to qBittorrent API
def get_client():
    client = qbittorrentapi.Client(host=QBITTORRENT_URL, username=USERNAME, password=PASSWORD)
    try:
        client.auth_log_in()
        log.debug("Connected to qBittorrent API.")
        return client
    except qbittorrentapi.LoginFailed as e:
        log.info(f"Login failed: {e}")
        raise

def enable_alt_speed():
    client = get_client()
    speed_mode = int(client.transfer.speed_limits_mode)
    if client and speed_mode == 0:
        log.info("Enabling alternative speed limits.")
        client.transfer.set_speed_limits_mode(True) # 0/False = Global speed mode; 1/True = Alt Speed Mode
    elif client and speed_mode == 1:
        log.debug("Alt speed already toggled ON.")

def disable_alt_speed():
    client = get_client()
    speed_mode = int(client.transfer.speed_limits_mode)
    if client and speed_mode == 1:
        log.info("Disabling alternative speed limits.")
        client.transfer.set_speed_limits_mode(False) # 0/False = Global speed mode; 1/True = Alt Speed Mode
    elif client and speed_mode == 0:
        log.debug("Alt speed already toggled OFF.")

# Schedule differently on weekdays and weekends
def schedule_tasks():
    current_day = datetime.datetime.now().weekday()
    days = ["Monday", "Tuesday", "Wednesday", 
        "Thursday", "Friday", "Saturday", "Sunday"]

    # Only update the schedule if the day has changed
    if current_day != schedule_tasks.last_day:
        schedule_tasks.last_day = current_day

        log.info(f"Setting schedule to {days[current_day]}.")
        schedule.clear()

        if current_day < 5:
            # Weekdays: Monday (0) to Friday (4)
            log.debug(f"Current day = {days[current_day]}")
            schedule.every().day.at(WEEKDAY_START, TZ).do(enable_alt_speed)
            schedule.every().day.at(WEEKDAY_STOP, TZ).do(disable_alt_speed)
            log.debug(schedule.get_jobs())
        else:
            # Weekends: Saturday (5) and Sunday (6)
            log.debug(f"Current day = {days[current_day]}")
            schedule.every().day.at(WEEKEND_START, TZ).do(enable_alt_speed)
            schedule.every().day.at(WEEKEND_STOP, TZ).do(disable_alt_speed)
            log.debug(schedule.get_jobs())

if __name__ == "__main__":
    log.info("Schedule started")
    schedule_tasks.last_day = None
    while True:
        schedule_tasks()
        schedule.run_pending()

        # Determine the sleep duration dynamically
        next_run = schedule.next_run()
        if next_run:
            sleep_time = (next_run - datetime.datetime.now()).total_seconds()
            sleep_time = max(sleep_time, 1)  # Ensure we don't sleep for negative durations
            log.debug(f"Sleeping for {sleep_time:.2f} seconds until next scheduled job.")
            time.sleep(sleep_time)
        else:
            log.debug("No scheduled jobs. Sleeping for default 60 seconds.")
            time.sleep(60)
