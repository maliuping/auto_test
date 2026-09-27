##############################################################################
# (C) Copyright 2025, Imvision Co., Ltd
# This file is classified as confidential level C3 within Imvision
#
# Change Logs:
# Date Author Notes
# 2025-12-25 Logan Ma Initialize.
##############################################################################

import serial
import time

def open_serial(port="com5", baudrate=921600, timeout=2):
    return serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

def collect_serial_log(ser: serial.Serial, timeout: float = 10.0):
    """读取串口日志直到超时"""
    end_time = time.time() + timeout
    log_data = ""
    while time.time() < end_time:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting).decode(errors="ignore")
            log_data += data
        time.sleep(0.1)
    return log_data
