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
from helpers.fun_utils import parse_rich_layer_kv_dict, parse_simple_layer_kv_dict

@pytest.mark.dpu
@pytest.mark.flip_func
@pytest.mark.require_driver("linlon_dp")
def test_dpu_hflip_func_031(case_runner):
    """
    DPU.FUNC.031: horizontal flip
    """
    case_id = "mode1.24"
    description = "DPU.FUNC.031: horizontal flip"

    print(f"\n=== Running {description} ===")

    # mipi output format: rgb888
    adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    result = case_runner.run_pipeline(case_id)

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status(case_id, 1080, 1920, "RGB888")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    key = parse_rich_layer_kv_dict(case_id)
    assert key["HFLIP"] == "ON", f"{case_id} rich layer failed: HFLIP is {key['HFLIP']}"

    key = parse_simple_layer_kv_dict(case_id)
    assert key["HFLIP"] == "ON", f"{case_id} simple layer failed: HFLIP is {key['HFLIP']}"

    print(f"✅ {description}: PASS")


@pytest.mark.dpu
@pytest.mark.flip_func
@pytest.mark.require_driver("linlon_dp")
def test_dpu_vflip_func_032(case_runner):
    """
    DPU.FUNC.032: vertical flip
    """
    case_id = "mode1.25"
    description = "DPU.FUNC.032: vertical flip"

    print(f"\n=== Running {description} ===")

    # mipi output format: rgb888
    adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    result = case_runner.run_pipeline(case_id)

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status(case_id, 1080, 1920, "RGB888")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    key = parse_rich_layer_kv_dict(case_id)
    assert key["VFLIP"] == "ON", f"{case_id} rich layer failed: VFLIP is {key['VFLIP']}"

    key = parse_simple_layer_kv_dict(case_id)
    assert key["VFLIP"] == "ON", f"{case_id} simple layer failed: VFLIP is {key['VFLIP']}"

    print(f"✅ {description}: PASS")