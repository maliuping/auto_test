##############################################################################
# (C) Copyright 2025, Imvision Co., Ltd
# This file is classified as confidential level C3 within Imvision
#
# Change Logs:
# Date Author Notes
# 2025-12-25 Logan Ma Initialize.
##############################################################################

import pytest
from helpers.case_runner import CaseRunner
from helpers.fun_utils import check_mipi_status
from helpers.adb_utils import adb_push, adb_shell
from helpers.fun_utils import parse_dou_info_dict

# the mode used for all crc 64bit func tests
# the mode is same with z-order func tests

@pytest.mark.dpu
@pytest.mark.crc_64bit_func
@pytest.mark.require_driver("linlon_dp")
def test_crc_64bit_func_029(case_runner):
    """
    DPU.FUNC.029: dou 64bit CRC
    """
    cases = [
        {
            "case_id": "mode7.0",
            "description": "DPU.FUNC.029",
            # if return crc is 0, failed
            # expected crc_64 value to be filled after first run
            "crc_64": 0x00,
        },
        {
            "case_id": "mode7.1",
            "description": "DPU.FUNC.029",
            "crc_64": 0x00,
        },
        {
            "case_id": "mode7.2",
            "description": "DPU.FUNC.029",
            "crc_64": 0x00,
        }
    ]

    for cfg in cases:
        print(f"\n=== Running {cfg['description']} ===")

        # mipi output format: rgb888
        adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

        result = case_runner.run_pipeline(cfg['case_id'])

        assert result == "PASS", f"{cfg['case_id']} failed: {result}"

        rc_bool, stat_str = check_mipi_status(cfg['case_id'], 1080, 1920, "RGB888")

        assert (rc_bool, stat_str) == (True, "OK"), f"{cfg['case_id']} failed: {rc_bool}, {stat_str}"

        # parse "run_cmodel.log" from server by case_runner
        key = parse_dou_info_dict(cfg['case_id'])

        # check CRC is ON
        assert key["CRC"] == "ON", F"{cfg['case_id']} failed: CRC not ON"

        crc0_low = key["BS_CRC0_LOW"]
        crc0_high = key["BS_CRC0_HIGH"]
        crc_64 = ( int(crc0_high,16) << 32 ) | int(crc0_low,16)
        # crc_64 is not 0
        assert crc_64 != cfg['crc_64'], f"{cfg['case_id']} failed: crc_64 {hex(crc_64)} == {hex(cfg['crc_64'])}"
        cfg['crc_64'] = crc_64  # update expected crc_64


    assert cases[0]['crc_64'] != cases[1]['crc_64'], \
        f"{cases[0]['case_id']} and {cases[1]['case_id']} have same crc_64 {hex(cases[0]['crc_64'])}"

    assert cases[0]['crc_64'] != cases[2]['crc_64'], \
        f"{cases[0]['case_id']} and {cases[2]['case_id']} have same crc_64 {hex(cases[0]['crc_64'])}"

    assert cases[1]['crc_64'] != cases[2]['crc_64'], \
        f"{cases[1]['case_id']} and {cases[2]['case_id']} have same crc_64 {hex(cases[1]['crc_64'])}"


    print(f"✅ DPU.FUNC.029: PASS")