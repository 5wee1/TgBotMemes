import paramiko, sys

HOST, PORT, USER, PASSWORD = "85.198.97.76", 22, "root", "420218"
REMOTE = "/opt/meme_bot"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, PORT, USER, PASSWORD, timeout=15)

def run(cmd):
    _, o, e = client.exec_command(cmd)
    print(o.read().decode(), end="")
    print(e.read().decode(), end="", file=sys.stderr)

# Check .env
run(f"test -f {REMOTE}/.env && echo '.env EXISTS' || echo '.env MISSING'")
run(f"ls {REMOTE}/")
run("systemctl status meme_bot --no-pager 2>&1 | head -20")
client.close()
