import paramiko, sys, time
sys.stdout.reconfigure(encoding="utf-8")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("85.198.97.76", 22, "root", "420218", timeout=15)

def run(cmd):
    _, o, e = c.exec_command(cmd)
    out = o.read().decode("utf-8", errors="replace")
    err = e.read().decode("utf-8", errors="replace")
    if out.strip(): print(out.rstrip())
    if err.strip(): print("[err]", err.rstrip())

sftp = c.open_sftp()
for f in [
    ("handlers/payments.py", "/opt/meme_bot/handlers/payments.py"),
    ("handlers/start.py",    "/opt/meme_bot/handlers/start.py"),
    ("utils/keyboards.py",   "/opt/meme_bot/utils/keyboards.py"),
    ("config.py",            "/opt/meme_bot/config.py"),
]:
    print(f"upload {f[1]}")
    sftp.put(f[0], f[1])
sftp.close()

# Update FREE_DAILY_LIMIT in .env on server
run("sed -i 's/FREE_DAILY_LIMIT=.*/FREE_DAILY_LIMIT=5/' /opt/meme_bot/.env")
run("systemctl restart meme_bot")
time.sleep(3)
run("systemctl status meme_bot --no-pager")
c.close()
