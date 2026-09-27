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
from helpers.fun_utils import check_mipi_status
from helpers.fun_utils import parse_vo_unit

@pytest.mark.subsys
@pytest.mark.based_reg
@pytest.mark.intf
def test_vo_intf_001(adb_device, serial_port):
    """
    VO.INTF.001: cpu read vo register test

    """
    case_id = "VO.INTF.001"
    case_name = "CPU Read VO Register Test"
    print(f"\n=== Running {case_name} ===")

    local_script = "scripts/check_vosubsys_read_reg.sh"
    remote_script = "/tmp/dpu_test/check_vosubsys_read_reg.sh"

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


@pytest.fixture(scope="session")
def single_mode_pipeline_result(case_runner):
    """
    Run expensive pipeline ONCE per session.
    """
    case_id = "mode8.0"
    ctool = "im_vo_unit"
    run_cmd = "im_vo_unit -m 1 -w 1080 -h 1920 -f 4"


    # mipi output format: rgb888
    adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    # based im_vo_unit
    result = case_runner.run_custom_pipeline(case_id, ctool, run_cmd)

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status(case_id, 1080, 1920, "RGB888")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    key = parse_vo_unit(case_id)

    ppi_crc = key['PPI_CRC']
    edpi_crc = key['EDPI_CRC']
    print(f"PPI_CRC: 0x{ppi_crc:08x}, EDPI_CRC: 0x{edpi_crc:08x}")

    assert key["PPI_CRC"] == key["EDPI_CRC"], "CRC mismatch"

    return result


CASE_IDS = [
    "VO.INTF.002",
    "VO.INTF.003",
    "VO_SC.001",
    "VO.DISPLAY.006",
]

@pytest.mark.subsys
@pytest.mark.intf
@pytest.mark.require_driver("linlon_dp")
@pytest.mark.parametrize("case_id", CASE_IDS)
def test_dpu_single_mode_cases(case_id, single_mode_pipeline_result):
    """
    Single pipeline, multiple logical cases
    """
    # In consideration of saving time,
    # in 'intf case', include 'VO.SC.001', 'VO.DISPLAY.006'
    assert single_mode_pipeline_result == "PASS", \
        f"{case_id} failed: {single_mode_pipeline_result}"

    print(f"✅ {case_id}: PASS")