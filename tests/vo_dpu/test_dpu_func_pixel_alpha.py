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
from helpers.fun_utils import parse_cu_input_controls


@pytest.mark.dpu
@pytest.mark.pixel_alpha_func
@pytest.mark.require_driver("linlon_dp")
def test_dpu_pixel_alpha_func_034(case_runner):
    """
    DPU.FUNC.034: pixel alpha
    """

    cases = [
        {
            "case_id": "mode6.0",
            "description": "DPU.FUNC.034: pixel alpha PMUL",
            "func": "PMUL",
        },
        {
            "case_id": "mode6.1",
            "description": "DPU.FUNC.034: pixel alpha PAD",
            "func": "PAD",
        }
    ]

    for cfg in cases:
        print(f"\n=== Running {cfg['description']} ===")

        adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

        result = case_runner.run_pipeline(cfg['case_id'])

        assert result == "PASS", f"{cfg['case_id']} failed: {result}"

        rc_bool, stat_str = check_mipi_status(cfg['case_id'], 1080, 1920, "RGB888")

        assert (rc_bool, stat_str) == (True, "OK"), f"{cfg['case_id']} failed: {rc_bool}, {stat_str}"

        func_item = cfg['func']
        if func_item == "PAD":
            FUNC = "PAD"
        else:
            FUNC = "PMUL"

        controls = parse_cu_input_controls(cfg['case_id'])
        print(controls)
        for c in controls:
            if c["input"] == 0:
                assert c["EN"] == "ON", f"{case_id} CU input 0 failed: EN is {c['EN']}"
                assert c[FUNC] == "ON", f"{case_id} CU input 0 failed: {FUNC} is {c[FUNC]}"
            elif c["input"] == 1:
                assert c["EN"] == "ON", f"{case_id} CU input 1 failed: EN is {c['EN']}"
                assert c[FUNC] == "ON", f"{case_id} CU input 1 failed: {FUNC} is {c[FUNC]}"
            elif c["input"] == 2:
                assert c["EN"] == "ON", f"{case_id} CU input 2 failed: EN is {c['EN']}"
                assert c[FUNC] == "ON", f"{case_id} CU input 2 failed: {FUNC} is {c[FUNC]}"
            elif c["input"] == 3:
                assert c["EN"] == "ON", f"{case_id} CU input 3 failed: EN is {c['EN']}"
                assert c[FUNC] == "ON", f"{case_id} CU input 3 failed: {FUNC} is {c[FUNC]}"
            elif c["input"] == 4:
                pass
            else:
                assert False, f"Unexpected input {c['input']} in CU controls"

        print(f"✅ {cfg['description']}: PASS")


@pytest.mark.dpu
@pytest.mark.pixel_global_alpha_func
@pytest.mark.require_driver("linlon_dp")
def test_dpu_pixel_global_alpha_func_035(case_runner):
    """
    DPU.FUNC.035: pixel global alpha
    """
    adb_shell("echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    case_id = "mode6.2"

    print(f"\n=== Running DPU.FUNC.035: pixel global alpha ===")

    result = case_runner.run_pipeline(case_id)
    assert result == "PASS", f"{case_id} failed: {result}"
    rc_bool, stat_str = check_mipi_status(case_id, 1080, 1920, "RGB888")
    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"
    controls = parse_cu_input_controls(case_id)
    print(controls)

    for c in controls:
        if c["input"] == 0:
            print("\n=== hi ===")
            assert c["EN"] == "ON", f"{case_id} CU input 0 failed: EN is {c['EN']}"
            assert c["LALPHA"] == 128, f"{case_id} CU input 0 failed: LALPHA is {c['LALPHA']}"
        elif c["input"] == 1:
            assert c["EN"] == "ON", f"{case_id} CU input 1 failed: EN is {c['EN']}"
            assert c["LALPHA"] == 128, f"{case_id} CU input 1 failed: LALPHA is {c['LALPHA']}"
        elif c["input"] == 2:
            assert c["EN"] == "ON", f"{case_id} CU input 2 failed: EN is {c['EN']}"
            assert c["LALPHA"] == 128, f"{case_id} CU input 2 failed: LALPHA is {c['LALPHA']}"
        elif c["input"] == 3:
            assert c["EN"] == "ON", f"{case_id} CU input 3 failed: EN is {c['EN']}"
            assert c["LALPHA"] == 128, f"{case_id} CU input 3 failed: LALPHA is {c['LALPHA']}"
        elif c["input"] == 4:
            pass
        else:
            assert False, f"Unexpected input {c['input']} in CU controls"

    print(f"✅ DPU.FUNC.035: pixel global alpha: PASS")