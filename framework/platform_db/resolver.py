from framework.core.errors import (
    AccessViolationError,
    AddressRangeError,
    FieldValueError,
    UnknownFieldError,
    UnknownRegisterError,
)


class RegisterResolver:
    def __init__(self, resolved_target):
        self.target = resolved_target

    def definition(self, register_name):
        try:
            return self.target.soc.registers[register_name]
        except KeyError as error:
            raise UnknownRegisterError(
                "unknown register {0} for target {1}".format(
                    register_name, self.target.target.name
                )
            ) from error

    def resolve(self, register_name):
        register = self.definition(register_name)
        space = self.target.soc.address_spaces[register.space]
        address = space.base + register.offset
        if address < space.base or address + (register.width // 8) > space.base + space.size:
            raise AddressRangeError(
                "register {0} resolves outside address space {1}".format(
                    register_name, register.space
                )
            )
        return address

    def validate_write(self, register_name, value):
        register = self.definition(register_name)
        if register.access in {"ro", "rc", "reserved"}:
            raise AccessViolationError(
                "register {0} with access {1} is not writable".format(
                    register_name, register.access
                )
            )
        if isinstance(value, bool) or not isinstance(value, int):
            raise FieldValueError("register value must be an integer")
        if value < 0 or value >= (1 << register.width):
            raise FieldValueError(
                "value {0} exceeds {1}-bit register {2}".format(
                    value, register.width, register_name
                )
            )
        return register

    def encode_fields(self, register_name, fields, base_value):
        register = self.validate_write(register_name, base_value)
        value = base_value
        for field_name, field_value in fields.items():
            field = self._field(register, field_name)
            self._validate_field_value(register_name, field, field_value)
            value = (value & ~field.mask) | (field_value << field.lsb)
        self.validate_write(register_name, value)
        return value

    def update_mask_and_value(self, register_name, fields):
        register = self.definition(register_name)
        if register.access != "rw":
            raise AccessViolationError(
                "runtime RMW requires rw access, got {0} for {1}".format(
                    register.access, register_name
                )
            )
        mask = 0
        encoded = 0
        for field_name, field_value in fields.items():
            field = self._field(register, field_name)
            self._validate_field_value(register_name, field, field_value)
            mask |= field.mask
            encoded |= field_value << field.lsb
        return mask, encoded

    def _field(self, register, field_name):
        try:
            return register.fields[field_name]
        except KeyError as error:
            raise UnknownFieldError(
                "unknown field {0}.{1}".format(register.name, field_name)
            ) from error

    def _validate_field_value(self, register_name, field, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise FieldValueError(
                "field {0}.{1} value must be an integer".format(register_name, field.name)
            )
        if value < 0 or value >= (1 << field.width):
            raise FieldValueError(
                "field {0}.{1} value {2} exceeds width {3}".format(
                    register_name, field.name, value, field.width
                )
            )
