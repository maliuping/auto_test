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
from helpers.fun_utils import parse_cu_info_dict

@pytest.mark.dpu
@pytest.mark.z_order_func
@pytest.mark.require_driver("linlon_dp")
def test_z_order_func_022(case_runner):
    """
    DPU.FUNC.022: z-order
    """
    cases = [
        {
            "case_id": "mode3.1",
            "description": "DPU.FUNC.022: z-order: 0 1 2 3",
            "EX_CU_INPUT_ID0": 0x1000,
            "EX_CU_INPUT_ID1": 0x1010,
            "EX_CU_INPUT_ID2": 0x1020,
            "EX_CU_INPUT_ID3": 0x1030,
        },
        {
            "case_id": "mode3.2",
            "description": "DPU.FUNC.022: z-order: 0 1 3 2",
            "EX_CU_INPUT_ID0": 0x1000,
            "EX_CU_INPUT_ID1": 0x1010,
            "EX_CU_INPUT_ID2": 0x1030,
            "EX_CU_INPUT_ID3": 0x1020,
        },
        {
            "case_id": "mode3.3",
            "description": "DPU.FUNC.022: z-order: 0 2 1 3",
            "EX_CU_INPUT_ID0": 0x1000,
            "EX_CU_INPUT_ID1": 0x1020,
            "EX_CU_INPUT_ID2": 0x1010,
            "EX_CU_INPUT_ID3": 0x1030,
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
        key = parse_cu_info_dict(cfg['case_id'])

        assert key["CU_INPUT_ID0"] == hex(cfg['EX_CU_INPUT_ID0'])
        assert key["CU_INPUT_ID1"] == hex(cfg['EX_CU_INPUT_ID1'])
        assert key["CU_INPUT_ID2"] == hex(cfg['EX_CU_INPUT_ID2'])
        assert key["CU_INPUT_ID3"] == hex(cfg['EX_CU_INPUT_ID3'])


    print(f"✅ {cfg['case_id']}: PASS")
