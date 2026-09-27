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

from helpers.adb_utils import adb_push, adb_shell
from helpers.fun_utils import check_mipi_status
from helpers.fun_utils import parse_vo_unit_event

@pytest.fixture(scope="session")
def demo_pipeline_result(case_runner):
    """
    Run expensive pipeline ONCE per session.
    """
    case_id = "mode8.0"

    ctool = "im_vo_unit"
    run_cmd = "im_vo_unit -m 1 -w 1080 -h 1920 -f 4 -V 1"

    # mipi output format: rgb888
    adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    # based im_vo_unit
    result = case_runner.run_custom_pipeline(case_id, ctool, run_cmd)

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status(case_id, 1080, 1920, "RGB888")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    event_lists = parse_vo_unit_event(case_id)
    print(event_lists)

    assert any(e["type"] == "FLIP" for e in event_lists)
    assert any(e["type"] == "VBLANK" for e in event_lists)

    return result


CASE_IDS = [
    "VO.INTR.002",
    "VO.INTR.003",
]

@pytest.mark.subsys
@pytest.mark.intr
@pytest.mark.require_driver("linlon_dp")
@pytest.mark.parametrize("case_id", CASE_IDS)
def test_vo_test_intr(case_id, demo_pipeline_result):
    """
    Single pipeline, multiple logical cases
    """
    # In consideration of saving time,
    # in 'intf case', include 'VO.SC.001', 'VO.DISPLAY.006'
    assert demo_pipeline_result == "PASS", \
        f"{case_id} failed: {demo_pipeline_result}"

    print(f"✅ {case_id}: PASS")