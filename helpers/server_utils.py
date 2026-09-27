##############################################################################
# (C) Copyright 2025, Imvision Co., Ltd
# This file is classified as confidential level C3 within Imvision
#
# Change Logs:
# Date Author Notes
# 2025-12-25 Logan Ma Initialize.
##############################################################################

import subprocess
import os

def server_run(host, port, key, cmd, timeout=300):
    """
    Run command on linux server using plink.
    """
    scmd = ["plink", "-batch", "-P", str(port), "-i", key, host, cmd]
    print("SERVER RUN:", " ".join(scmd))

    p = subprocess.run(
        scmd,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return p.returncode, p.stdout, p.stderr


def server_push(host, port, key, local, remote):
    """
    Push file/directory to server.
    """
    cmd = ["pscp", "-batch", "-r", "-P", str(port), "-i", key, local, f"{host}:{remote}"]
    print("SERVER PUSH:", " ".join(cmd))
    return subprocess.run(cmd).returncode


def server_pull(host, port, key, remote, local):
    """
    Pull file/directory from server.
    """
    cmd = ["pscp", "-batch", "-r", "-P", str(port), "-i", key, f"{host}:{remote}", local]
    print("SERVER PULL:", " ".join(cmd))
    return subprocess.run(cmd).returncode
