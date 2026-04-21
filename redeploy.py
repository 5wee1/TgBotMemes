import paramiko, sys, time
sys.stdout.reconfigure(encoding="utf-8")

FAL_KEY = "823d3d74-4674-4a7e-80a5-0a1da5a908d8:5f8d6e8c428d4c26b7bb59cecc5d9609"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("85.198.97.76", 22, "root", "420218", timeout=15)

def run(cmd):
    _, o, e = c.exec_command(cmd)
    out = o.read().decode("utf-8", errors="replace")
    err = e.read().decode("utf-8", errors="replace")
    if out.strip(): print(out.rstrip())
    if err.strip(): print("[err]", err.rstrip())

files = [
    ("providers/image_provider.py", "/opt/meme_bot/providers/image_provider.py"),
    ("utils/prompt_builder.py",     "/opt/meme_bot/utils/prompt_builder.py"),
    ("utils/text_overlay.py",       "/opt/meme_bot/utils/text_overlay.py"),
    ("handlers/meme.py",            "/opt/meme_bot/handlers/meme.py"),
]

sftp = c.open_sftp()
for local, remote in files:
    print(f"upload {remote}")
    sftp.put(local, remote)
sftp.close()

# Update .env: set fal.ai key
run(f"sed -i 's|IMAGE_API_KEY=.*|IMAGE_API_KEY={FAL_KEY}|' /opt/meme_bot/.env")
run(f"sed -i 's|IMAGE_API_BASE_URL=.*|IMAGE_API_BASE_URL=https://fal.run|' /opt/meme_bot/.env")
run(f"grep IMAGE_API /opt/meme_bot/.env")

# Install Pillow on server
run("/opt/meme_bot/venv/bin/pip install -q Pillow")
# Install fonts
run("apt-get install -y fonts-dejavu-core 2>/dev/null | tail -1")

run("systemctl restart meme_bot")
time.sleep(4)
run("systemctl status meme_bot --no-pager")
c.close()
