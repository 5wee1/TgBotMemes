import paramiko, sys
sys.stdout.reconfigure(encoding="utf-8")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("85.198.97.76", 22, "root", "420218", timeout=15)
_, o, e = c.exec_command("journalctl -u meme_bot -n 50 --no-pager 2>&1")
print(o.read().decode("utf-8", errors="replace"))
print(e.read().decode("utf-8", errors="replace"), file=sys.stderr)
c.close()
