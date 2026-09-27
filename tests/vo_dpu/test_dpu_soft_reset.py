##############################################################################
# (C) Copyright 2025, Imvision Co., Ltd
# This file is classified as confidential level C3 within Imvision
#
# Change Logs:
# Date Author Notes
# 2025-12-25 Logan Ma Initialize.
##############################################################################

import pytest
from helpers.adb_utils import adb_push, adb_shell
from helpers.serial_utils import collect_serial_log

@pytest.mark.dpu
@pytest.mark.soft_reset
@pytest.mark.based_reg
def test_dpu_soft_reset_001(adb_device, serial_port):
    """
    DPU.SOFTRST.001

    """
    case_id = "DPU.SOFTRST.001"
    case_name = "DPU Soft Reset Test"
    print(f"\n=== Running {case_name} ===")

    local_script = "scripts/check_dpu_soft_reset.sh"
    remote_script = "/tmp/dpu_test/check_dpu_soft_reset.sh"

    # push to device
    adb_push(local_script, remote_script)
    adb_shell(f"chmod +x {remote_script}")

    # Run script and collect ADB output for debugging
    print("Running shell script on DUT...")
    rc, output, stderr = adb_shell(f"sh {remote_script}")
    print("ADB output:")
    print(output)

    # collect serial output
    logs = collect_serial_log(serial_port, timeout=8)
    print("Captured log:")
    print(logs)

    assert "PASS" in output.upper(), f"{case_name} failed"

    print(f"✅ {case_id}: {case_name} PASS")
