#!/bin/bash
# Script to verify if DPU register returns to default value after hardware reset

#----------------------------------------
# Configuration
#----------------------------------------
REG_ADDR=0x16001ee0
DEFAULT_VAL=0x01e00280

#----------------------------------------
# Function: Read register value
#----------------------------------------
read_reg() {
    val=$(devmem $1)
    echo $val
}

#----------------------------------------
# Step 1: Read original value
#----------------------------------------
echo "=== Step 1: Read original register value ==="
orig_val=$(read_reg $REG_ADDR)
echo "Original value: $orig_val"

#----------------------------------------
# Step 2: Write test value
#----------------------------------------
echo "=== Step 2: Write test value 0x7800438 ==="
devmem $REG_ADDR 32 0x7800438 >/dev/null

echo "Value after write:"
set_val=$(read_reg $REG_ADDR)
echo "$set_val"

#----------------------------------------
# Step 3: Change DPU clock mux and perform hardware reset
#----------------------------------------
echo "=== Step 3: Change DPU clock mux and trigger hardware reset ==="
devmem 0x2024010 32 0xFFFF >/dev/null
devmem 0x2024010 32 0xacce55 >/dev/null
devmem 0x2024014 32 0x01234567 >/dev/null
devmem 0x2024bd8 32 0x40 >/dev/null
devmem 0x2024bdc 32 0x40 >/dev/null

#----------------------------------------
# Step 4: Read value after reset
#----------------------------------------
echo "=== Step 4: Read register value after reset ==="
after_val=$(read_reg $REG_ADDR)
echo "Value after reset: $after_val"
echo "Expected default value: $DEFAULT_VAL"

#----------------------------------------
# Step 5: Compare and report result (case-insensitive)
#----------------------------------------
# Normalize both to lowercase
lower_after=$(echo "$after_val" | tr 'A-F' 'a-f')
lower_default=$(echo "$DEFAULT_VAL" | tr 'A-F' 'a-f')

if [ "$lower_after" == "$lower_default" ]; then
    echo -e "\033[32m[PASS]\033[0m Register value restored to default."
else
    echo -e "\033[31m[FAIL]\033[0m Register value did not return to default!"
fi
