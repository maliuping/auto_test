##############################################################################
# (C) Copyright 2025, Imvision Co., Ltd
# This file is classified as confidential level C3 within Imvision
#
# SPDX-License-Identifier: xxx
#
# Change Logs:
# Date Author Notes
# 2025-12-25 Logan Ma Initialize.
##############################################################################

import os
import pytest
import subprocess
from pathlib import Path
from time import strftime
from html import escape  # using spec html.escape
from _pytest.reports import TestReport
from dotenv import load_dotenv

from helpers.serial_utils import open_serial
from helpers.case_runner import CaseRunner
from helpers.fun_utils import get_env
from helpers.fun_utils import is_driver_loaded, load_driver


def pytest_addoption(parser):
    group = parser.getgroup("platform abstraction")
    group.addoption(
        "--target",
        action="store",
        default=None,
        help="Target profile under auto_test/platforms/targets",
    )


@pytest.fixture(scope="session")
def target_name(request):
    value = request.config.getoption("--target") or os.getenv("AUTO_TEST_TARGET")
    if not value:
        pytest.fail("target is required: use --target or AUTO_TEST_TARGET")
    return value


@pytest.fixture(scope="session")
def resolved_target(target_name):
    from framework.platform_db import PlatformLoader

    platform_root = Path(__file__).resolve().parent / "platforms"
    return PlatformLoader(platform_root).load_target(target_name)


@pytest.fixture(scope="session")
def register_resolver(resolved_target):
    from framework.platform_db import RegisterResolver

    return RegisterResolver(resolved_target)


@pytest.fixture(scope="session")
def shell_compiler(resolved_target):
    from framework.compiler import ShellCompiler

    return ShellCompiler(resolved_target)


@pytest.fixture(scope="session")
def dpu_hal():
    from hal import DpuHal

    return DpuHal()

@pytest.fixture(scope="session")
def env_config():
    """
    Load .env and validate required settings
    """
    env_file = ".env"

    if not os.path.exists(env_file):
        raise FileNotFoundError( f".env nod found: {env_file}")

    load_dotenv(env_file)
    cfg = {
        # server configs
        "repo_dir": get_env("REPO_DIR"),
        "host": get_env("HOST"),
        "port": get_env("PORT"),
        "key": get_env("KEY"),

        # serial configs
        "serial_port": get_env("SERIAL_PORT"),
        "serial_baud": int(get_env("SERIAL_BAUD")),
    }

    return cfg

@pytest.fixture(scope="session")
def serial_port(env_config):
    """
    Create and provide a serial port object.
    """
    port = env_config["serial_port"]
    baud = env_config["serial_baud"]

    ser = open_serial(port, baud)
    print(f"[SERIAL] Opened {port} @ {baud}")

    yield ser

    print(f"[SERIAL] Closing {port}")
    ser.close()

@pytest.fixture(scope="session")
def adb_device():
    # check adb device connect
    out = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    assert "device" in out.stdout, "No adb device found"
    yield


@pytest.fixture(scope="session")
def case_runner(env_config):
    """
    Provide a ready-to-use CaseRunner instance.
    """
    return CaseRunner(
        repo_dir = env_config["repo_dir"],
        host     = env_config["host"],
        port     = env_config["port"],
        key      = env_config["key"],
    )


@pytest.fixture(scope="session")
def _driver_manager():
    """
    Low-level driver manager.
    Not used directly by tests.
    """
    loaded = set()

    def ensure(name: str):
        if name in loaded:
            return

        if not is_driver_loaded(name):
            load_driver(name)
            # verify load loaded success
            if not is_driver_loaded(name):
                raise RuntimeError(f"Driver '{name}' failed to load")

        loaded.add(name)

    return ensure

# ----------------------
#   pytest_collection
#   │
#   ├─ pytest_runtest_setup        # fixture not inject
#   │
#   ├─ fixture setup phase         # fixture is init here
#   │   ├─ session scope
#   │   ├─ module scope
#   │   ├─ function scope
#   │
#   ├─ pytest_runtest_call         # fixture is available here
#   │   │
#   │   └─ exec test_xxx()
#   │
#   ├─ pytest_runtest_teardown
#   │
#   └─ fixture teardown phase
# ----------------------

def pytest_runtest_call(item):
    marker = item.get_closest_marker("require_driver")
    if not marker:
        return

    driver_names = marker.args
    if not driver_names:
        pytest.fail("require_driver mark requires at least one driver name")

    # get fixture , _driver_manager
    driver_mgr = item.session._driver_manager

    for name in driver_names:
        try:
            driver_mgr(name)
        except Exception as e:
            pytest.skip(f"Required driver '{name}' not available: {e}")



@pytest.fixture(scope="session", autouse=True)
def _register_driver_manager(request, _driver_manager):
    # attach the fixture to the session for hook usage
    # pytest_runtest_call cannot inject fixtures; this is the only way to pass them
    request.session._driver_manager = _driver_manager



# ----------------------
# Html Report
# ----------------------

def pytest_html_report_title(report):
    report.title = "Dpu Sv Test Report"

def pytest_html_results_table_header(cells):
    # Generate the table header using standard HTML strings
    cells.insert(2, '<th>Description</th>')
    cells.insert(1, '<th class="sortable time" col="time">Time</th>')
    cells.pop()

def pytest_html_results_table_row(report, cells):
    if isinstance(report, TestReport):
        # Generate table rows using standard HTML strings
        description = escape(report.description or "")
        timestamp = strftime('%Y-%m-%d %H:%M:%S')
        cells.insert(2, f'<td>{description}</td>')
        cells.insert(1, f'<td class="col-time">{timestamp}</td>')
        cells.pop()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    report.description = str(item.function.__doc__)
