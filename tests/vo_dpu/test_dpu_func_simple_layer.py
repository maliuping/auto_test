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
from helpers.fun_utils import parse_simple_layer_kv_dict


@pytest.mark.dpu
@pytest.mark.simple_layer_func
@pytest.mark.require_driver("linlon_dp")
def test_simple_layer_func_008(case_runner):
    """
    DPU.FUNC.008: Simple layer Inverse Transform
    """
    case_id = "DPU.FUNC.008"

    # mipi output format: rgb888
    adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    result = case_runner.run_pipeline("mode1.22")

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status("mode1.22", 1080, 1920, "RGB888")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    key = parse_simple_layer_kv_dict("mode1.22")

    assert key["IT"] == "ON"
    assert key["EN"] == "ON"
    assert key["LAYER_FORMAT"] == "RG24"

    print(f"✅ {case_id}: PASS")


@pytest.mark.dpu
@pytest.mark.simple_layer_func
def test_simple_layer_func_009():
    """
    DPU.FUNC.009: Simple layer rgb2rgb
    """
    case_id = "DPU.FUNC.009"

    key = parse_simple_layer_kv_dict("mode1.22")

    assert key["EN"] == "ON"
    assert key["LAYER_FORMAT"] == "RG24"
    assert key["RGB"] == "ON"

    print(f"✅ {case_id}: PASS")


@pytest.mark.dpu
@pytest.mark.simple_layer_func
def test_simple_layer_func_010():
    """
    DPU.FUNC.010: Simple layer forward transform
    """
    case_id = "DPU.FUNC.010"

    key = parse_simple_layer_kv_dict("mode1.22")

    assert key["EN"] == "ON"
    assert key["LAYER_FORMAT"] == "RG24"
    assert key["FT"] == "ON"

    print(f"✅ {case_id}: PASS")