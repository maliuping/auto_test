#!/bin/bash

# Function to read register value using devmem
read_reg() {
    val=$(devmem $1)
    echo "$1: $val"
}

# Start and end addresses (in hex)
START_ADDR=0x16040000
END_ADDR=0x16040070

# Step size (assuming 4 bytes per register, since 32-bit registers)
STEP=4

echo "=== Reading registers from $START_ADDR to $END_ADDR ==="

# Convert hex to decimal for arithmetic operations
current_addr=$((START_ADDR))

# Loop over the address range using while
while [ $current_addr -le $((END_ADDR)) ]; do
    read_reg $(printf "0x%X" $current_addr)
    current_addr=$((current_addr + STEP))
done

echo -e "\033[32m[FINAL PASS] Finished reading registers.\033[0m"