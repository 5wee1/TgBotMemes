"""One-shot deploy script: rsync project to server and restart service."""
import paramiko
import os
import sys

HOST = "85.198.97.76"
PORT = 22
USER = "root"
PASSWORD = "420218"
REMOTE_PATH = "/opt/meme_bot"
SERVICE = "meme_bot"

LOCAL_PATH = os.path.dirname(os.path.abspath(__file__))

EXCLUDE = {".git", "__pycache__", "*.pyc", "venv", ".venv", "memes.db", "*.log", "deploy.py"}


def run(client: paramiko.SSHClient, cmd: str, check=True) -> str:
    print(f"  $ {cmd}")
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out.strip():
        print(out.rstrip())
    if err.strip():
        print(err.rstrip(), file=sys.stderr)
    return out


def upload(sftp: paramiko.SFTPClient, local_dir: str, remote_dir: str):
    try:
        sftp.mkdir(remote_dir)
    except OSError:
        pass

    for name in os.listdir(local_dir):
        if any(name == e or name.endswith(e.lstrip("*")) for e in EXCLUDE):
            continue
        local_path = os.path.join(local_dir, name)
        remote_path = f"{remote_dir}/{name}"
        if os.path.isdir(local_path):
            upload(sftp, local_path, remote_path)
        else:
            print(f"  upload {remote_path}")
            sftp.put(local_path, remote_path)


def main():
    print(f"Connecting to {HOST}…")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, USER, PASSWORD, timeout=15)
    print("Connected.")

    run(client, f"mkdir -p {REMOTE_PATH}")
    run(client, f"apt-get install -y python3.11 python3.11-venv python3-pip 2>/dev/null | tail -1")

    sftp = client.open_sftp()
    print("\nUploading files…")
    upload(sftp, LOCAL_PATH, REMOTE_PATH)
    sftp.close()
    print("Upload done.")

    print("\nSetting up venv & deps…")
    run(client, f"cd {REMOTE_PATH} && python3.11 -m venv venv 2>/dev/null || python3 -m venv venv")
    run(client, f"cd {REMOTE_PATH} && venv/bin/pip install -q --upgrade pip && venv/bin/pip install -q -r requirements.txt")

    print("\nInstalling systemd service…")
    run(client, f"cp {REMOTE_PATH}/meme_bot.service /etc/systemd/system/")
    run(client, "systemctl daemon-reload")
    run(client, f"systemctl enable {SERVICE}")

    # Check .env exists on server
    _, out, _ = client.exec_command(f"test -f {REMOTE_PATH}/.env && echo yes || echo no")
    has_env = out.read().decode().strip()
    if has_env == "no":
        print(f"\n⚠️  No .env on server yet! Copy .env.example to {REMOTE_PATH}/.env and fill in values.")
        print("   Then run: systemctl start meme_bot")
    else:
        run(client, f"systemctl restart {SERVICE} 2>/dev/null || systemctl start {SERVICE}")
        run(client, f"systemctl status {SERVICE} --no-pager")

    client.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
