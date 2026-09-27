##############################################################################
# (C) Copyright 2025, Imvision Co., Ltd
# This file is classified as confidential level C3 within Imvision
#
# Change Logs:
# Date Author Notes
# 2025-12-25 Logan Ma Initialize.
##############################################################################

import pytest
import re

from helpers.case_runner import CaseRunner
from helpers.fun_utils import check_mipi_status
from helpers.adb_utils import adb_push, adb_shell
from helpers.fun_utils import parse_rich_layer_kv_dict, parse_simple_layer_kv_dict
from helpers.fun_utils import parse_vo_unit
from helpers.serial_utils import collect_serial_log

@pytest.mark.subsys
@pytest.mark.test
@pytest.mark.require_driver("linlon_dp")
def test_vo_test_crc_001(case_runner):
    """
    VO.TEST.001: EDPI DRC vs PPI CRC check
    """
    case_id = "mode8.0"
    description = "VO.TEST.001: EDPI DRC vs PPI CRC check"

    ctool = "im_vo_unit"
    run_cmd = "im_vo_unit -m 1 -w 1080 -h 1920 -f 4"

    print(f"\n=== Running {description} ===")

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

    print(f"✅ {description}: PASS")


def parse_devmem_crc(output):
    """
    Extract hex value from devmem output
    return int
    """
    m = re.search(r'0x([0-9a-fA-F]{8})', output)
    if not m:
        raise ValueError(f"Invalid devmem output: {output!r}")
    return int(m.group(1), 16)



@pytest.mark.subsys
@pytest.mark.test
def test_vo_test_pipeline_002(adb_device, serial_port):
    """
    VO.TEST.002: VoSubsys dpu vpg pipeline test
    """
    case_id = "VO.TEST.002"
    case_name = "VoSubsys dpu vpg pipeline test"

    print(f"\n=== Running {case_name} ===")

    local_script = "scripts/check_vosubsys_dpu_vpg_pipeline.sh"
    remote_script = "/tmp/dpu_test/check_vosubsys_dpu_vpg_pipeline.sh"

    # push to device
    adb_push(local_script, remote_script)
    adb_shell(f"chmod +x {remote_script}")

    print("Running shell script on DUT...")
    rc, output, stderr = adb_shell(f"sh {remote_script} on")

    print("ADB output:")
    print(output)

    if "Done" not in output:
        raise AssertionError(f"{case_name} failed: Script did not complete successfully")

    # enable pkt monitor
    # "echo status 1-1 > /sys/kernel/debug/dsi-tx0/monitor"
    # above command can disable monitor, so we enable it here
    adb_shell("devmem 0x160a2058 32 0x1")
    # enable ppi crc
    adb_shell("devmem 0x160a203c 32 0x1")

    _, ppi_out, _ = adb_shell("devmem 0x160a2038")
    _, edpi_out, _ = adb_shell("devmem 0x1604001c")

    rc, output, stderr = adb_shell(f"sh {remote_script} off")

    dpu_vpg_crc_ref = 0x9908db23
    ppi_crc = parse_devmem_crc(ppi_out)
    edpi_crc = parse_devmem_crc(edpi_out)
    print(f"PPI_CRC={ppi_crc}, EDPI_CRC={edpi_crc}")

    assert ppi_crc == edpi_crc, \
        f"{case_name} failed: PPI_CRC=0x{ppi_crc:08x}, EDPI_CRC=0x{edpi_crc:08x}"
    assert edpi_crc == dpu_vpg_crc_ref, \
        f"{case_name} failed: EDPI_CRC=0x{edpi_crc:08x}, expected=0x{dpu_vpg_crc_ref:08x}"

    # collect serial output
    logs = collect_serial_log(serial_port, timeout=8)
    print("Captured log:")
    print(logs)

    print(f"✅ {case_id}: {case_name} PASS")


def parse_dpu_polarity(reg):
    vsp = (reg >> 28) & 0x1
    hsp = (reg >> 12) & 0x1

    if vsp == 1 and hsp == 1:
        return "positive"
    elif vsp == 0 and hsp == 0:
        return "negative"
    else:
        return "mixed"

def parse_dsi_polarity(reg):
    vsync = (reg >> 1) & 0x1
    hsync = (reg >> 2) & 0x1

    if vsync == 0 and hsync == 0:
        return "positive"
    elif vsync == 1 and hsync == 1:
        return "negative"
    else:
        return "mixed"


@pytest.mark.subsys
@pytest.mark.test
@pytest.mark.require_driver("linlon_dp")
def test_vo_test_polarity_003(case_runner):
    """
    VO.TEST.003: VO Subsystem Signal Polarity Test
    """
    case_id = "mode8.0"
    description = "VO.TEST.003: VO Subsystem Signal Polarity Test"

    ctool = "im_vo_unit"
    run_cmd = "im_vo_unit -m 1 -w 1080 -h 1920 -f 4"

    # bit28: vsp, 0: negative, 1: positive
    # bit12: hsp, 0: negative, 1: positive
    # dpu_polarity_excpected_positive = 0x10061008
    # dpu_polarity_excpected_negative = 0x00060008

    # bit1: vsync, 0: active high, 1: active low
    # bit2: hsync, 0: active high, 1: active low
    # dsi_polarity_expected_positive = 0x00000000
    # dsi_polarity_expected_negative = 0x00000006

    print(f"\n=== Running {description} ===")

    # mipi output format: rgb888
    adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    # based im_vo_unit
    result = case_runner.run_custom_pipeline(case_id, ctool, run_cmd)

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status(case_id, 1080, 1920, "RGB888")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    key = parse_vo_unit(case_id)

    # check polarity
    dpu_reg = key["DPU_POLARITY"]
    dsi_reg = key["DSI_POLARITY"]

    print(f"DPU polarity reg: 0x{dpu_reg:08x}")
    print(f"DSI polarity reg: 0x{dsi_reg:08x}")

    dpu_pol = parse_dpu_polarity(dpu_reg)
    dsi_pol = parse_dsi_polarity(dsi_reg)

    assert dpu_pol in ("positive", "negative"), f"Invalid DPU polarity: {dpu_pol}"
    assert dsi_pol in ("positive", "negative"), f"Invalid DSI polarity: {dsi_pol}"

    assert dpu_pol == dsi_pol, (
        f"{description} failed: polarity mismatch "
        f"(DPU={dpu_pol}, DSI={dsi_pol})"
    )

    print(f"✅ {description}: PASS")