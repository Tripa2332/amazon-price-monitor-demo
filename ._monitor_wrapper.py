
import subprocess, sys, json, re, os
from pathlib import Path

PROGRESS_FILE = Path(".monitor_progress.json")
LOG_FILE      = Path(".monitor_log.txt")
PID_FILE      = Path(".monitor_pid")

PID_FILE.write_text(str(os.getpid()))
LOG_FILE.write_text("")

proc = subprocess.Popen(
    [sys.executable, "-u", "monitor_aws.py"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True, bufsize=1, env=dict(os.environ),
)

progress = {"current": 0, "total": int(os.environ.get("TOTAL_PRODUCTOS", "1")),
            "ultimo": "", "status": "running"}

with open(LOG_FILE, "a", encoding="utf-8") as log:
    for line in proc.stdout:
        line = line.rstrip()
        log.write(line + "\n")
        log.flush()

        m = re.search(r'completados?:\s*(\d+)/(\d+)', line, re.IGNORECASE)
        if m:
            progress["current"] = int(m.group(1))
            progress["total"]   = int(m.group(2))

        m2 = re.search(r'Buscado:\s*(.+?)\s*---', line)
        if m2:
            progress["ultimo"] = m2.group(1).strip()

        PROGRESS_FILE.write_text(json.dumps(progress))

proc.wait()
progress["status"] = "done"
PROGRESS_FILE.write_text(json.dumps(progress))
try:
    PID_FILE.unlink()
except FileNotFoundError:
    pass
