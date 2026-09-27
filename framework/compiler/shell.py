import shlex

from framework.core.artifact import ShellArtifact
from framework.core.errors import CapabilityError, CompilationError, SchemaError
from framework.core.operations import UpdateFields, WriteFields, WriteRegister
from framework.platform_db.resolver import RegisterResolver


class ShellCompiler:
    def __init__(self, resolved_target):
        self.target = resolved_target
        self.resolver = RegisterResolver(resolved_target)

    def compile(self, plan):
        self._validate_capabilities(plan)
        lines = [
            "#!/bin/sh",
            "set -eu",
            "",
            "# target: {0}".format(self.target.target.name),
            "# verification_status: {0}".format(
                self.target.target.verification_status
            ),
            "# profile_hash: {0}".format(self.target.profile_hash),
            "# plan: {0}".format(plan.plan_id),
            "",
        ]
        manifest_operations = []

        for operation in plan.operations:
            shell_lines, manifest_operation = self._compile_operation(operation)
            lines.extend(shell_lines)
            lines.append("")
            manifest_operations.append(manifest_operation)

        manifest = {
            "schema_version": 1,
            "target": self.target.target.name,
            "soc": self.target.soc.name,
            "board": self.target.target.board,
            "runtime": self.target.runtime.name,
            "verification_status": self.target.target.verification_status,
            "profile_hash": self.target.profile_hash,
            "plan_id": plan.plan_id,
            "metadata": dict(plan.metadata),
            "operations": manifest_operations,
        }
        return ShellArtifact(
            plan_id=plan.plan_id,
            script="\n".join(lines).rstrip() + "\n",
            manifest=manifest,
        )

    def _compile_operation(self, operation):
        if isinstance(operation, WriteRegister):
            return self._compile_write_register(operation)
        if isinstance(operation, WriteFields):
            return self._compile_write_fields(operation)
        if isinstance(operation, UpdateFields):
            return self._compile_update_fields(operation)
        raise CompilationError(
            "unsupported operation type: {0}".format(type(operation).__name__)
        )

    def _compile_write_register(self, operation):
        register = self.resolver.validate_write(operation.register, operation.value)
        address = self.resolver.resolve(operation.register)
        value = operation.value
        command = self._write_command(register, address, value)
        lines = self._step_lines(operation, [command])
        return lines, self._manifest_operation(operation, register, address, value)

    def _compile_write_fields(self, operation):
        value = self.resolver.encode_fields(
            operation.register,
            operation.fields,
            operation.base_value,
        )
        register = self.resolver.definition(operation.register)
        address = self.resolver.resolve(operation.register)
        command = self._write_command(register, address, value)
        lines = self._step_lines(operation, [command])
        manifest = self._manifest_operation(operation, register, address, value)
        manifest["base_value"] = operation.base_value
        manifest["fields"] = dict(operation.fields)
        return lines, manifest

    def _compile_update_fields(self, operation):
        register = self.resolver.definition(operation.register)
        mask, encoded = self.resolver.update_mask_and_value(
            operation.register, operation.fields
        )
        address = self.resolver.resolve(operation.register)
        tool = self._register_tool(register)
        values = {
            "address": self._hex(address, max(8, register.width // 4)),
            "width": str(register.width),
        }
        read_command = self._render(tool.read, values)
        write_values = dict(values)
        write_values["value"] = '"$new_value"'
        write_command = self._render(tool.write, write_values, raw_keys={"value"})
        commands = [
            'old_value="$({0})"'.format(read_command),
            "new_value=$(( (old_value & ~{0}) | {1} ))".format(
                self._hex(mask, register.width // 4),
                self._hex(encoded, register.width // 4),
            ),
            write_command,
        ]
        lines = self._step_lines(operation, commands)
        manifest = self._manifest_operation(operation, register, address, None)
        manifest["mask"] = mask
        manifest["encoded_value"] = encoded
        manifest["fields"] = dict(operation.fields)
        return lines, manifest

    def _step_lines(self, operation, commands):
        return [
            "# op: {0} / {1}".format(operation.operation_id, operation.register),
            "# source: {0}".format(operation.source),
            "printf '%s\\n' {0}".format(
                shlex.quote("STEP_START {0}".format(operation.operation_id))
            ),
            *commands,
            "printf '%s\\n' {0}".format(
                shlex.quote("STEP_PASS {0}".format(operation.operation_id))
            ),
        ]

    def _write_command(self, register, address, value):
        tool = self._register_tool(register)
        values = {
            "address": self._hex(address, max(8, register.width // 4)),
            "width": str(register.width),
            "value": self._hex(value, register.width // 4),
        }
        return self._render(tool.write, values)

    def _register_tool(self, register):
        space = self.target.soc.address_spaces[register.space]
        try:
            return self.target.runtime.register_tools[space.access_tool]
        except KeyError as error:
            raise SchemaError(
                "runtime {0} does not define register tool {1}".format(
                    self.target.runtime.name, space.access_tool
                )
            ) from error

    def _render(self, template, values, raw_keys=None):
        raw_keys = raw_keys or set()
        rendered = []
        for token in template:
            if token.startswith("{") and token.endswith("}"):
                key = token[1:-1]
                if key in raw_keys:
                    rendered.append(values[key])
                    continue
            rendered.append(shlex.quote(token.format(**values)))
        return " ".join(rendered)

    def _validate_capabilities(self, plan):
        required = tuple(plan.metadata.get("required_capabilities", ()))
        available = set(self.target.target.capabilities)
        missing = [capability for capability in required if capability not in available]
        if missing:
            raise CapabilityError(
                "target {0} lacks capabilities: {1}".format(
                    self.target.target.name, ", ".join(missing)
                )
            )

    def _manifest_operation(self, operation, register, address, value):
        manifest = {
            "id": operation.operation_id,
            "type": type(operation).__name__,
            "source": operation.source,
            "register": operation.register,
            "address": address,
            "width": register.width,
        }
        if value is not None:
            manifest["value"] = value
        return manifest

    def _hex(self, value, digits):
        return "0x{0:0{1}X}".format(value, digits)
