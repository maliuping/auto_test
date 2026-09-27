##############################################################################
# (C) Copyright 2025, Imvision Co., Ltd
# This file is classified as confidential level C3 within Imvision
#
# Change Logs:
# Date Author Notes
# 2025-12-25 Logan Ma Initialize.
##############################################################################

import subprocess

def adb_push(local_path: str, remote_path: str):
    cmd = ["adb", "push", local_path, remote_path]
    subprocess.run(cmd, check=True, capture_output=True)

def adb_pull(remote_path: str, local_path: str):
    result = subprocess.run(["adb", "pull", remote_path, local_path], capture_output=True, text=True)
    return result.returncode

def adb_shell(command: str):
    cmd = ["adb", "shell", command]
    print("ADB SHELL:", " ".join(cmd))
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    # return result.stdout.strip()
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def adb_reboot():
    return subprocess.run(["adb", "reboot"]).returncode