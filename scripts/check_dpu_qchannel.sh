#!/bin/sh

cur=$(cd `dirname $0`; pwd)
cd $cur

#----------------------------------------
# Function: Read register value
#----------------------------------------
read_reg() {
    val=$(devmem $1)
        printf "0x%X\n" "$val"
    #echo $val
}


dpu_vpg()
{
    ######## config DPU ########

    # MASK DOU0 config valid irq
    devmem 0x160000a8 32 0x01

    # 0: INACTIVE 1: TBU_CONNECT 2: TBU_DISCONNECT
    # 3: DO0_ACTIVE 4: DO1_ACTIVE 5: DO01_ACTIVE
    devmem 0x160000d0 32 0x03

    ######### DOU0_BS ##########
    # BS_CONTROL
    # BIT[1] : video mode enable
    # BIT[0] : display backend timing enable
    # BIT[12] : TM
    # BIT[18] : CRC_ENBALE
    devmem 0x16001ed0 32 0x41003

    # BS_ACTIVESIZE
    # BIT[28:16] : VACTIVE
    # BIT[12:0] : HACTIVE
    devmem 0x16001ee0 32 0x7800438

    # BS_HINTERVALS
    # BIT[25:16] : HBACKPORCH 60
    # BIT[11:0] : HFRONTPORCH 16
    devmem 0x16001ee4 32 0x340030

    # BS_VINTERVALS
    # BIT[23:16] : VBACKPORCH 30
    # BIT[13:0] :  VFRONTPORCH 9
    devmem 0x16001ee8 32 0xF0010

    # BS_SYNC
    # BIT[28]                : VSP
    # BIT[23:16]        : VSYNCWIDTH 6
    # BIT[12]                : HSP
    # BIT[9:0]                : HSYNCWIDTH 62
    devmem 0x16001eec 32 0x10061008

    ######### DOU0_IPS ##########
    # INPUT_ID
    # BIT[15:0]                : INPUT_ID
    devmem 0x16001a80 32 0x200

    ######### IPS_CONTROL ##########
    # INPUT_CONTROL
    # BIT[18]                : IM(image merge processing enable)
    # BIT[17]                : SBS(side-by-side display processing enable)
    # BIT[16]                : CLAMP(clamping enable)
    # BIT[12]                : DITH(dithering enable)
    # BIT[11]                : LPF(Chrominance low-pass filter enable)
    # BIT[10]                : CHD420(422->420)
    # BIT[9]                : CHD422(444->422)
    # BIT[8]                : YUV(RGB->YUV)
    # BIT[4]                : FT(Forward transform(gamma) enable)
    # BIT[1]                : IT(Inverse transform enable)
    # BIT[0]                : RGB(RGB->RGB)
    devmem 0x16001ad0 32 0x0

    # IPS_SIZE
    # BIT[28:16]                : VSIZE
    # BIT[12:0]                        : HSIZE
    devmem 0x16001ad4 32 0x7800438

    # config DOU_IRQ_MASK
    devmem 0x160018A8 32 0x6000

    # config DOU0_IPS_DEPTH
    devmem 0x16001AD8 32 0x8

    #GCU_CONFIG_VALID0
    devmem 0x160000d4 32 0x1
    echo "=== DPU VPG Config Sucess ==="
}

dsi_host_disable()
{
    echo 0 > /sys/kernel/debug/dsi-tx0/prepare
    echo 0 > /sys/kernel/debug/panel_tx0/prepare
    echo 0 > /sys/kernel/debug/panel_tx0/enable
    echo 0 > /sys/kernel/debug/dsi-tx0/enable

    echo "=== DSI Host Disable Sucess ==="
}

dsi_host_enable()
{
    echo "600000 2 rgb888 0 0 burst" > /sys/kernel/debug/dsi-tx0/config
    echo timing "30000 1080 48 8 52 1920 16 6 15" > /sys/kernel/debug/dsi-tx0/mode
    echo 1 > /sys/kernel/debug/dsi-tx0/prepare
    echo 1 > /sys/kernel/debug/panel_tx0/prepare
    echo 1 > /sys/kernel/debug/panel_tx0/enable
    echo 1 > /sys/kernel/debug/dsi-tx0/enable

    echo "=== DSI Host Enable Sucess ==="
}


