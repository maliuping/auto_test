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
from helpers.fun_utils import parse_wb_layer_kv_dict

# the mode used for all wb layer func tests
# cover case DPU.FUNC.004, DPU.FUNC.011, DPU.FUNC.012
# the content is defined in the file mode1.23 located under the sv_case directory.

MODE_NAME = "mode1.23"


@pytest.fixture(scope="session")
def run_wb_layer_func_pipeline(case_runner):
    """
    Run expensive pipeline ONCE per session.
    """
    # mipi output format: rgb888
    adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    result = case_runner.run_pipeline(MODE_NAME)

    return result


@pytest.mark.dpu
@pytest.mark.wb_layer_func
@pytest.mark.require_driver("linlon_dp")
def test_wb_layer_func_004(run_wb_layer_func_pipeline):
    """
    DPU.FUNC.004
    """
    case_id = "DPU.FUNC.004"

    assert run_wb_layer_func_pipeline == "PASS", \
    f"{case_id} failed: {run_wb_layer_func_pipeline}"

    rc_bool, stat_str = check_mipi_status(MODE_NAME, 1080, 1920, "RGB888")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    # parse "run_cmodel.log" from server by case_runner
    key = parse_wb_layer_kv_dict(MODE_NAME)

    assert key["EN"] == "ON"
    # assert key["LAYER_FORMAT"] == "NV12"

    print(f"✅ {case_id}: PASS")


@pytest.mark.dpu
@pytest.mark.wb_layer_func
@pytest.mark.require_driver("linlon_dp")
def test_wb_layer_func_011(run_wb_layer_func_pipeline):
    """
    DPU.FUNC.011
    """
    case_id = "DPU.FUNC.011"

    assert run_wb_layer_func_pipeline == "PASS", \
    f"{case_id} failed: {run_wb_layer_func_pipeline}"

    rc_bool, stat_str = check_mipi_status(MODE_NAME, 1080, 1920, "RGB888")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    # parse "run_cmodel.log" from server by case_runner
    key = parse_wb_layer_kv_dict(MODE_NAME)

    assert key["EN"] == "ON"
    assert key["LAYER_FORMAT"] == "NV12"

    print(f"✅ {case_id}: PASS")


@pytest.mark.dpu
@pytest.mark.wb_layer_func
@pytest.mark.require_driver("linlon_dp")
def test_wb_layer_func_012(run_wb_layer_func_pipeline):
    """
    DPU.FUNC.012
    """
    case_id = "DPU.FUNC.012"

    assert run_wb_layer_func_pipeline == "PASS", \
    f"{case_id} failed: {run_wb_layer_func_pipeline}"

    rc_bool, stat_str = check_mipi_status(MODE_NAME, 1080, 1920, "RGB888")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    # parse "run_cmodel.log" from server by case_runner
    key = parse_wb_layer_kv_dict(MODE_NAME)

    assert key["EN"] == "ON"
    assert key["LAYER_FORMAT"] == "NV12"

    print(f"✅ {case_id}: PASS")
