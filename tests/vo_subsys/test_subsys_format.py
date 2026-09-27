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
from helpers.case_runner import CaseRunner
from helpers.fun_utils import check_mipi_status
from helpers.adb_utils import adb_push, adb_shell
from helpers.fun_utils import unload_driver, load_driver



def disable_dsi_tx():
    """
    Disable DSI TX to allow changing bus format
    """
    adb_shell("echo 0 > /sys/kernel/debug/dsi-tx0/vpg")
    adb_shell("echo 0 > /sys/kernel/debug/dsi-tx0/prepare")
    adb_shell("echo 0 > /sys/kernel/debug/panel_tx0/prepare")
    adb_shell("echo 0 > /sys/kernel/debug/panel_tx0/enable")
    adb_shell("echo 0 > /sys/kernel/debug/dsi-tx0/enable")

def enable_dsi_tx():
    """
    Enable DSI TX after changing bus format
    """
    adb_shell("echo 1 > /sys/kernel/debug/dsi-tx0/prepare")
    adb_shell("echo 1 > /sys/kernel/debug/panel_tx0/prepare")
    adb_shell("echo 1 > /sys/kernel/debug/panel_tx0/enable")
    adb_shell("echo 1 > /sys/kernel/debug/dsi-tx0/enable")


#  fixture
#   ├─ setup
#   ├─ yield obj
#   └─ teardown
@pytest.fixture(scope="function")
def set_dsi_bus_format_setup_teardown():

    def _set(target_fmt="rgb888"):
        # unload_driver("linlon-dp")

        # disable_dsi_tx()
        #--------------------------------------
        # modprobe -r linlon_dp im_panel im_mipi_tx dw_dsi_tx dw_phy_tx_fpga vo_ss
        unload_driver("linlon_dp")
        unload_driver("drm_dma_helper")
        unload_driver("im_panel")
        unload_driver("im_mipi_tx")
        unload_driver("dw_dsi_tx")
        unload_driver("dw_dphy_tx_2l_6nm")
        unload_driver("vo_ss")

        # adb_shell("modprobe -a dw_dsi_tx im_mipi_tx vo_ss im_panel dw_phy_tx_fpga")
        # modprobe -a dw_dsi_tx dw_phy_tx_fpga im_mipi_tx vo_ss im_panel

        load_driver("dw_dsi_tx")
        load_driver("im_mipi_tx")
        load_driver("vo_ss")
        load_driver("im_panel")
        load_driver("dw_dphy_tx_2l_6nm")
        load_driver("drm_dma_helper")

        fmt = target_fmt.lower()
        fmt_map = {
            "rgb888":     "0x100a",
            "rgb101010":  "0x1018",
            "yuv422_8":   "0x200f",
            "yuv422_10":  "0x201a",
            "yuv420_8":   "0x2026",
        }

        if fmt not in fmt_map:
            raise ValueError(f"Unsupported format: {target_fmt}")

        adb_shell(f"echo {fmt_map[fmt]} > /sys/kernel/debug/panel_tx0/bus_fmt")
        # adb_shell(f"echo 1 > /sys/kernel/debug/mipi_tx0/hpd")
        time.sleep(0.2)

        adb_shell("modprobe linlon-dp clkvalid=1")

    yield _set

    try:
        adb_shell("echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")
        adb_shell(f"echo 1 > /sys/kernel/debug/mipi_tx0/hpd")
    except Exception as e:
        print(f"[WARN] teardown failed: {e}")




@pytest.mark.subsys
@pytest.mark.mipi_format
@pytest.mark.require_driver("linlon_dp")
def test_vo_mipi_format_001(set_dsi_bus_format_setup_teardown, case_runner):
    """
    VO.FORMAT.001
    Mipi Format: RGB101010
    """
    case_id = "VO.FORMAT.001"

    # adb_shell(f"echo 0x1018 > /sys/kernel/debug/panel_tx0/bus_fmt")

    # Use fixture to set and restore format
    set_dsi_bus_format_setup_teardown("rgb101010")

    result = case_runner.run_pipeline("mode1.0")

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status("mode1.0", 1080, 1920, "RGB101010")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    # restore to RGB888
    # adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    print(f"✅ {case_id}: PASS")


@pytest.mark.subsys
@pytest.mark.mipi_format
@pytest.mark.require_driver("linlon_dp")
def test_vo_mipi_format_002(set_dsi_bus_format_setup_teardown, case_runner):
    """
    VO.FORMAT.002
    Mipi Format: RGB888
    """
    case_id = "VO.FORMAT.002"

    # adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")
    # Use fixture to set and restore format
    set_dsi_bus_format_setup_teardown("rgb888")

    result = case_runner.run_pipeline("mode1.0")

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status("mode1.0", 1080, 1920, "RGB888")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    print(f"✅ {case_id}: PASS")


@pytest.mark.subsys
@pytest.mark.mipi_format
@pytest.mark.require_driver("linlon_dp")
def test_vo_mipi_format_003(set_dsi_bus_format_setup_teardown, case_runner):
    """
    VO.FORMAT.003
    Mipi Format: yuv420_8
    """
    case_id = "VO.FORMAT.003"

    # adb_shell(f"echo 0x2026 > /sys/kernel/debug/panel_tx0/bus_fmt")
    set_dsi_bus_format_setup_teardown("yuv420_8")

    result = case_runner.run_pipeline("mode1.0")

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status("mode1.0", 1080, 1920, "yuv420_8")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    # restore to RGB888
    # adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    print(f"✅ {case_id}: PASS")


@pytest.mark.subsys
@pytest.mark.mipi_format
@pytest.mark.require_driver("linlon_dp")
def test_vo_mipi_format_004(set_dsi_bus_format_setup_teardown, case_runner):
    """
    VO.FORMAT.004
    Mipi Format: yuv422_8
    """
    case_id = "VO.FORMAT.004"

    # adb_shell(f"echo 0x200f > /sys/kernel/debug/panel_tx0/bus_fmt")
    set_dsi_bus_format_setup_teardown("yuv422_8")

    result = case_runner.run_pipeline("mode1.0")

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status("mode1.0", 1080, 1920, "yuv422_8")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    # restore to RGB888
    # adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    print(f"✅ {case_id}: PASS")


@pytest.mark.subsys
@pytest.mark.mipi_format
@pytest.mark.require_driver("linlon_dp")
def test_vo_mipi_format_005(set_dsi_bus_format_setup_teardown, case_runner):
    """
    VO.FORMAT.005
    Mipi Format: yuv422_10
    """
    case_id = "VO.FORMAT.005"

    # adb_shell(f"echo 0x201a > /sys/kernel/debug/panel_tx0/bus_fmt")
    set_dsi_bus_format_setup_teardown("yuv422_10")

    result = case_runner.run_pipeline("mode1.0")

    assert result == "PASS", f"{case_id} failed: {result}"

    rc_bool, stat_str = check_mipi_status("mode1.0", 1080, 1920, "yuv422_10")

    assert (rc_bool, stat_str) == (True, "OK"), f"{case_id} failed: {rc_bool}, {stat_str}"

    # restore to RGB888
    # adb_shell(f"echo 0x100a > /sys/kernel/debug/panel_tx0/bus_fmt")

    print(f"✅ {case_id}: PASS")


