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
@pytest.mark.interface
@pytest.mark.based_reg
@pytest.mark.require_driver("linlon_dp")
def test_dpu_interface_001(case_runner):
    """
    DPU.INTERFACE.001
    """
    case_id = "DPU.INTERFACE.001"


    cases = [
        # {
        #     "name": "axi_aout128_bout128_outstd9",
        #     "r_val": "0x0F108080",
        #     "w_val": "0x0F100009",
        # },
        {
            # R: ARQOS=15, BURSTLEN=16, AOUT=64, BOUT=64
            # w: AWQOS=15，BURSTLEN=16, OUTSTDCAB = 3(写事务并发能力被设置为 3)
            "name": "axi_aout64_bout64_outstd3",
            "r_val": "0x0F104040",
            "w_val": "0x0F100003",
        },
        {
            # R: ARQOS=15, BURSTLEN=16, AOUT=32, BOUT=32
            # w: AWQOS=15，BURSTLEN=16, OUTSTDCAB = 16(写事务并发能力被设置为 16)
            "name": "axi_aout32_bout32_outstd16",
            "r_val": "0x0F102020",
            "w_val": "0x0F100010",
        },
    ]

    for cfg in cases:

        print(f"\n=== Run case with cfg: {cfg['name']} ===")

        # 1. set registers
        adb_shell(f"devmem 0x160002d0 32 {cfg['r_val']}")
        adb_shell(f"devmem 0x160002d4 32 {cfg['w_val']}")

        # 2. running pipeline
        result = case_runner.run_pipeline("mode1.0")

        # 3. assert result
        assert result == "PASS", f"{cfg['name']} failed: {result}"

    print(f"✅ {case_id}: PASS")


@pytest.mark.dpu
@pytest.mark.interface
@pytest.mark.based_reg
def test_dpu_interface_002(adb_device, serial_port):
    """
    DPU.INTERFACE.002
    """
    case_id = "DPU.INTERFACE.002"
    print(f"\n=== Running {case_id} ===")

    local_script = "scripts/check_dpu_reg_wr.sh"
    remote_script = "/tmp/dpu_test/check_dpu_reg_wr.sh"

    # push 到 DUT
    adb_push(local_script, remote_script)
    adb_shell(f"chmod +x {remote_script}")

    # Run script and collect ADB output for debugging
    print("Running shell script on DUT...")
    rc, out, err = adb_shell(f"sh {remote_script}")
    print("ADB output:")
    print(out)

    # 收集串口输出
    logs = collect_serial_log(serial_port, timeout=8)
    print("Captured log:")
    print(logs)

    # 校验结果
    assert "PASS" in out.upper(), f"{case_id} failed"

    print(f"✅ {case_id}: PASS")