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
for local, remote in [
    ("handlers/meme.py",           "/opt/meme_bot/handlers/meme.py"),
    ("providers/image_provider.py","/opt/meme_bot/providers/image_provider.py"),
    ("utils/caption_generator.py", "/opt/meme_bot/utils/caption_generator.py"),
]:
    sftp.put(local, remote)
    print(f"uploaded {remote}")
sftp.close()
run("systemctl restart meme_bot")
time.sleep(4)
run("systemctl status meme_bot --no-pager")
c.close()
