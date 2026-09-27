from framework.core.operations import OperationPlan, WriteFields


class DpuHal:
    def configure_vpg_register_core(
        self,
        width,
        height,
        video_mode=True,
        timing_enable=True,
        test_mode=True,
        crc_enable=True,
    ):
        return OperationPlan(
            plan_id="dpu_vpg_register_core",
            operations=(
                WriteFields(
                    operation_id="vpg-core-001",
                    source="dpu.configure_vpg_register_core",
                    register="DPU.GCU.IRQ_MASK",
                    base_value=0,
                    fields={"dou0_config_valid_mask": 1},
                ),
                WriteFields(
                    operation_id="vpg-core-002",
                    source="dpu.configure_vpg_register_core",
                    register="DPU.GCU.CONTROL",
                    base_value=0,
                    fields={"state": 3},
                ),
                WriteFields(
                    operation_id="vpg-core-003",
                    source="dpu.configure_vpg_register_core",
                    register="DPU.DOU0.BS_CONTROL",
                    base_value=0,
                    fields={
                        "timing_enable": int(timing_enable),
                        "video_mode": int(video_mode),
                        "test_mode": int(test_mode),
                        "crc_enable": int(crc_enable),
                    },
                ),
                WriteFields(
                    operation_id="vpg-core-004",
                    source="dpu.configure_vpg_register_core",
                    register="DPU.DOU0.BS_ACTIVE_SIZE",
                    base_value=0,
                    fields={"hactive": width, "vactive": height},
                ),
            ),
            metadata={
                "scope": "register-core-only",
                "required_capabilities": ("dpu.vpg_core",),
            },
        )
