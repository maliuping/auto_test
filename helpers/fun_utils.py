##############################################################################
# (C) Copyright 2025, Imvision Co., Ltd
# This file is classified as confidential level C3 within Imvision
#
# Change Logs:
# Date Author Notes
# 2025-12-25 Logan Ma Initialize.
##############################################################################

import os
import re
import glob
import time
import signal
from helpers.adb_utils import adb_shell

# ----------------------
# case parse
# ----------------------
def parse_run_result(output):
    if "PASS" in output.upper():
        return True
    return False


def parse_result_file(path):
    try:
        with open(path, "r") as f:
            txt = f.read().upper()
            return "PASS" in txt
    except:
        return False

def get_log_text_from_case(log_name, case_name, case_dir="auto_cases"):
    """
    log_name is "run_cmodel.log" or "dmesg.log"
    "run_cmodel" from server by case_runner
    "demseg" from device by case_runner
    """

    log_path = os.path.join(case_dir, case_name, log_name)

    if not os.path.exists(log_path):
        print("run_cmodel.log not found")
        return None

    with open(log_path, "r", errors="ignore") as f:
        log_text = f.read()

    return log_text

# ----------------------
# env
# ----------------------

def get_env(name):
    """
    load required variables, if not, report err
    """
    v = os.getenv(name)
    if v is None or v.strip() == "":
        raise ValueError(f"Missing required environment variable: {name}")
    return v


# ----------------------
# load driver
# ----------------------
def is_driver_loaded(name: str) -> bool:
    rc, out, err = adb_shell(f"lsmod | grep -w {name} || true")
    print(f"--------------{out.splitlines()} -----------\n")
    return bool(out.strip())


def load_driver(name: str):
    if name == "linlon_dp":
        adb_shell("modprobe linlon_dp clkvalid=1")
    else:
        adb_shell(f"modprobe {name}")

def unload_driver(module, retry=10, interval=0.2):
    """
    Ensure kernel module is unloaded
    """
    if not is_driver_loaded(module):
        print(f"[OK] module {module} not loaded")
        return True

    for i in range(retry):
        adb_shell(f"modprobe -r {module} || true")

        if not is_driver_loaded(module):
            print(f"[OK] module {module} unloaded")
            return True

        print(f"[WAIT] {module} still loaded, retry {i+1}/{retry}")
        time.sleep(interval)

    raise RuntimeError(f"Failed to unload module: {module}")


# ----------------------
# kill device process
# ----------------------

def kill_device_process(proc_name):
    cmd = f"""
    pid=$(pidof {proc_name} 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "[KILL] SIGTERM {proc_name} ($pid)"
        kill -2 $pid
        sleep 0.5
        if kill -0 $pid 2>/dev/null; then
            echo "[KILL] SIGKILL {proc_name} ($pid)"
            kill -9 $pid
        fi
    else
        echo "[KILL] {proc_name} not running"
    fi
    """
    adb_shell(cmd)


# ----------------------
# ppi monitor check
# ----------------------
MONITOR_RE = re.compile(
    r"DT:\s*(0x[0-9a-fA-F]+),\s*WC:\s*(\d+),\s*CNT:\s*(\d+)"
)


def parse_packet_monitor(log_text):
    """
    Parse the PPI monitor information from the log text and return the result list.

    Return list of dicts:
    [
        {'dt': 0x3e, 'wc': 3240, 'cnt': 1920},
        ...
    ]
    """
    results = []

    for m in MONITOR_RE.finditer(log_text):
        dt  = int(m.group(1), 16)
        wc  = int(m.group(2))
        cnt = int(m.group(3))
        results.append({
            "dt": dt,
            "wc": wc,
            "cnt": cnt,
        })

    return results


def find_entry(entries, dt, wc, cnt):
    for e in entries:
        if wc == "ignore":
            if e["dt"] == dt and e["cnt"] == cnt:
                return True, e

        if cnt == "ignore":
            if e["dt"] == dt and e["wc"] == wc:
                return True, e

    return False, None


##########################################
def _calc_h_wc(fmt, width):
    #special
    return "ignore"

    if fmt == "rgb888":
        return 8
    elif fmt == "rgb101010":
        return 2
    elif fmt == "yuv422_8":
        return 0
    elif fmt == "yuv422_10":
        return 8
    elif fmt == "yuv420_8":
        return 4
    else:
        raise ValueError(fmt)


def _calc_w_wc(fmt, width):
    if fmt == "rgb888":
        return width * 3
    elif fmt == "rgb101010":
        return int(width * 30 / 8)  # 2048 → 7680
    elif fmt == "yuv422_8":
        return width * 2
    elif fmt == "yuv422_10":
        return int(width * 3)
    elif fmt == "yuv420_8":
        return int(width * 1.5)
    else:
        raise ValueError(fmt)


