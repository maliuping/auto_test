#!/bin/bash

# Function to read register value and print it
read_reg() {
    val=$(atool devmem $1)
    # echo "$1: $val"
    echo $val
}

normalize() { echo "$1" | tr 'A-F' 'a-f'; }

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

# Read DPU reg original value
echo "=== Step 1: Read DPU reg original value ==="
read_reg 0x16001ee0

# Set DPU reg value and read back
echo "=== Step 2: Set DPU reg value and read back ==="
devmem 0x16001ee0 32 0x7800438
read_reg 0x16001ee0
check_status "DPU Reg BS_ACTIVESIZE" 0x16001ee0 0x07800438 || overall=1

# Read DSI Host reg original value
echo "=== Step 3: Read DSI Host reg original value ==="
read_reg 0x160a000c

# Set DSI Host reg value and read back
echo "=== Step 4: Set DSI Host reg value and read back ==="
devmem 0x160a000c 32 0x1
read_reg 0x160a000c
check_status "DSI Host Reg DPI_VCID" 0x160a000c 0x00000001 || overall=1

# Read MIPI TX SC reg original value
echo "=== Step 5: Read MIPI TX SC reg original value ==="
read_reg 0x160a2010

# Set MIPI TX SC reg value and read back
echo "=== Step 6: Set MIPI TX SC reg value and read back ==="
devmem 0x160a2010 32 0x06
read_reg 0x160a2010
check_status "MIPI TX SC Reg" 0x160a2010 0x00000006 || overall=1

# Read VO SC reg original value
echo "=== Step 7: Read VO SC reg original value ==="
read_reg 0x16040010

# Set VO SC reg value and read back
echo "=== Step 8: Set VO SC reg value and read back ==="
devmem 0x16040010 32 0x4000
read_reg 0x16040010
check_status "VO SC Reg" 0x16040010 0x00004000 || overall=1

# Change DPU clock mux
echo "=== Step 9: Change DPU clock mux ==="
devmem 0x2024010 32 0xFFFF
devmem 0x2024010 32 0xacce55
devmem 0x2024014 32 0x01234567

# Config HW reset
echo "=== Step 10: Config HW reset ==="
devmem 0x2024bd8 32 0xffffffff
devmem 0x2024bdc 32 0xffffffff
devmem 0x2024e10 32 0x100
devmem 0x2024e14 32 0x100

echo "=== Step 11: Check reg values after HW reset ==="
check_status "DPU Reg" 0x16001ee0 0x01e00280 || overall=1
check_status "DSI Host Reg" 0x160a000c 0x00000000 || overall=1
check_status "MIPI TX SC Reg" 0x160a2010 0x00000000 || overall=1
check_status "VO SC Reg" 0x16040010 0x00000000 || overall=1

echo ""
if [ $overall -eq 0 ]; then
    echo -e "\033[32m[FINAL PASS] All registers match expected values.\033[0m"
else
    echo -e "\033[31m[FINAL FAIL] Some registers did not match expected values.\033[0m"
fi
