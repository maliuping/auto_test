#!/bin/bash

#----------------------------------------
# Configuration
#----------------------------------------
LPU_IRQ_MASK_ADDR=0x160002a8
LPU_IRQ_MASK_SETVAL=0x00002000

LR_CONTROL_ADDR=0x160004d0
LR_CONTROL_SETVAL=0x30000001

LR0_FORMAT_ADDR=0x160004d8
LR0_FORMAT_SETVAL=0x00000035

LR0_IN_SIZE_ADDR=0x160004e0
LR0_IN_SIZE_SETVAL=0x07800438

CU_INPUT_ID0_ADDR=0x16000e80
CU_INPUT_ID0_SETVAL=0x00001000

DOU0_IRQ_MASK_ADDR=0x160018a8
DOU0_IRQ_MASK_SETVAL=0x00002000

DOU0_IPS_SIZE_ADDR=0x16001ad4
DOU0_IPS_SIZE_SETVAL=0x07800438

BS_ACTIVESIZE_ADDR=0x16001ee0
BS_ACTIVESIZE_SETVAL=0x07800438





#----------------------------------------
# Function: Read register value
#----------------------------------------
read_reg() {
    devmem $1
}

normalize() {
    echo "$1" | tr 'A-F' 'a-f'
}

#----------------------------------------
# Step 1: Write test values
#----------------------------------------
echo "=== Step 1: Write test values ==="

write_and_show() {
    local name=$1
    local addr=$2
    local value=$3

    echo "-- Write $name ($value) --"
    devmem $addr 32 $value >/dev/null
    echo "After write: $(read_reg $addr)"
}

write_and_show "LPU_IRQ_MASK"   $LPU_IRQ_MASK_ADDR      $LPU_IRQ_MASK_SETVAL
write_and_show "LR_CONTROL"     $LR_CONTROL_ADDR        $LR_CONTROL_SETVAL
write_and_show "LR0_FORMAT"     $LR0_FORMAT_ADDR        $LR0_FORMAT_SETVAL
write_and_show "LR0_IN_SIZE"    $LR0_IN_SIZE_ADDR       $LR0_IN_SIZE_SETVAL
write_and_show "CU_INPUT_ID0"   $CU_INPUT_ID0_ADDR      $CU_INPUT_ID0_SETVAL
write_and_show "DOU0_IRQ_MASK"  $DOU0_IRQ_MASK_ADDR     $DOU0_IRQ_MASK_SETVAL
write_and_show "DOU0_IPS_SIZE"  $DOU0_IPS_SIZE_ADDR     $DOU0_IPS_SIZE_SETVAL
write_and_show "BS_ACTIVESIZE"  $BS_ACTIVESIZE_ADDR     $BS_ACTIVESIZE_SETVAL




sleep 0.05

#----------------------------------------
# Step 2: Check registers
#----------------------------------------
echo "=== Step 2: Check registers ==="

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


check_status "LPU_IRQ_MASK"   $LPU_IRQ_MASK_ADDR      $LPU_IRQ_MASK_SETVAL      || overall=1
check_status "LR_CONTROL"     $LR_CONTROL_ADDR        $LR_CONTROL_SETVAL        || overall=1
check_status "LR0_FORMAT"     $LR0_FORMAT_ADDR        $LR0_FORMAT_SETVAL        || overall=1
check_status "LR0_IN_SIZE"    $LR0_IN_SIZE_ADDR       $LR0_IN_SIZE_SETVAL       || overall=1
check_status "CU_INPUT_ID0"   $CU_INPUT_ID0_ADDR      $CU_INPUT_ID0_SETVAL      || overall=1
check_status "DOU0_IRQ_MASK"  $DOU0_IRQ_MASK_ADDR     $DOU0_IRQ_MASK_SETVAL     || overall=1
check_status "DOU0_IPS_SIZE"  $DOU0_IPS_SIZE_ADDR     $DOU0_IPS_SIZE_SETVAL     || overall=1
check_status "BS_ACTIVESIZE"  $BS_ACTIVESIZE_ADDR     $BS_ACTIVESIZE_SETVAL     || overall=1

echo ""
if [ $overall -eq 0 ]; then
    echo -e "\033[32m[FINAL PASS] All status registers match expected values.\033[0m"
else
    echo -e "\033[31m[FINAL FAIL] Some status registers do NOT match expected values.\033[0m"
fi
