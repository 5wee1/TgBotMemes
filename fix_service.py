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
    if err.strip(): print("[stderr]", err.rstrip())

# Upload fixed service file
sftp = c.open_sftp()
sftp.put("meme_bot.service", "/opt/meme_bot/meme_bot.service")
sftp.close()

run("cp /opt/meme_bot/meme_bot.service /etc/systemd/system/meme_bot.service")
run("chmod 600 /opt/meme_bot/.env")
run("systemctl daemon-reload")
run("systemctl restart meme_bot")
time.sleep(4)
run("systemctl status meme_bot --no-pager")
c.close()
