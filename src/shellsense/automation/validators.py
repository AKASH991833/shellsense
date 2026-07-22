from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from typing import Any

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def merge(self, other: ValidationResult) -> None:
        self.valid = self.valid and other.valid
        self.warnings.extend(other.warnings)
        self.errors.extend(other.errors)
        self.suggestions.extend(other.suggestions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "warnings": self.warnings,
            "errors": self.errors,
            "suggestions": self.suggestions,
        }


class BashValidator:
    def validate(self, content: str) -> ValidationResult:
        result = ValidationResult()
        lines = content.split("\n")

        has_shebang = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if i == 1 and stripped.startswith("#!"):
                has_shebang = True
            if stripped.startswith("#"):
                continue
            if not stripped:
                continue
            if re.search(r"\$\{?\w*\}?\s*/\s*$", stripped) and "rm " in stripped:
                result.warnings.append(
                    f"Line {i}: Possible dangerous rm with empty variable"
                )
            if re.search(r"\brm\s+-rf\s+(/\s*|\$\{?\w*\}?\s*/\s*)$", stripped):
                result.errors.append(f"Line {i}: Dangerous rm -rf command detected")
            if re.search(r"\bdd\s+if=.*\s+of=/dev/sd", stripped):
                result.errors.append(f"Line {i}: Dangerous dd disk write detected")
            if ":(){" in stripped or ":)|" in stripped:
                result.errors.append(f"Line {i}: Fork bomb detected")
            if re.search(r"\bcurl\s+.*\|\s*bash\b", stripped):
                result.warnings.append(f"Line {i}: Piped curl to bash")
            if re.search(r"\bwget\s+.*-O\s*-\s*\|\s*bash\b", stripped):
                result.warnings.append(f"Line {i}: Piped wget to bash")
            if "`" in stripped and "$(" in stripped:
                result.suggestions.append(
                    f"Line {i}: Mixing backticks with $() - use $() consistently"
                )
            if re.search(r"\$\[.*\]", stripped):
                result.suggestions.append(
                    f"Line {i}: Use $(( )) instead of deprecated $[]"
                )

        if not has_shebang:
            result.warnings.append("No shebang (#!) line found")

        has_set_e = any("set -e" in l or "set -o errexit" in l for l in lines)
        if not has_set_e:
            result.suggestions.append("Consider adding 'set -e' for error handling")

        try:
            r = subprocess.run(
                ["bash", "-n", "/dev/stdin"],
                input=content,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode != 0:
                result.valid = False
                result.errors.append(f"Bash syntax error: {r.stderr.strip()}")
        except FileNotFoundError:
            result.warnings.append("bash not found for syntax validation")
        except Exception as e:
            result.warnings.append(f"Syntax validation skipped: {e}")

        return result


class PythonValidator:
    def validate(self, content: str) -> ValidationResult:
        result = ValidationResult()
        try:
            compile(content, "<string>", "exec")
        except SyntaxError as e:
            result.valid = False
            result.errors.append(f"Python syntax error: {e}")
        return result


class SystemdValidator:
    def validate(self, content: str) -> ValidationResult:
        result = ValidationResult()
        lines = content.split("\n")
        sections: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("["):
                sections.append(stripped)
        required_sections = {"[Unit]", "[Service]", "[Install]"}
        found_sections = set(sections)
        missing = required_sections - found_sections
        if missing:
            missing_str = ", ".join(sorted(missing))
            if "[Service]" in missing_str:
                result.valid = False
                result.errors.append(f"Missing required sections: {missing_str}")
            else:
                result.warnings.append(f"Missing optional sections: {missing_str}")

        exec_start_found = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith(";"):
                continue
            if stripped.upper().startswith("EXECSTART") or stripped.startswith(
                "ExecStart"
            ):
                exec_start_found = True
                if not stripped.split("=", 1)[1].strip():
                    result.valid = False
                    result.errors.append("ExecStart has empty value")
                break
        if not exec_start_found and "[Service]" in found_sections:
            result.valid = False
            result.errors.append("Missing ExecStart directive in [Service] section")

        for line in lines:
            stripped = line.strip()
            if "=" in stripped:
                key, val = stripped.split("=", 1)
                if not val.strip() and not stripped.startswith("#"):
                    result.warnings.append(f"Empty value for {key}")
        return result


class DockerfileValidator:
    def validate(self, content: str) -> ValidationResult:
        result = ValidationResult()
        lines = content.split("\n")
        has_from = False
        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith("FROM"):
                has_from = True
                break
        if not has_from:
            result.valid = False
            result.errors.append("Dockerfile must have a FROM instruction")

        for line in lines:
            stripped = line.strip()
            if (
                stripped.upper().startswith("ADD")
                and not stripped.upper().startswith("ADD ")
                and stripped != stripped
            ):
                pass
            if "ADD" in stripped.upper() and "https://" in stripped:
                result.warnings.append("Prefer COPY over ADD for local files")
                break

        has_expose = any(l.strip().upper().startswith("EXPOSE") for l in lines)
        has_cmd = any(l.strip().upper().startswith("CMD") for l in lines) or any(
            l.strip().upper().startswith("ENTRYPOINT") for l in lines
        )

        if not has_expose:
            result.warnings.append("No EXPOSE instruction found")
        if not has_cmd:
            result.warnings.append("No CMD or ENTRYPOINT instruction found")

        return result


class ComposeValidator:
    def validate(self, content: str) -> ValidationResult:
        result = ValidationResult()
        if "services:" not in content:
            result.valid = False
            result.errors.append("Docker Compose file must have a 'services:' section")
        if "version:" not in content:
            result.warnings.append("No version specified")
        return result


class CronValidator:
    CRON_REGEX = re.compile(
        r"^(\*|([0-5]?\d)(-([0-5]?\d))?(/([0-9]+))?)\s+"
        r"(\*|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?(/([0-9]+))?)\s+"
        r"(\*|([01]?\d|2[0-9]|3[01])(-([01]?\d|2[0-9]|3[01]))?(/([0-9]+))?)\s+"
        r"(\*|([1-9]|1[0-2])(-([1-9]|1[0-2]))?(/([0-9]+))?)\s+"
        r"(\*|([0-6])(-([0-6]))?(/([0-9]+))?)\s+"
        r".+$"
    )

    SPECIAL_STRINGS = {
        "@reboot",
        "@hourly",
        "@daily",
        "@weekly",
        "@monthly",
        "@yearly",
        "@annually",
        "@midnight",
    }

    def validate(self, content: str) -> ValidationResult:
        result = ValidationResult()
        for line in content.strip().split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if parts[0] in self.SPECIAL_STRINGS:
                continue
            if len(parts) < 6:
                result.valid = False
                result.errors.append(
                    f"Invalid cron expression: '{stripped}' - need at least 5 time fields + command"
                )
                continue
            time_fields = " ".join(parts[:5])
            if not self.CRON_REGEX.match(stripped):
                if not any(f == "*" for f in parts[:5]):
                    result.warnings.append(
                        f"Cron expression may be invalid: '{stripped}'"
                    )
            command = " ".join(parts[5:])
            if not command:
                result.valid = False
                result.errors.append(f"No command in cron entry: '{stripped}'")
        if not result.errors:
            result.valid = True
        return result


class NginxValidator:
    def validate(self, content: str) -> ValidationResult:
        result = ValidationResult()
        if "server {" not in content and "http {" not in content:
            result.valid = False
            result.errors.append("Nginx config must have a server or http block")
        braces = 0
        for line in content.split("\n"):
            stripped = line.strip()
            if "{" in stripped and not stripped.startswith("#"):
                braces += stripped.count("{")
            if "}" in stripped and not stripped.startswith("#"):
                braces -= stripped.count("}")
        if braces != 0:
            result.valid = False
            result.errors.append(f"Unbalanced braces (count: {braces})")
        if "server_name" not in content:
            result.warnings.append("No server_name directive found")
        if "listen" not in content:
            result.warnings.append("No listen directive found")
        try:
            r = subprocess.run(
                ["nginx", "-t"], capture_output=True, text=True, timeout=10
            )
            if r.returncode != 0:
                result.warnings.append(f"nginx -t: {r.stderr.strip()}")
        except FileNotFoundError:
            pass
        except Exception as e:
            result.warnings.append(f"Nginx validation skipped: {e}")
        return result


class ApacheValidator:
    def validate(self, content: str) -> ValidationResult:
        result = ValidationResult()
        if "<VirtualHost" not in content:
            result.valid = False
            result.errors.append("Apache config must have a VirtualHost block")
        braces = 0
        for line in content.split("\n"):
            stripped = line.strip()
            if "<" in stripped and not stripped.startswith("#"):
                braces += stripped.count("<")
            if ">" in stripped and not stripped.startswith("#"):
                pass
            if "</" in stripped:
                braces -= 1
        try:
            r = subprocess.run(
                ["apachectl", "-t"], capture_output=True, text=True, timeout=10
            )
            if r.returncode != 0:
                result.warnings.append(f"apachectl -t: {r.stderr.strip()}")
        except FileNotFoundError:
            pass
        except Exception as e:
            result.warnings.append(f"Apache validation skipped: {e}")
        return result


class YAMLValidator:
    def validate(self, content: str) -> ValidationResult:
        result = ValidationResult()
        try:
            import yaml

            yaml.safe_load(content)
        except ImportError:
            try:
                import json

                try:
                    yaml_data = json.dumps({"data": content})
                except Exception:
                    pass
            except Exception:
                result.warnings.append("PyYAML not installed - basic validation only")
        except Exception as e:
            result.errors.append(f"YAML parse error: {e}")
            result.valid = False
        lines = content.strip().split("\n")
        for i, line in enumerate(lines, 1):
            if "\t" in line:
                result.warnings.append(
                    f"Line {i}: Tab character found - use spaces for indentation"
                )
                result.valid = False
        return result


def validate_content(content: str, file_type: str) -> ValidationResult:
    validators = {
        "sh": BashValidator(),
        "bash": BashValidator(),
        "py": PythonValidator(),
        "python": PythonValidator(),
        "service": SystemdValidator(),
        "timer": SystemdValidator(),
        "Dockerfile": DockerfileValidator(),
        "compose.yaml": ComposeValidator(),
        "yaml": YAMLValidator(),
        "yml": YAMLValidator(),
        "conf": NginxValidator(),
        "cron": CronValidator(),
    }
    validator = validators.get(file_type)
    if validator is None:
        return ValidationResult(
            warnings=[f"No validator available for type: {file_type}"]
        )
    return validator.validate(content)