dpu_power_off()
{
    echo "=== DPU Power Off Start ==="
    # devmem 0x2023014 32 0x04168990
    #
    # devmem 0x2023210 32 0x40004
	#
	atool pmctrl -d 0

    result=$(read_reg 0x2023228)
    if [ $((result & 0xFF)) -eq $((0x30)) ]; then
            echo "read 0x2023228 pass"
    else
            echo "read 0x2023228 fail, not 0x30"
            exit 1
    fi

    devmem 0x202305c 32 0x800000
    devmem 0x2023040 32 0x800000
    devmem 0x2023064 32 0x800000
    devmem 0x2023034 32 0x800000

    echo "=== DPU Power Off Sucess ==="
}

dpu_power_on()
{
    echo "=== DPU Power On Start ==="
    # devmem 0x2023030 32 0x800000
    # devmem 0x2023058 32 0x800000
    #
    # sleep 1
    # devmem 0x202305c 32 0x800000
    # devmem 0x2023068 32 0x800000
    # devmem 0x2023050 32 0x800000
    # devmem 0x2023058 32 0x800000
    # devmem 0x2023210 32 0x40004

	atool pmctrl -u 0
	result=$(read_reg 0x2023228)
	if [ $((result & 0xFF)) -eq $((0x00)) ]; then
		echo "read 0x2023228 pass"
	else
		echo "read 0x2023228 fail, not 0x00"
		exit 1
	fi

	echo "=== DPU Power On Sucess ==="
}

set_dpu_inactive()
{
    # config dou0 not output data
    devmem 0x16001ed0 32 0x00040002

    # config dou valid
    devmem 0x160000d4 32 0x1

    # config dpu inactive
    devmem 0x160000d0 32 0x0

    echo "=== Set DPU Inactive ==="
}


start_idx=0
end_idx=2

if [ x$1 != x'' ]; then
    start_idx=$1
fi

if [ x$2 != x'' ]; then
    end_idx=$2
fi

let num=$end_idx+1

frame_id=$start_idx
while [ $frame_id -lt $num ]; do
    echo "=== frame $frame_id: DPU Low Power Test Start ==="
        dpu_pwr_hs=0x2023118
        val=`atool devmem $dpu_pwr_hs`
        echo "init dpu_pwr_hs: $val"

        # config dou0 not output data
        # config dou valid
        # config dpu inactive
        set_dpu_inactive

        # disable dsi host
        dsi_host_disable

        # read pmctrl dpu status
        val=`atool devmem $dpu_pwr_hs`
        echo "after set dpu noactive dpu_pwr_hs: $val"

        # request dpu powerdown
        atool devmem $dpu_pwr_hs 32 0x0

        expect=0x00000000
        real=`atool devmem $dpu_pwr_hs`
        if [ x"$real" != x"$expect" ]; then
                echo "dpu lp handshake failed"
                echo "Expect: $expect"
                echo "Actually: $real"
                exit 1
        else
                echo "dpu lp handshake success"
                echo "Prepare vo powerdown..."
                # Close vo powerdomian
                # atool pmctrl -d 0
                #echo off > /sys/devices/platform/pmctrl-pd-vo/pmctrl_pd
                dpu_power_off
        fi

        for i in $(seq 3 -1 1); do
                echo "Count down: $i s"
                sleep 1
        done

        echo "Prepare vo powerup..."
        # Open vo powerdomian
        # atool pmctrl -u 0
        # echo on > /sys/devices/platform/pmctrl-pd-vo/pmctrl_pd
        dpu_power_on

        # request dpu powerdown
        atool devmem $dpu_pwr_hs 32 0x1
        expect=0x00000101
        real=`atool devmem $dpu_pwr_hs`
        if [ x"$real" != x"$expect" ]; then
                echo "dpu poweron handshake failed"
                echo "Expect: $expect"
                echo "Actually: $real"
                exit 1
        else
                echo "dpu poweron handshake success"
                devmem 0x160000d0
        fi

        # sh dpu_vpg.sh
        dsi_host_enable
        dpu_vpg
        frame_id=$((frame_id + 1))

        for i in $(seq 5 -1 1); do
                echo " Ouput count down: $i"
                sleep 1
        done
done

set_dpu_inactive
echo -e "\033[32m[FINAL PASS] Dpu Low power Test PASS.\033[0m"
