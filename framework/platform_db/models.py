from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple


@dataclass(frozen=True)
class AddressSpace:
    name: str
    base: int
    size: int
    access_tool: str


@dataclass(frozen=True)
class RegisterField:
    name: str
    lsb: int
    width: int

    @property
    def mask(self):
        return ((1 << self.width) - 1) << self.lsb


@dataclass(frozen=True)
class RegisterDefinition:
    name: str
    space: str
    offset: int
    width: int
    access: str
    reset: Optional[int]
    fields: Mapping[str, RegisterField]


@dataclass(frozen=True)
class SocProfile:
    name: str
    address_spaces: Mapping[str, AddressSpace]
    registers: Mapping[str, RegisterDefinition]


@dataclass(frozen=True)
class RegisterTool:
    read: Tuple[str, ...]
    write: Tuple[str, ...]


@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    register_tools: Mapping[str, RegisterTool]
    paths: Mapping[str, Any]
    modules: Mapping[str, Any]
    nodes: Mapping[str, str]
    programs: Mapping[str, Any]


@dataclass(frozen=True)
class TargetProfile:
    name: str
    soc: str
    board: str
    runtime: str
    lab: str
    capabilities: Tuple[str, ...]
    verification_status: str


@dataclass(frozen=True)
class ResolvedTarget:
    target: TargetProfile
    soc: SocProfile
    board: Mapping[str, Any]
    runtime: RuntimeProfile
    lab: Mapping[str, Any]
    profile_hash: str
