"""
Deploy script — reads secrets from local .env, never hardcodes them.
Usage: python redeploy.py
"""
import os, paramiko, sys, time
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

SSH_HOST = "85.198.97.76"
SSH_USER = "root"
SSH_PASS = os.getenv("DEPLOY_SSH_PASS", "")
REMOTE   = "/opt/meme_bot"

FILES = [
    ("handlers/meme.py",              f"{REMOTE}/handlers/meme.py"),
    ("handlers/payments.py",          f"{REMOTE}/handlers/payments.py"),
    ("handlers/start.py",             f"{REMOTE}/handlers/start.py"),
    ("utils/caption_generator.py",    f"{REMOTE}/utils/caption_generator.py"),
    ("utils/keyboards.py",            f"{REMOTE}/utils/keyboards.py"),
    ("utils/prompt_builder.py",       f"{REMOTE}/utils/prompt_builder.py"),
    ("utils/text_overlay.py",         f"{REMOTE}/utils/text_overlay.py"),
    ("providers/image_provider.py",   f"{REMOTE}/providers/image_provider.py"),
    ("database/repository.py",        f"{REMOTE}/database/repository.py"),
    ("config.py",                     f"{REMOTE}/config.py"),
    ("requirements.txt",              f"{REMOTE}/requirements.txt"),
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(SSH_HOST, 22, SSH_USER, SSH_PASS, timeout=15)

def run(cmd):
    _, o, e = c.exec_command(cmd)
    out = o.read().decode("utf-8", errors="replace")
    err = e.read().decode("utf-8", errors="replace")
    if out.strip(): print(out.rstrip())
    if err.strip(): print("[err]", err.rstrip())

sftp = c.open_sftp()
for local, remote in FILES:
    if os.path.exists(local):
        print(f"  upload {remote}")
        sftp.put(local, remote)
sftp.close()

run(f"/opt/meme_bot/venv/bin/pip install -q -r {REMOTE}/requirements.txt")
run("systemctl restart meme_bot")
time.sleep(4)
run("systemctl status meme_bot --no-pager")
c.close()
