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


@pytest.fixture(scope="session")
def single_mode_pipeline_result(case_runner):
    """
    Run expensive pipeline ONCE per session.
    """
    result = case_runner.run_pipeline("mode1.27")
    return result


CASE_IDS = [
    "VO.SCENARIO.001",
]

@pytest.mark.subsys
@pytest.mark.scenario
@pytest.mark.require_driver("linlon_dp")
@pytest.mark.parametrize("case_id", CASE_IDS)
def test_dpu_single_mode_cases(case_id, single_mode_pipeline_result):
    """
    Single pipeline, multiple logical cases
    """

    assert single_mode_pipeline_result == "PASS", \
        f"{case_id} failed: {single_mode_pipeline_result}"

    print(f"✅ {case_id}: PASS")