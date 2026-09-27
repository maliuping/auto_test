class PlatformAbstractionError(Exception):
    code = "platform.unknown"

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class SchemaError(PlatformAbstractionError):
    code = "config.schema_invalid"


class UnknownTargetError(PlatformAbstractionError):
    code = "config.target_unknown"


class UnknownRegisterError(PlatformAbstractionError):
    code = "register.unknown"


class UnknownFieldError(PlatformAbstractionError):
    code = "register.field_unknown"


class FieldValueError(PlatformAbstractionError):
    code = "register.value_out_of_range"


class AccessViolationError(PlatformAbstractionError):
    code = "register.access_violation"


class AddressRangeError(PlatformAbstractionError):
    code = "register.address_out_of_range"


class CapabilityError(PlatformAbstractionError):
    code = "platform.capability_missing"


class CompilationError(PlatformAbstractionError):
    code = "compiler.unsupported_operation"
