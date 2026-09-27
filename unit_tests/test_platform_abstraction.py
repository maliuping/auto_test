from pathlib import Path

import pytest

from framework.compiler import ShellCompiler
from framework.core.errors import AccessViolationError, FieldValueError
from framework.core.operations import OperationPlan, UpdateFields, WriteRegister
from framework.platform_db import PlatformLoader, RegisterResolver
from hal import DpuHal


PLATFORM_ROOT = Path(__file__).resolve().parents[1] / "platforms"


@pytest.fixture(scope="module")
def loader():
    return PlatformLoader(PLATFORM_ROOT)


@pytest.fixture(scope="module")
def legacy_target(loader):
    return loader.load_target("legacy_160")


def test_target_profiles_resolve_different_dpu_bases(loader):
    legacy = RegisterResolver(loader.load_target("legacy_160"))
    candidate = RegisterResolver(loader.load_target("candidate_170"))

    assert legacy.resolve("DPU.DOU0.BS_CONTROL") == 0x16001ED0
    assert candidate.resolve("DPU.DOU0.BS_CONTROL") == 0x17001ED0


def test_active_size_field_encoding(legacy_target):
    resolver = RegisterResolver(legacy_target)

    value = resolver.encode_fields(
        "DPU.DOU0.BS_ACTIVE_SIZE",
        {"hactive": 1080, "vactive": 1920},
        base_value=0,
    )

    assert value == 0x07800438


def test_field_value_out_of_range_fails_before_execution(legacy_target):
    resolver = RegisterResolver(legacy_target)

    with pytest.raises(FieldValueError, match="hactive"):
        resolver.encode_fields(
            "DPU.DOU0.BS_ACTIVE_SIZE",
            {"hactive": 8192},
            base_value=0,
        )


def test_vpg_register_core_generates_auditable_shell(legacy_target):
    plan = DpuHal().configure_vpg_register_core(width=1080, height=1920)

    artifact = ShellCompiler(legacy_target).compile(plan)

    assert "devmem 0x160000A8 32 0x00000001" in artifact.script
    assert "devmem 0x160000D0 32 0x00000003" in artifact.script
    assert "devmem 0x16001ED0 32 0x00041003" in artifact.script
    assert "devmem 0x16001EE0 32 0x07800438" in artifact.script
    assert "STEP_START vpg-core-001" in artifact.script
    assert artifact.manifest["verification_status"] == "unverified"
    assert len(artifact.manifest["operations"]) == 4


def test_runtime_update_fields_generates_read_modify_write(legacy_target):
    plan = OperationPlan(
        plan_id="update_crc",
        operations=(
            UpdateFields(
                operation_id="update-001",
                source="unit-test",
                register="DPU.DOU0.BS_CONTROL",
                fields={"crc_enable": 0},
            ),
        ),
    )

    artifact = ShellCompiler(legacy_target).compile(plan)

    assert 'old_value="$(devmem 0x16001ED0 32)"' in artifact.script
    assert "new_value=$(( (old_value & ~0x00040000) | 0x00000000 ))" in artifact.script
    assert 'devmem 0x16001ED0 32 "$new_value"' in artifact.script


def test_read_only_register_write_is_rejected(legacy_target):
    plan = OperationPlan(
        plan_id="invalid_write",
        operations=(
            WriteRegister(
                operation_id="invalid-001",
                source="unit-test",
                register="DPU.GCU.STATUS",
                value=1,
            ),
        ),
    )

    with pytest.raises(AccessViolationError, match="not writable"):
        ShellCompiler(legacy_target).compile(plan)


def test_duplicate_operation_ids_are_rejected():
    operation = WriteRegister(
        operation_id="duplicate",
        source="unit-test",
        register="DPU.GCU.CONTROL",
        value=0,
    )

    with pytest.raises(ValueError, match="unique"):
        OperationPlan(
            plan_id="duplicates",
            operations=(operation, operation),
        )
