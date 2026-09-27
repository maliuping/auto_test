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

@pytest.mark.dpu
@pytest.mark.spec
@pytest.mark.require_driver("linlon_dp")
def test_dpu_spec_001(case_runner):
    """
    DPU.SPEC.001
    """
    case_id = "DPU.SPEC.001"
    case_name = "mode5.0"
    print(f"\n=== Running {case_id} ===")

    result = case_runner.run_pipeline(case_name)

    assert result == "PASS", f"{case_name} failed: {result}"

    print(f"✅ {case_id}: PASS")


@pytest.mark.dpu
@pytest.mark.spec
@pytest.mark.require_driver("linlon_dp")
def test_dpu_spec_002(case_runner):
    """
    DPU.SPEC.002
    """
    case_id = "DPU.SPEC.002"
    case_name = "mode5.1"
    print(f"\n=== Running {case_id} ===")

    result = case_runner.run_pipeline(case_name)

    assert result == "PASS", f"{case_name} failed: {result}"

    print(f"✅ {case_id}: PASS")

@pytest.mark.dpu
@pytest.mark.spec
@pytest.mark.require_driver("linlon_dp")
def test_dpu_spec_003(case_runner):
    """
    DPU.SPEC.003
    """
    case_id = "DPU.SPEC.003"
    case_name = "mode5.2"
    print(f"\n=== Running {case_id} ===")

    result = case_runner.run_pipeline(case_name)

    assert result == "PASS", f"{case_name} failed: {result}"

    print(f"✅ {case_id}: PASS")