PPI_FORMATS = {
    "rgb888": {
        "dt": 0x3E,
        "wc_per_pixel": 3,
    },
    "rgb101010": {
        "dt": 0x0D,
        "wc_per_pixel": 30 / 8,  # 3.75
    },
    "yuv422_8": {
        "dt": 0x2C,
        "wc_per_pixel": 2,
    },
    "yuv422_10": {
        "dt": 0x0C,
        "wc_per_pixel": 3,
    },
    "yuv420_8": {
        "dt": 0x3D,
        "wc_per_pixel": 1.5,
    },
}

def expected_ppi_entries(fmt, width, height):
    fmt = fmt.lower()
    fmt_cfg = PPI_FORMATS[fmt]
    dt = fmt_cfg["dt"]

    # height entry（行）
    h_entry = {
        "dt": dt,
        "wc": _calc_h_wc(fmt, width),
        "cnt": height,
    }

    # width entry（行内）
    w_entry = {
        "dt": dt,
        "wc": _calc_w_wc(fmt, width),
        "cnt": "ignore",
    }

    return h_entry, w_entry

def check_mipi_status(case_name, width, height, fmt="RGB888", case_dir="auto_cases"):
    dmesg_path = os.path.join(case_dir, case_name, "dmesg.log")
    if not os.path.exists(dmesg_path):
        return False, "dmesg.log not found"

    with open(dmesg_path, "r", errors="ignore") as f:
        log_text = f.read()

    entries = parse_packet_monitor(log_text)
    if not entries:
        return False, "No monitor entries found"

    h_exp, w_exp = expected_ppi_entries(fmt, width, height)

    ok, _ = find_entry(entries, **h_exp)
    if not ok:
        return False, f"{fmt} height mismatch, expect {h_exp}, got {entries}"

    ok, _ = find_entry(entries, **w_exp)
    if not ok:
        return False, f"{fmt} width mismatch, expect {w_exp}, got {entries}"

    return True, "OK"




def wait_vo_ready(timeout_s=2.0, poll_interval=0.05):
    """
    Poll /tmp/vo_ready for 'DISPLAY_STARTED'
    return True  -> detected
           False -> timeout
    """
    deadline = time.monotonic() + timeout_s

    while time.monotonic() < deadline:
        rc, out, err = adb_shell("cat /tmp/vo_ready")
        if rc == 0:
            contents = out.strip()
            if "DISPLAY_STARTED" in contents:
                return True
        time.sleep(poll_interval)

    return False

def dsi_monitor_worker(stop_event, result_queue, ctool):
    """
    Background worker to control dsi monitor
    """
    # 1) clear old dmesg logs
    adb_shell("dmesg -c || true")

    # 2) wait for vo ready (max 8s)
    if ctool == "im_vo_unit":
        if not wait_vo_ready(timeout_s=8.0):
            print("DISPLAY_STARTED not detected within 8s")
            result_queue.put(False)
        else:
            print("DISPLAY_STARTED detected")
            result_queue.put(True)

    # 3) monitor mipi data
    adb_shell("echo status 1-1 > /sys/kernel/debug/dsi-tx0/monitor || true")
    adb_shell("echo stat_wc 1-1 > /sys/kernel/debug/dsi-tx0/monitor || true")

    if ctool == "im_vo_unit":
        kill_device_process("im_vo_unit")

    # wait until stop_event is set
    while not stop_event.is_set():
        time.sleep(0.2)


VO_UNIT_PATTERN = re.compile(
    r'vo_unit.*?(PPI_CRC|EDPI_CRC|DPU_POLARITY|DSI_POLARITY):0x([0-9a-fA-F]{8})'
)

def parse_vo_unit(case_name, case_dir="auto_cases"):
    """
    Parse all PPI_CRC / EDPI_CRC from vo_unit logs
    return dict: {'PPI_CRC': int, 'EDPI_CRC': int}
    """
    log_text = get_log_text_from_case("dmesg.log", case_name, case_dir)

    vo_unit_dic = {}
    for name, value in VO_UNIT_PATTERN.findall(log_text):
        vo_unit_dic[name] = int(value, 16)
    return vo_unit_dic

VO_UNIT_EVENT_PATTERN = re.compile(
    r'\[vo_unit\]\s+(FLIP|VBLANK):\s+frame=(\d+)\s+ts=(\d+)'
)

