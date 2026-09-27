##############################################################################
# (C) Copyright 2025, Imvision Co., Ltd
# This file is classified as confidential level C3 within Imvision
#
# Change Logs:
# Date Author Notes
# 2025-12-25 Logan Ma Initialize.
##############################################################################

import os
import shutil
import time
import platform
import threading
import queue
from datetime import datetime

from helpers.server_utils import server_run, server_push, server_pull
from helpers.adb_utils import adb_shell, adb_push, adb_pull
from helpers.fun_utils import get_env
from helpers.fun_utils import dsi_monitor_worker


DEV_ROOT_DIR = "/tmp/dpu_test"
GEN_LOG_FILE = "gen_case.log"
GEN_RES_FILE = "gen_result.log"
RUN_LOG_FILE = "run_case.log"
RUN_RES_FILE = "result.log"
GEN_CMODEL_CONFIG_FILE = "gen_cmodel_config.log"
RUN_CMODEL_FILE = "run_cmodel.log"
RUN_CMODEL_RESULT_FILE = "run_cmodel_result.log"

CTOOL_DEFAULT="linlondp_cv_unit"
RUN_CMD_DEFAULT = "linlondp_cv_unit -c linlondp_cv_unit_config.xml -d {dev_dir}/dump -R"

class CaseRunner:
    def __init__(self, repo_dir, host, port, key, case_dir="auto_cases"):
        self.repo_dir = repo_dir.rstrip("/\\")
        self.host     = host
        self.port     = int(port)
        self.key      = key
        self.local_case_dir = case_dir

        # 3. create local case directory
        self.local_case_dir = case_dir
        if not os.path.exists(case_dir):
            os.makedirs(case_dir)

        self.system_name = platform.system()
        print(f"system: {self.system_name}")
        if self.system_name == "Windows":
            base = f"{self.repo_dir}/im/sv/argos_v4/display"
        else:
            base = os.path.join(self.repo_dir, "im/sv/argos_v4/display")

        self.display_dir = base
        self.test_dir    = f"{base}/sv_case"
        self.cmodel_dir  = f"{base}/display_cmodel"
        self.template_dir = f"{base}/template"


    # ----------------------
    # 1. Generate case on server
    # ----------------------

    def generate_case(self, case_name):
        ser_dir = f"{self.test_dir}/{case_name}"
        env_setup = f"{self.display_dir}/tools/env_setup.sh"
        gen_cmd = f"gen_case.py -t {self.display_dir}/template -c top_config.yaml -G"

        cmds = [
            f"cd {ser_dir}",
            f"rm -rf configs dump test {GEN_RES_FILE} {GEN_LOG_FILE}",
            f"source {env_setup}",
            f"{gen_cmd} > {GEN_LOG_FILE} 2>&1",
            f"echo $? > {GEN_RES_FILE}",
        ]

        rc, out, err = server_run(self.host, self.port, self.key, " && ".join(cmds))
        if rc != 0:
            return False

        rc, _, _ = server_run(self.host, self.port, self.key, f"exit $(cat {ser_dir}/{GEN_RES_FILE})")
        return rc == 0

    # ----------------------
    # 2. Push case to device
    # ----------------------

    def push_case(self, case_name, ctool="linlondp_cv_unit"):
        ser_dir = f"{self.test_dir}/{case_name}"
        local_dir = os.path.join(self.local_case_dir, case_name)

        if os.path.exists(local_dir):
            shutil.rmtree(local_dir)
        os.makedirs(local_dir)

        # pull config files from server
        if ctool == "im_vo_unit":
            cfgs = [
                "configs/check_result.sh",
                "configs/input/raw_dump",
            ]
        else:
            cfgs = [
                "configs/linlondp_cv_unit_config.xml",
                "configs/check_result.sh",
                "configs/input/mdp"
            ]

        for c in cfgs:
            server_pull(self.host, self.port, self.key, f"{ser_dir}/{c}", local_dir)

        dev_dir = f"{DEV_ROOT_DIR}/{case_name}"
        adb_shell(f"rm -rf {dev_dir}")
        adb_shell(f"mkdir -p {dev_dir}")
        adb_shell(f"mkdir -p {dev_dir}/dump")

        # push all files to device
        for fname in os.listdir(local_dir):
            adb_push(os.path.join(local_dir, fname), dev_dir)

        return True

    # ----------------------
    # 3. Run case on device and pull "dump" to local
    # ----------------------

    def run_case_device(self, case_name, ctool=CTOOL_DEFAULT, run_cmd=RUN_CMD_DEFAULT):

        # use queue to communicate between threads
        result_queue = queue.Queue()

        # dsi monitor thread
        stop_event = threading.Event()
        monitor_thread = threading.Thread(
            target=dsi_monitor_worker,
            args=(stop_event, result_queue, ctool),
            daemon=True
        )

        print("[MONITOR] start dsi monitor thread")
        monitor_thread.start()

        # run case and check thread result
        dev_dir = f"{DEV_ROOT_DIR}/{case_name}"

        if ctool == "im_vo_unit":
            # run_cmd from parameter
            script_cmd = "sh check_result.sh im_vo_unit"
        else:
            # force use default run_cmd
            run_cmd = f"linlondp_cv_unit -c linlondp_cv_unit_config.xml -d {dev_dir}/dump -R"
            script_cmd = "sh check_result.sh linlondp_cv_unit"

        try:
            cmds = [
                f"cd {dev_dir}",
                f"{run_cmd} | tee {RUN_LOG_FILE}",
                f"{script_cmd}"
            ]
            rc, out, err = adb_shell(" && ".join(cmds))

        finally:
            stop_event.set()
            monitor_thread.join(timeout=12.0)
            if not result_queue.empty():
                result = result_queue.get()
            else:
                result = False
            print("[MONITOR] dsi monitor thread stopped")

        if (rc != 0) or (ctool == "im_vo_unit" and result is False):
            return False

        # check if result.log is an empty file
        rc, out, err = adb_shell(f"cat {dev_dir}/{RUN_RES_FILE}")
        out_first_line = out.splitlines()[0] if out else ""
        if rc != 0 or out_first_line != "PASS":
            print(f"from {RUN_RES_FILE}: \n\r {out} \n")
            return False

        # pull the dump folder: delete local copy first, then pull
        local_dir = os.path.join(self.local_case_dir, case_name)
        dump_local = os.path.join(local_dir, "dump")
        dump_remote = f"{dev_dir}/dump"

        if os.path.exists(dump_local):
            shutil.rmtree(dump_local)

        adb_pull(dump_remote, dump_local)

        # pull "result.log" to local
        local_dir = os.path.join(self.local_case_dir, case_name)
        dump_local = os.path.join(local_dir, RUN_RES_FILE)
        dump_remote = f"{dev_dir}/{RUN_RES_FILE}"

        if os.path.exists(dump_local):
            shutil.rmtree(dump_local)

        adb_pull(dump_remote, dump_local)

        return True

    # ----------------------
    # 4. collect demsag logs
    # ----------------------
    def collect_dmesg_logs(self, case_name):
        """
        Collect dmesg logs from device
        """

        dev_dir = f"{DEV_ROOT_DIR}/{case_name}"
        local_dir = os.path.join(self.local_case_dir, case_name)

        os.makedirs(local_dir, exist_ok=True)

        dmesg_local = os.path.join(local_dir, "dmesg.log")
        dmesg_remote = f"{dev_dir}/dmesg.log"

        # 1) clear old dmesg logs
        # 2) monitor mipi data
        # move 1&2 to dsi_monitor_worker

        # 3) collect dmesg on device
        print("[DMESG] collecting dmesg")
        adb_shell(f"dmesg > {dmesg_remote}")

        # 4) pull to local
        if os.path.exists(dmesg_local):
            os.remove(dmesg_local)

        adb_pull(dmesg_remote, dmesg_local)

        print(f"[DMESG] saved to {dmesg_local}")

        return True


    # ----------------------
    # 5. Push "dump" to server
    # ----------------------
    def push_files_to_server(self, case_name):
        """
        Push local dump to server
        <local_case_dir>/<case_name>/dump -> <test_dir>/<case_name>/dump
        """

        local_dump = os.path.join(self.local_case_dir, case_name, "dump")
        remote_dump = f"{self.test_dir}/{case_name}/dump"

        if not os.path.exists(local_dump):
            print(f"[WARN] Local dump not found: {local_dump}")
            return False

        # 1) remove old dump
        server_run(self.host, self.port, self.key, f"rm -rf {remote_dump}")

        # 2) recreate empty dump folder
        server_run(self.host, self.port, self.key, f"mkdir -p {remote_dump}")

        # 3) push contents instead of folder
        print(f"Pushing dump contents: {local_dump}/*  ->  {remote_dump}")
        if self.system_name == "Windows":
            src = local_dump + "\\*"
        else:
            src = local_dump + "/*"

        rc = server_push(self.host, self.port, self.key, src, remote_dump)

        return rc == 0


    # ----------------------
    # 6. Run cmodel on server and pull run_cmodel.log
    # ----------------------

    def run_cmodel(self, case_name):
        ser_dir = f"{self.test_dir}/{case_name}"
        env_setup = f"{self.display_dir}/tools/env_setup.sh"

        gen_cmd = f"gen_cmodel_config.py -i {self.cmodel_dir} -r {ser_dir}/dump -b {ser_dir}/configs/input/mdp -o {ser_dir}/test"
        run_cmd = f"run_cmodel.py -i {ser_dir}/test -c {self.cmodel_dir}"

        cmds = [
            f"cd {ser_dir}",
            f"source {env_setup}",
            f"{gen_cmd} > {GEN_CMODEL_CONFIG_FILE}",
            f"{run_cmd} | tee {RUN_CMODEL_FILE}",
        ]

        server_run(self.host, self.port, self.key, " && ".join(cmds))

        rc, _, _ = server_run(self.host, self.port, self.key, f"exit $(cat {ser_dir}/{RUN_CMODEL_RESULT_FILE})")
        if rc != 0:
            return False

        # pull run_cmodel.log to local
        local_cmodel_log = os.path.join(self.local_case_dir, case_name, "run_cmodel.log")
        remote_cmodel_log = f"{self.test_dir}/{case_name}/run_cmodel.log"
        rc = server_pull(self.host, self.port, self.key, remote_cmodel_log, local_cmodel_log)
        if rc != 0:
            return False

        return True

    # ----------------------
    # Full pipeline
    # ----------------------

    def run_pipeline(self, case_name, collect=True):
        """
        Full pipeline to run a test case:
        case_name: name of the test case
        collect: whether to collect dmesg logs from device, default True
        """
        print(f"\n=== GENERATE {case_name} ===")
        if not self.generate_case(case_name):
            return "GEN_FAIL"

        print(f"\n=== PUSH To Device {case_name} ===")
        if not self.push_case(case_name):
            return "PUSH_DEVICE_FAIL"

        print(f"\n=== RUN DEVICE {case_name} ===")
        if not self.run_case_device(case_name):
            return "RUN_FAIL"

        if collect:
            print(f"\n=== COLLECT DMESG {case_name} ===")
            if not self.collect_dmesg_logs(case_name):
                return "COLLECT_DMESG_FAIL"

        print(f"\n=== PUSH To Server {case_name} ===")
        if not self.push_files_to_server(case_name):
            return "PUSH_SERVER_FAIL"

        print(f"\n=== RUN CMODEL {case_name} ===")
        if not self.run_cmodel(case_name):
            return "CMODEL_FAIL"

        return "PASS"


    # ----------------------
    # this pipeline based on im_vo_unit
    # ----------------------

    def run_custom_pipeline(self, case_name, ctool, run_cmd, collect=True):
        """
        Custom pipeline to run a test case:
        """
        print(f"\n=== GENERATE {case_name} ===")
        if not self.generate_case(case_name):
            return "GEN_FAIL"

        print(f"\n=== PUSH To Device {case_name} ===")
        if not self.push_case(case_name, ctool):
            return "PUSH_DEVICE_FAIL"

        print(f"\n=== RUN DEVICE {case_name} ===")
        if not self.run_case_device(case_name, ctool, run_cmd):
            return "RUN_FAIL"

        # print(f"\n=== STOP CTOOL im_vo_unit {case_name} ===")


        if collect:
            print(f"\n=== COLLECT DMESG {case_name} ===")
            if not self.collect_dmesg_logs(case_name):
                return "COLLECT_DMESG_FAIL"

        return "PASS"

