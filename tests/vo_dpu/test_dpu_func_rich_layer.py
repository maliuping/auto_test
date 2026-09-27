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
from helpers.fun_utils import parse_rich_layer_kv_dict


@pytest.mark.dpu
@pytest.mark.rich_layer_func
@pytest.mark.require_driver("linlon_dp")
def test_rich_layer_func_005(case_runner):
    """
    DPU.FUNC.005: Chroma Interpdation
    """
    case_id = "DPU.FUNC.005"

    # mipi output format: rgb888
    adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    result = case_runner.run_pipeline("mode1.14")

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status("mode1.14", 1080, 1920, "RGB888")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    key = parse_rich_layer_kv_dict("mode1.14")

    # assert key["IT"] == "ON"
    # assert key["EN"] == "ON"
    assert key["CHI422"] == "BILINEAR"
    assert key["CHI420"] == "JPEG"
    assert key["LAYER_FORMAT"] == "NV12"

    print(f"✅ {case_id}: PASS")


@pytest.mark.dpu
@pytest.mark.rich_layer_func
def test_rich_layer_func_006():
    """
    DPU.FUNC.006: YUV2RGB
    """
    case_id = "DPU.FUNC.006"

    key = parse_rich_layer_kv_dict("mode1.14")

    assert key["CHI422"] == "BILINEAR"
    assert key["CHI420"] == "JPEG"
    assert key["LAYER_FORMAT"] == "NV12"

    print(f"✅ {case_id}: PASS")


@pytest.mark.dpu
@pytest.mark.rich_layer_func
def test_rich_layer_func_007():
    """
    DPU.FUNC.007: Inverse transform
    """
    case_id = "DPU.FUNC.007"

    key = parse_rich_layer_kv_dict("mode1.14")

    assert key["IT"] == "ON"

    print(f"✅ {case_id}: PASS")