"""
scheduler.py
Runs fetch_data.py once every hour so history.csv builds up meaningful
trend data over days/weeks. Leave this running in the background
(e.g. inside a `screen`/`tmux` session, or as a systemd/cron job on a
server, or deployed as a scheduled task on PythonAnywhere / Render / a
free-tier VM).

Usage:
    export OPENWEATHER_API_KEY="your_key_here"
    python scripts/scheduler.py
"""

import subprocess
import sys
import time
import datetime
import schedule

SCRIPT_DIR = __file__.rsplit("/", 1)[0]


def run_fetch():
    print(f"\n=== Running fetch_data.py at {datetime.datetime.now().isoformat()} ===")
    result = subprocess.run([sys.executable, f"{SCRIPT_DIR}/fetch_data.py"])
    if result.returncode != 0:
        print("fetch_data.py exited with an error. Check OPENWEATHER_API_KEY / network.")


def main():
    print("Air Quality scheduler started. Fetching every hour. Ctrl+C to stop.")
    run_fetch()  # run once immediately on startup
    schedule.every(1).hours.do(run_fetch)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
