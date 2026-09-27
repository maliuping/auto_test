#!/bin/bash

#----------------------------------------
# Configuration
#----------------------------------------
BS_ACTIVESIZE_ADDR=0x16001ee0
BS_ACTIVESIZE_SETVAL=0x07800438

GCU_CONTROL_ADDR=0x160000d0
GCU_CONTROL_DFVAL=0x00000000

GCU_STATUS_ADDR=0x160000b0
GCU_STATUS_DFVAL=0x00000000

DOU_STATUS_ADDR=0x160018b0
DOU_STATUS_DFVAL=0x00000000

CU_STATUS_ADDR=0x16000eb0
CU_STATUS_DFVAL=0x00000000

#----------------------------------------
# Function: Read register value
#----------------------------------------
read_reg() {
    val=$(devmem $1)
    echo $val
}

normalize() { echo "$1" | tr 'A-F' 'a-f'; }

#----------------------------------------
# Step 1: Read original value
#----------------------------------------
echo "=== Step 1: Read original register value ==="
orig_val=$(read_reg $BS_ACTIVESIZE_ADDR)
echo "Original value: $orig_val"

#----------------------------------------
# Step 2: Write test value
#----------------------------------------
echo "=== Step 2: Write test value $BS_ACTIVESIZE_SETVAL ==="
devmem $BS_ACTIVESIZE_ADDR 32 $BS_ACTIVESIZE_SETVAL >/dev/null

echo "Value after write:"
set_val=$(read_reg $BS_ACTIVESIZE_ADDR)
echo "$set_val"

#----------------------------------------
# Step 3: Change DPU soft reset
#----------------------------------------
echo "=== Step 3: Change DPU soft reset ==="
devmem $GCU_CONTROL_ADDR 32 0x10000 >/dev/null

#----------------------------------------
# Step 4: Read status registers and compare
#----------------------------------------
echo "=== Step 6: Check status registers after reset ==="

check_status() {
    local name=$1
    local addr=$2
    local expect=$3

    val=$(read_reg $addr)
    norm_val=$(normalize "$val")
    norm_expect=$(normalize "$expect")

    printf "%-20s Read: %s  Expect: %s " "$name" "$val" "$expect"

    if [ "$norm_val" == "$norm_expect" ]; then
        echo -e "\033[32m[OK]\033[0m"
        return 0
    else
        echo -e "\033[31m[NG]\033[0m"
        return 1
    fi
}

overall=0

check_status "GCU_STATUS"   $GCU_STATUS_ADDR   $GCU_STATUS_DFVAL || overall=1
check_status "DOU_STATUS"   $DOU_STATUS_ADDR   $DOU_STATUS_DFVAL || overall=1
check_status "CU_STATUS"    $CU_STATUS_ADDR    $CU_STATUS_DFVAL || overall=1
check_status "BS_ACTIVESIZE_ADDR"     $BS_ACTIVESIZE_ADDR          $BS_ACTIVESIZE_SETVAL || overall=1

echo ""
if [ $overall -eq 0 ]; then
    echo -e "\033[32m[FINAL PASS] All status registers match default values.\033[0m"
else
    echo -e "\033[31m[FINAL FAIL] Some status registers do NOT match default values.\033[0m"
fi
