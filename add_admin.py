import paramiko, sys, time
sys.stdout.reconfigure(encoding="utf-8")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("85.198.97.76", 22, "root", "420218", timeout=15)
def run(cmd):
    _, o, e = c.exec_command(cmd)
    out = o.read().decode("utf-8", errors="replace")
    if out.strip(): print(out.rstrip())

sftp = c.open_sftp()
sftp.put("providers/image_provider.py", "/opt/meme_bot/providers/image_provider.py")
print("uploaded image_provider.py")
sftp.close()

run("sed -i 's|ADMIN_IDS=.*|ADMIN_IDS=1106469742,1143899559|' /opt/meme_bot/.env")
run("grep ADMIN_IDS /opt/meme_bot/.env")
run("systemctl restart meme_bot")
time.sleep(4)
run("systemctl status meme_bot --no-pager")
c.close()
