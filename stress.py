##############################################################################
# (C) Copyright 2025, Imvision Co., Ltd
# This file is classified as confidential level C3 within Imvision
#
# Change Logs:
# Date Author Notes
# 2025-12-25 Logan Ma Initialize.
##############################################################################

import subprocess
from datetime import datetime
from pathlib import Path

loops = 1
report_dir = Path("reports")
report_dir.mkdir(exist_ok=True)

for i in range(1, loops + 1):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = report_dir / f"report_dpu_{i}_{ts}.html"

    print(f"===== Run {i} =====")
    # dpu and not mipi_format and not hard_reset and not soft_reset and not qchannel_func
    # qchannel_func or simple_layer_func
    # subsys and mipi_format or dpu and format
    # subsys and not based_reg and not display and not test
    cmd = [
        "python", "-m", "pytest",
        "-s", "-v", "--capture=sys",
        "-m", "pipe1_format",
        f"--html={report}"
    ]

    ret = subprocess.run(cmd)
    if ret.returncode != 0:
        # raise RuntimeError(f"Run {i} failed")
        print(f"Run {i} failed")




