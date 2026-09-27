##############################################################################
# (C) Copyright 2025, Imvision Co., Ltd
# This file is classified as confidential level C3 within Imvision
#
# Change Logs:
# Date Author Notes
# 2025-12-25 Logan Ma Initialize.
##############################################################################

import pytest
import time
import threading

from helpers.adb_utils import adb_push, adb_shell
from helpers.fun_utils import check_underrun, check_overrun

# the mode used for all exception interrupt tests
# the mode is simple mode with one layer

@pytest.fixture(scope="function")
def dpu_underun_injection_setup_teardown():
    """
    Fixture to setup and teardown DPU fault injection environment.
    """
    # Setup: Inject fault for underrun exception
    # w: AWQOS=15，BURSTLEN=16, BOUTSTDCAB = 128 , AOUTSTDCAB = 128
    adb_shell("devmem 0x160002d0 32 0x0F108080")  # Example register setup

    yield

    # Teardown: Remove fault injection
    adb_shell("devmem 0x160002d0 32 0x0F102020")


@pytest.mark.dpu
@pytest.mark.exception_interrupt
@pytest.mark.require_driver("linlon_dp")
def test_dpu_exce_interrupt_underrun(case_runner, dpu_underun_injection_setup_teardown):
    """
    DPU.FUNC.030: underrun exception interrupt test
    """
    case_name = "mode1.26"
    case_runner.run_pipeline(case_name)

    underrun_ids = check_underrun(case_name)
    # print(underrun_ids)
    count = len(underrun_ids)
    print(f"Underrun count: {count}")
    assert count > 0, f"{case_name} failed: underrun count {count}"

    print("✅ DPU.FUNC.030: underrun exception interrupt test: PASS")





@pytest.fixture(scope="function")
def dpu_overrun_injection_setup_teardown():
    """
    Fixture to setup and teardown DPU fault injection environment for overrun.
    """
    # Setup: Inject fault for overrun exception
    # w: AWQOS=15，BURSTLEN=16, OUTSTDCAB = 2
    adb_shell("devmem 0x160002d4 32 0x0F100000")

    yield

    # Teardown: Remove fault injection
    adb_shell("devmem 0x160002d4 32 0x0F100010")



@pytest.mark.dpu
@pytest.mark.exception_interrupt
@pytest.mark.require_driver("linlon_dp")
def test_dpu_exce_interrupt_overrun(case_runner, dpu_overrun_injection_setup_teardown):
    """
    DPU.FUNC.030: overrun exception interrupt test
    """
    case_name = "mode1.26"
    case_runner.run_pipeline(case_name)
    overrun_ids = check_overrun(case_name)
    count = len(overrun_ids)
    print(f"Overrun count: {count}")
    assert count > 0, f"{case_name} failed: overrun count {count}"

    print("✅ DPU.FUNC.030: overrun exception interrupt test: PASS")