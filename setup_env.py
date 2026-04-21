import paramiko, sys
sys.stdout.reconfigure(encoding="utf-8")

HOST, PORT, USER, PASSWORD = "85.198.97.76", 22, "root", "420218"
REMOTE = "/opt/meme_bot"

ENV_CONTENT = """BOT_TOKEN=8401760800:AAGHk6uYDaDixXoJDJa8zZXbh3Itv2xGfzk

# Image generation API - fill in when ready
IMAGE_API_BASE_URL=https://api.openai.com/v1
IMAGE_API_KEY=REPLACE_ME
IMAGE_MODEL=dall-e-3
TIMEOUT_SECONDS=90
RETRIES=2

# Admin IDs
ADMIN_IDS=

# Database
DB_PATH=/opt/meme_bot/memes.db

# Limits
FREE_DAILY_LIMIT=3
RATE_LIMIT_SECONDS=10
MAX_CONCURRENT_PER_USER=2

# Telegram Payments
PAYMENT_PROVIDER_TOKEN=
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, PORT, USER, PASSWORD, timeout=15)

sftp = client.open_sftp()
with sftp.open(f"{REMOTE}/.env", "w") as f:
    f.write(ENV_CONTENT)
sftp.close()
print(".env written to server")

def run(cmd):
    _, o, e = client.exec_command(cmd)
    out = o.read().decode("utf-8", errors="replace")
    err = e.read().decode("utf-8", errors="replace")
    if out.strip(): print(out.rstrip())
    if err.strip(): print(err.rstrip(), file=sys.stderr)

run(f"chmod 600 {REMOTE}/.env")
print("Starting meme_bot service...")
run("systemctl start meme_bot")
import time; time.sleep(3)
run("systemctl status meme_bot --no-pager")
client.close()