def parse_vo_unit_event(case_name, case_dir="auto_cases"):
    """
    return:
    events = [
        {"type": "FLIP", "frame": 10, "ts": 123456},
        {"type": "VBLANK", "frame": 10, "ts": 123460},
    ]
    """
    log_text = get_log_text_from_case("dmesg.log", case_name, case_dir)

    event_items = VO_UNIT_EVENT_PATTERN.findall(log_text)
    events = [
        {"type": t, "frame": int(f), "ts": int(ts)}
        for t, f, ts in event_items
    ]

    return events

# ----------------------
# rich layer pre_process func check
# ----------------------

# regular expression for LPU0_LAYER0 in run_cmodel.log
LPU_LAYER0_BLOCK_RE = re.compile(
    r">>>>>\s*LPU\[0\]_LAYER\[0\]:\s*<<<<<\n"
    r"(.*?)"
    r"(?=\n>>>>>|\Z)",
    re.DOTALL
)

# rich layer regular expression
LAYER0_FUNC_KV_RE = re.compile(
    r"^\s*(IT|EN|CHI422|CHI420|LAYER_FORMAT|HFLIP|VFLIP)\s*:\s*([A-Za-z0-9_.]+)",
    re.MULTILINE
)


def extract_lpu_layer0_block(text: str):
    m = LPU_LAYER0_BLOCK_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()

def parse_rich_layer_kv_dict(case_name, case_dir="auto_cases"):

    # "run_cmodel" from server by case_runner
    log_path = os.path.join(case_dir, case_name, "run_cmodel.log")

    if not os.path.exists(log_path):
        print("run_cmodel.log not found")
        return False

    with open(log_path, "r", errors="ignore") as f:
        log_text = f.read()

    layer0 = extract_lpu_layer0_block(log_text)
    print(layer0)
    if layer0 is None:
        return False

    return {k: v for k, v in LAYER0_FUNC_KV_RE.findall(layer0)}

# ----------------------
# simple layer pre_process func check
# ----------------------

# regular expression for LPU0_LAYER1 in run_cmodel.log
LPU_LAYER1_BLOCK_RE = re.compile(
    r">>>>>\s*LPU\[0\]_LAYER\[1\]:\s*<<<<<\n"
    r"(.*?)"
    r"(?=\n>>>>>|\Z)",
    re.DOTALL
)

# simple layer regular expression
LAYER1_FUNC_KV_RE = re.compile(
    r"^\s*(IT|EN|FT|RGB|LAYER_FORMAT|HFLIP|VFLIP)\s*:\s*([A-Za-z0-9_.]+)",
    re.MULTILINE
)

def extract_lpu_layer1_block(text: str):
    m = LPU_LAYER1_BLOCK_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()

def parse_simple_layer_kv_dict(case_name, case_dir="auto_cases"):

    # "run_cmodel" from server by case_runner
    log_path = os.path.join(case_dir, case_name, "run_cmodel.log")

    if not os.path.exists(log_path):
        print("run_cmodel.log not found")
        return False

    with open(log_path, "r", errors="ignore") as f:
        log_text = f.read()

    layer1 = extract_lpu_layer1_block(log_text)
    print(layer1)
    if layer1 is None:
        return False

    return {k: v for k, v in LAYER1_FUNC_KV_RE.findall(layer1)}


# ----------------------
# wb layer pre_process func check
# ----------------------

# regular expression for LPU0_LAYER[wr] in run_cmodel.log
LPU_WB_BLOCK_RE = re.compile(
    r">>>>>\s*LPU\[0\]_LAYER\[_WR\]:\s*<<<<<\n"
    r"(.*?)"
    r"(?=\n>>>>>|\Z)",
    re.DOTALL
)

# simple layer regular expression
LAYER_WB_YUV2RGB_KV_RE = re.compile(
    r"^\s*(EN|LAYER_FORMAT)\s*:\s*([A-Za-z0-9_.]+)",
    re.MULTILINE
)

def extract_lpu_wb_layer_block(text: str):
    m = LPU_WB_BLOCK_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()

def parse_wb_layer_kv_dict(case_name, case_dir="auto_cases"):

    # "run_cmodel" from server by case_runner
    log_path = os.path.join(case_dir, case_name, "run_cmodel.log")

    if not os.path.exists(log_path):
        print("run_cmodel.log not found")
        return False

    with open(log_path, "r", errors="ignore") as f:
        log_text = f.read()

    wb_layer = extract_lpu_wb_layer_block(log_text)
    print(wb_layer)
    if wb_layer is None:
        return False

    return {k: v for k, v in LAYER_WB_YUV2RGB_KV_RE.findall(wb_layer)}


# ----------------------
# CU func check
# ----------------------

