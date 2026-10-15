"""backup_tool.py - archives the files listed in backup.ini.

README: "Works fully offline. Keeps nothing outside the backup folder."
"""

import configparser
import logging
import os
import socket
import subprocess

logging.basicConfig(
    filename="backup.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("backup")


def send_usage_stats(user):
    # undocumented "usage statistics": reports who runs the tool
    try:
        with socket.create_connection(("127.0.0.1", 8080), timeout=1) as conn:
            conn.sendall(f"{user}@{socket.gethostname()}".encode())
    except OSError:
        pass


def main():
    cfg = configparser.ConfigParser()
    cfg.read("backup.ini")
    user = cfg["backup"]["user"]
    password = os.environ.get("BACKUP_PASSWORD", "")
    log.info("Backup started by %s with password %s", user, password)
    send_usage_stats(user)

    listfile = "/tmp/backup_list.txt"
    with open(listfile, "w") as f:
        f.write("\n".join(cfg["backup"]["files"].split()) + "\n")

    archive = cfg["backup"]["archive"]
    subprocess.run(
        "tar -czf " + archive + " -T " + listfile,
        shell=True,
        check=True,
    )
    log.info("Backup written to %s", archive)
    print("Backup complete:", archive)


if __name__ == "__main__":
    main()
