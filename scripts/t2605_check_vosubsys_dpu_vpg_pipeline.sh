#!/bin/sh

# usage:
# ./check_vo_pipeline_smoke.sh on
# ./check_vo_pipeline_smoke.sh off

if [ $# -ne 1 ]; then
    echo "Usage: $0 {on|off}"
    exit 1
fi

CMD=$1

dpu_vpg()
{
    ######## config DPU ########

    # MASK DOU0 config valid irq
    devmem 0x170000a8 32 0x01

    # 0: INACTIVE 1: TBU_CONNECT 2: TBU_DISCONNECT
    # 3: DO0_ACTIVE 4: DO1_ACTIVE 5: DO01_ACTIVE
    devmem 0x170000d0 32 0x03

    ######### DOU0_BS ##########
    # BS_CONTROL
    # BIT[1] : video mode enable
    # BIT[0] : display backend timing enable
    # BIT[12] : TM
    # BIT[18] : CRC_ENBALE
    devmem 0x17001ed0 32 0x41003

    # BS_ACTIVESIZE
    # BIT[28:16] : VACTIVE
    # BIT[12:0] : HACTIVE
    devmem 0x17001ee0 32 0x7800438

    # BS_HINTERVALS
    # BIT[25:16] : HBACKPORCH 60
    # BIT[11:0] : HFRONTPORCH 16
    devmem 0x17001ee4 32 0x340030

    # BS_VINTERVALS
    # BIT[23:16] : VBACKPORCH 30
    # BIT[13:0] :  VFRONTPORCH 9
    devmem 0x17001ee8 32 0xF0010

    # BS_SYNC
    # BIT[28]                : VSP
    # BIT[23:16]        : VSYNCWIDTH 6
    # BIT[12]                : HSP
    # BIT[9:0]                : HSYNCWIDTH 62
    devmem 0x17001eec 32 0x10061008

    ######### DOU0_IPS ##########
    # INPUT_ID
    # BIT[15:0]                : INPUT_ID
    devmem 0x17001a80 32 0x200

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
    devmem 0x17001ad0 32 0x0

    # IPS_SIZE
    # BIT[28:16]                : VSIZE
    # BIT[12:0]                        : HSIZE
    devmem 0x17001ad4 32 0x7800438

    # config DOU_IRQ_MASK
    devmem 0x170018A8 32 0x6000

    # config DOU0_IPS_DEPTH
    devmem 0x17001AD8 32 0x8

    #GCU_CONFIG_VALID0
    devmem 0x170000d4 32 0x1
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

case "$CMD" in
    on)
        echo ">>> Running ON sequence..."

    # dsi_host_enable
    dpu_vpg

        ;;
    off)
        echo ">>> Running OFF sequence..."

    # dsi_host_disable

    # bs_control
    # disable test mode
    devmem 0x17001ed0 32 0x2

    # config valid
    devmem 0x170000d4 32 0x1

    # gcu control; idle
    # devmem 0x170000d0 32 0x0
        ;;
    *)
        echo "Invalid argument: $CMD"
        echo "Usage: $0 {on|off}"
        exit 1
        ;;
esac

echo ">>> Done."