# regular expression for CU[0] in run_cmodel.log
CU_BLOCK_RE = re.compile(
    r">>>>>\s*CU\[0\]\s*<<<<<\n"
    r"(.*?)"
    r"(?=\n>>>>>|\Z)",
    re.DOTALL
)

# CU regular expression
CU_KV_RE = re.compile(
    r"^\s*(CU_INPUT_ID0|CU_INPUT_ID1|CU_INPUT_ID2|CU_INPUT_ID3)\s*:\s*([A-Za-z0-9_.]+)",
    re.MULTILINE
)

# cu input control regular expression
CU_INPUT_CONTROL_RE = re.compile(
    r'CU_INPUT(\d+)_CONTROL\s*'
    r'LALPHA:\s*(\d+)\s*'
    r'PMUL:\s*(\w+)\s*'
    r'PAD:\s*(\w+)\s*'
    r'EN:\s*(\w+)',
    re.MULTILINE
)


def extract_cu_block(text: str):
    m = CU_BLOCK_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()

def parse_cu_info_dict(case_name, case_dir="auto_cases"):

    # "run_cmodel" from server by case_runner
    log_path = os.path.join(case_dir, case_name, "run_cmodel.log")

    if not os.path.exists(log_path):
        print("run_cmodel.log not found")
        return False

    with open(log_path, "r", errors="ignore") as f:
        log_text = f.read()

    cu_info = extract_cu_block(log_text)
    # print(f"\n===\n{cu_info}\n===\n")
    if cu_info is None:
        return False

    return {k: v for k, v in CU_KV_RE.findall(cu_info)}


def parse_cu_input_controls(case_name, case_dir="auto_cases"):
    # "run_cmodel" from server by case_runner
    log_text = get_log_text_from_case("run_cmodel.log", case_name, case_dir)

    results = []

    for idx, lalpha, pmul, pad, en in CU_INPUT_CONTROL_RE.findall(log_text):
        results.append({
            "input": int(idx),
            "LALPHA": int(lalpha),
            "PMUL": pmul,
            "PAD": pad,
            "EN": en,
        })

    return results

# ----------------------
# DOU func check
# ----------------------

# regular expression for DOU[0] in run_cmodel.log
DOU_BLOCK_RE = re.compile(
    r">>>>>\s*DOU\[0\]\s*<<<<<\n"
    r"(.*?)"
    r"(?=\n>>>>>|\Z)",
    re.DOTALL
)

# DOU regular expression
DOU_KV_RE = re.compile(
    r"^\s*(CRC|BS_CRC0_LOW|BS_CRC0_HIGH)\s*:\s*([A-Za-z0-9_.]+)",
    re.MULTILINE
)

def extract_dou_block(text: str):
    m = DOU_BLOCK_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()

def parse_dou_info_dict(case_name, case_dir="auto_cases"):

    # "run_cmodel" from server by case_runner
    log_path = os.path.join(case_dir, case_name, "run_cmodel.log")

    if not os.path.exists(log_path):
        print("run_cmodel.log not found")
        return False

    with open(log_path, "r", errors="ignore") as f:
        log_text = f.read()

    dou_info = extract_dou_block(log_text)
    # print(f"\n===\n{dou_info}\n===\n")
    if dou_info is None:
        return False

    return {k: v for k, v in DOU_KV_RE.findall(dou_info)}


# ----------------------
# DPU Exception Log Check
# ----------------------

UNDERRUN_RE = re.compile(
    r'UNDERRUN\s+frame_id:\s*(\d+)'
)

OVERRUN_RE = re.compile(
    r'OVERRUN\s+frame_id:\s*(\d+)'
)

def check_underrun(case_name, case_dir="auto_cases"):
    """
    demsg log from run_pipeline of case_runner.py,
    run case then get dmesg log from device.
    check mipi status from dmesg log on local PC.
    """
    dmesg_path = os.path.join(case_dir, case_name, "dmesg.log")

    if not os.path.exists(dmesg_path):
        return False, "dmesg.log not found"

    with open(dmesg_path, "r", errors="ignore") as f:
        log_text = f.read()

    # return frame ids []
    frames = UNDERRUN_RE.findall(log_text)

    return frames


def check_overrun(case_name, case_dir="auto_cases"):
    """
    demsg log from run_pipeline of case_runner.py,
    run case then get dmesg log from device.
    check mipi status from dmesg log on local PC.
    """
    dmesg_path = os.path.join(case_dir, case_name, "dmesg.log")

    if not os.path.exists(dmesg_path):
        return False, "dmesg.log not found"

    with open(dmesg_path, "r", errors="ignore") as f:
        log_text = f.read()

    # return frame ids []
    frames = OVERRUN_RE.findall(log_text)

    return frames
