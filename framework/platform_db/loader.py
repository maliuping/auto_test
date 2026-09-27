import hashlib
import json
import re
from pathlib import Path
from types import MappingProxyType

import yaml

from framework.core.errors import SchemaError, UnknownTargetError
from framework.platform_db.models import (
    AddressSpace,
    RegisterDefinition,
    RegisterField,
    RegisterTool,
    ResolvedTarget,
    RuntimeProfile,
    SocProfile,
    TargetProfile,
)


SCHEMA_VERSION = 1
VALID_ACCESS_TYPES = frozenset({"ro", "rw", "wo", "w1c", "w1s", "rc", "reserved"})
VALID_REGISTER_WIDTHS = frozenset({8, 16, 32, 64})
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise SchemaError("duplicate YAML key: {0}".format(key))
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _mapping(value, context):
    if not isinstance(value, dict):
        raise SchemaError("{0} must be a mapping".format(context))
    return value


def _string(value, context):
    if not isinstance(value, str) or not value:
        raise SchemaError("{0} must be a non-empty string".format(context))
    return value


def _integer(value, context):
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaError("{0} must be an integer".format(context))
    return value


def _immutable(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _immutable(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_immutable(item) for item in value)
    return value


class PlatformLoader:
    def __init__(self, root):
        self.root = Path(root)

    def load_target(self, target_name):
        self._validate_name(target_name, "target")
        target_data = self._load_document("targets", target_name, required=True)
        target = self._parse_target(target_data, target_name)
        soc_data = self._load_document("soc", target.soc, required=True)
        board_data = self._load_document("boards", target.board, required=True)
        runtime_data = self._load_document("runtimes", target.runtime, required=True)
        lab_data = self._load_document("labs", target.lab, required=True)

        soc = self._parse_soc(soc_data, target.soc)
        runtime = self._parse_runtime(runtime_data, target.runtime)
        self._validate_named_document(board_data, "board", target.board)
        self._validate_named_document(lab_data, "lab", target.lab)

        canonical = {
            "target": target_data,
            "soc": soc_data,
            "board": board_data,
            "runtime": runtime_data,
            "lab": lab_data,
        }
        profile_hash = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        return ResolvedTarget(
            target=target,
            soc=soc,
            board=_immutable(board_data),
            runtime=runtime,
            lab=_immutable(lab_data),
            profile_hash=profile_hash,
        )

    def _load_document(self, category, name, required):
        self._validate_name(name, category)
        path = self.root / category / "{0}.yaml".format(name)
        if not path.is_file():
            if required:
                if category == "targets":
                    raise UnknownTargetError("unknown target: {0}".format(name))
                raise SchemaError("missing platform document: {0}".format(path))
            return {}
        try:
            with path.open("r", encoding="utf-8") as stream:
                data = yaml.load(stream, Loader=UniqueKeyLoader)
        except SchemaError:
            raise
        except (OSError, yaml.YAMLError) as error:
            raise SchemaError("failed to load {0}: {1}".format(path, error)) from error
        data = _mapping(data, str(path))
        if data.get("schema_version") != SCHEMA_VERSION:
            raise SchemaError(
                "{0} requires schema_version={1}".format(path, SCHEMA_VERSION)
            )
        return data

    def _parse_target(self, data, expected_name):
        self._validate_named_document(data, "target", expected_name)
        capabilities = data.get("capabilities", [])
        if not isinstance(capabilities, list) or not all(
            isinstance(item, str) and item for item in capabilities
        ):
            raise SchemaError("target.capabilities must be a list of strings")
        return TargetProfile(
            name=expected_name,
            soc=_string(data.get("soc"), "target.soc"),
            board=_string(data.get("board"), "target.board"),
            runtime=_string(data.get("runtime"), "target.runtime"),
            lab=_string(data.get("lab"), "target.lab"),
            capabilities=tuple(capabilities),
            verification_status=_string(
                data.get("verification_status", "unverified"),
                "target.verification_status",
            ),
        )

    def _parse_soc(self, data, expected_name):
        self._validate_named_document(data, "soc", expected_name)
        address_spaces = {}
        for name, raw_space in _mapping(
            data.get("address_spaces"), "soc.address_spaces"
        ).items():
            raw_space = _mapping(raw_space, "address_space.{0}".format(name))
            base = _integer(raw_space.get("base"), "address_space.{0}.base".format(name))
            size = _integer(raw_space.get("size"), "address_space.{0}.size".format(name))
            if base < 0 or size <= 0:
                raise SchemaError("address_space.{0} has invalid base or size".format(name))
            address_spaces[name] = AddressSpace(
                name=name,
                base=base,
                size=size,
                access_tool=_string(
                    raw_space.get("access_tool"),
                    "address_space.{0}.access_tool".format(name),
                ),
            )

        registers = {}
        for name, raw_register in _mapping(data.get("registers"), "soc.registers").items():
            registers[name] = self._parse_register(name, raw_register, address_spaces)

        return SocProfile(
            name=expected_name,
            address_spaces=MappingProxyType(address_spaces),
            registers=MappingProxyType(registers),
        )

    def _parse_register(self, name, raw_register, address_spaces):
        raw_register = _mapping(raw_register, "register.{0}".format(name))
        space_name = _string(raw_register.get("space"), "register.{0}.space".format(name))
        if space_name not in address_spaces:
            raise SchemaError("register {0} references unknown space {1}".format(name, space_name))
        offset = _integer(raw_register.get("offset"), "register.{0}.offset".format(name))
        width = _integer(raw_register.get("width"), "register.{0}.width".format(name))
        access = _string(raw_register.get("access"), "register.{0}.access".format(name))
        if width not in VALID_REGISTER_WIDTHS:
            raise SchemaError("register {0} has unsupported width {1}".format(name, width))
        if access not in VALID_ACCESS_TYPES:
            raise SchemaError("register {0} has unsupported access {1}".format(name, access))
        if offset < 0 or offset % (width // 8):
            raise SchemaError("register {0} offset is not aligned".format(name))
        space = address_spaces[space_name]
        if offset + (width // 8) > space.size:
            raise SchemaError("register {0} is outside address space {1}".format(name, space_name))

        reset = raw_register.get("reset")
        if reset is not None:
            reset = _integer(reset, "register.{0}.reset".format(name))
            if reset < 0 or reset >= (1 << width):
                raise SchemaError("register {0} reset value exceeds width".format(name))

        fields = {}
        occupied_mask = 0
        for field_name, raw_field in _mapping(
            raw_register.get("fields", {}), "register.{0}.fields".format(name)
        ).items():
            raw_field = _mapping(raw_field, "register.{0}.{1}".format(name, field_name))
            lsb = _integer(raw_field.get("lsb"), "field.{0}.{1}.lsb".format(name, field_name))
            field_width = _integer(
                raw_field.get("width"), "field.{0}.{1}.width".format(name, field_name)
            )
            if lsb < 0 or field_width <= 0 or lsb + field_width > width:
                raise SchemaError("field {0}.{1} exceeds register width".format(name, field_name))
            field = RegisterField(name=field_name, lsb=lsb, width=field_width)
            if field.mask & occupied_mask:
                raise SchemaError("field {0}.{1} overlaps another field".format(name, field_name))
            occupied_mask |= field.mask
            fields[field_name] = field

        return RegisterDefinition(
            name=name,
            space=space_name,
            offset=offset,
            width=width,
            access=access,
            reset=reset,
            fields=MappingProxyType(fields),
        )

    def _parse_runtime(self, data, expected_name):
        self._validate_named_document(data, "runtime", expected_name)
        tools_data = _mapping(data.get("tools"), "runtime.tools")
        register_tools = {}
        for name, raw_tool in tools_data.items():
            raw_tool = _mapping(raw_tool, "runtime.tools.{0}".format(name))
            read = self._command_template(raw_tool.get("read"), "runtime.tools.{0}.read".format(name))
            write = self._command_template(raw_tool.get("write"), "runtime.tools.{0}.write".format(name))
            if not {"{address}", "{width}"}.issubset(set(read)):
                raise SchemaError("register read template must include {address} and {width}")
            if not {"{address}", "{width}", "{value}"}.issubset(set(write)):
                raise SchemaError(
                    "register write template must include {address}, {width}, and {value}"
                )
            register_tools[name] = RegisterTool(read=read, write=write)
        return RuntimeProfile(
            name=expected_name,
            register_tools=MappingProxyType(register_tools),
            paths=_immutable(_mapping(data.get("paths", {}), "runtime.paths")),
            modules=_immutable(_mapping(data.get("modules", {}), "runtime.modules")),
            nodes=_immutable(_mapping(data.get("nodes", {}), "runtime.nodes")),
            programs=_immutable(_mapping(data.get("programs", {}), "runtime.programs")),
        )

    def _command_template(self, value, context):
        if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
            raise SchemaError("{0} must be a non-empty list of strings".format(context))
        return tuple(value)

    def _validate_named_document(self, data, key, expected_name):
        actual_name = _string(data.get(key), key)
        if actual_name != expected_name:
            raise SchemaError(
                "{0} name mismatch: expected {1}, got {2}".format(key, expected_name, actual_name)
            )

    def _validate_name(self, name, context):
        if not isinstance(name, str) or not SAFE_NAME.fullmatch(name):
            raise SchemaError("invalid {0} name: {1!r}".format(context, name))
