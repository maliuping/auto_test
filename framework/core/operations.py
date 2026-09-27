from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple, Union


def _immutable_mapping(value):
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class WriteRegister:
    operation_id: str
    source: str
    register: str
    value: int


@dataclass(frozen=True)
class WriteFields:
    operation_id: str
    source: str
    register: str
    base_value: int
    fields: Mapping[str, int]

    def __post_init__(self):
        object.__setattr__(self, "fields", _immutable_mapping(self.fields))


@dataclass(frozen=True)
class UpdateFields:
    operation_id: str
    source: str
    register: str
    fields: Mapping[str, int]

    def __post_init__(self):
        object.__setattr__(self, "fields", _immutable_mapping(self.fields))


RegisterOperation = Union[WriteRegister, WriteFields, UpdateFields]


@dataclass(frozen=True)
class OperationPlan:
    plan_id: str
    operations: Tuple[RegisterOperation, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        operations = tuple(self.operations)
        operation_ids = [operation.operation_id for operation in operations]
        if not self.plan_id:
            raise ValueError("plan_id must not be empty")
        if len(operation_ids) != len(set(operation_ids)):
            raise ValueError("operation_id values must be unique within a plan")
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "metadata", _immutable_mapping(self.metadata))
