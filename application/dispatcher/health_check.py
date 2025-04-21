# Should be run as a cron job
# */5 * * * * /usr/bin/python3 PROJECT_DIR/application/dispatcher/health_check.py

import subprocess
import smtplib
from email.mime.text import MIMEText
import os

from pathlib import Path
from dotenv import load_dotenv

# Абсолютный путь до текущего файла
BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path)


# Конфигурация
CONTAINERS = ["chronicler", "celery_worker_chr", "redis"]
CHECK_INTERVAL = int(os.getenv("HEALTHCHECK_INTERVAL"))  # секунд
EMAIL = os.getenv("HEALTHCHECK_EMAIL")
SMTP_SERVER = os.getenv("HEALTHCHECK_SMTP_SERVER")
SMTP_PORT = int(os.getenv("HEALTHCHECK_SMTP_PORT"))
SMTP_USER = os.getenv("HEALTHCHECK_SMTP_USER")
SMTP_PASSWORD = os.getenv("HEALTHCHECK_SMTP_PASSWORD")

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [EMAIL], msg.as_string())

def check_containers():
    result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
    running = result.stdout.strip().split("\n")
    not_running = [c for c in CONTAINERS if c not in running]
    return not_running

def main():
    down = check_containers()
    if down:
        #send_email("🚨 Контейнеры упали", f"Неактивны: {', '.join(down)}")
        #print("🚨 Контейнеры упали", f"Неактивны: {', '.join(down)}")
        pass

if __name__ == "__main__":
    main()
