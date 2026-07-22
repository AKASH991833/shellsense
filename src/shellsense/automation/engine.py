from __future__ import annotations

from typing import Any

from shellsense.ai.core import AIEngine
from shellsense.automation.exporters import AutomationExporter
from shellsense.automation.generators.bash import BashGenerator, GeneratedOutput
from shellsense.automation.generators.cron import CronGenerator
from shellsense.automation.generators.docker import DockerGenerator
from shellsense.automation.generators.infrastructure import InfrastructureGenerator
from shellsense.automation.generators.python_script import PythonGenerator
from shellsense.automation.generators.ssh import SSHGenerator
from shellsense.automation.generators.systemd import SystemdGenerator
from shellsense.automation.generators.webserver import WebServerGenerator
from shellsense.automation.interactive import InteractiveGenerator
from shellsense.automation.prompts import (
    get_automation_system_prompt,
    get_generation_prompt,
)
from shellsense.automation.templates import TemplateLibrary
from shellsense.automation.validators import ValidationResult, validate_content
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class AutomationEngine:
    def __init__(self, ai: AIEngine | None = None) -> None:
        self._ai = ai
        self.templates = TemplateLibrary()
        self.bash = BashGenerator(self.templates)
        self.python_gen = PythonGenerator(self.templates)
        self.systemd = SystemdGenerator(self.templates)
        self.cron = CronGenerator(self.templates)
        self.docker = DockerGenerator(self.templates)
        self.webserver = WebServerGenerator(self.templates)
        self.ssh = SSHGenerator(self.templates)
        self.infrastructure = InfrastructureGenerator(self.templates)
        self.exporter = AutomationExporter()
        self.interactive = InteractiveGenerator(self)

    def generate(self, template_type: str, **kwargs: Any) -> GeneratedOutput:
        generator_map: dict[str, Any] = {
            "backup": self.bash.generate_backup_script,
            "log-rotation": self.bash.generate_log_rotation,
            "disk-cleanup": self.bash.generate_disk_cleanup,
            "package-update": self.bash.generate_package_update,
            "health-check": self.bash.generate_health_check,
            "user-management": self.bash.generate_user_management,
            "network-diagnostics": self.bash.generate_network_diagnostics,
            "service-management": self.bash.generate_service_management,
            "file-operations": self.bash.generate_file_operations,
            "monitoring": self.bash.generate_monitoring,
            "python-script": self.python_gen.generate_script,
            "sysadmin": self.python_gen.generate_sysadmin,
            "log-parser": self.python_gen.generate_log_parser,
            "systemd-service": self.systemd.generate_service,
            "systemd-timer": self.systemd.generate_timer,
            "systemd-socket": self.systemd.generate_socket,
            "systemd-target": self.systemd.generate_target,
            "cron-job": self.cron.generate_job,
            "dockerfile": self.docker.generate_dockerfile,
            "docker-compose": self.docker.generate_compose,
            "nginx-reverse-proxy": self.webserver.generate_nginx_reverse_proxy,
            "nginx-static": self.webserver.generate_nginx_static,
            "nginx-load-balancer": self.webserver.generate_nginx_load_balancer,
            "apache-vhost": self.webserver.generate_apache_vhost,
            "ssh-client": self.ssh.generate_client_config,
            "ssh-server": self.ssh.generate_server_config,
            "ssh-key-guidance": self.ssh.generate_key_guidance,
            "ansible": self.infrastructure.generate_ansible_playbook,
            "terraform": self.infrastructure.generate_terraform,
            "kubernetes": self.infrastructure.generate_kubernetes,
            "podman": self.infrastructure.generate_podman,
        }
        gen = generator_map.get(template_type)
        if gen is None:
            return self.bash.generate_custom(
                template_type, kwargs.get("description", ""), kwargs.get("content", "")
            )
        return gen(**{k: v for k, v in kwargs.items() if k in gen.__code__.co_varnames})

    def generate_with_ai(
        self, template_type: str, requirement: str, provider: str | None = None
    ) -> GeneratedOutput:
        if self._ai is None or not self._ai.is_ready:
            return self.generate(template_type, description=requirement)

        system_prompt = get_automation_system_prompt()
        user_prompt = get_generation_prompt(template_type, requirement)
        try:
            response = self._ai.generate(
                prompt=user_prompt, system_prompt=system_prompt, provider=provider
            )
            content = response.content
            ext = self._get_extension_for(template_type)
            return GeneratedOutput(
                content=content,
                filename=f"ai_generated_{template_type}",
                extension=ext,
                description=requirement,
            )
        except Exception as e:
            logger.error("AI generation failed: %s", e)
            return self.generate(template_type, description=requirement)

    def _get_extension_for(self, template_type: str) -> str:
        ext_map = {
            "bash": ".sh",
            "backup": ".sh",
            "log-rotation": ".sh",
            "disk-cleanup": ".sh",
            "package-update": ".sh",
            "health-check": ".sh",
            "python": ".py",
            "python-script": ".py",
            "systemd": ".service",
            "systemd-service": ".service",
            "systemd-timer": ".timer",
            "systemd-socket": ".socket",
            "cron": ".txt",
            "cron-job": ".txt",
            "dockerfile": "Dockerfile",
            "docker-compose": "compose.yaml",
            "nginx": ".conf",
            "apache": ".conf",
            "ssh": ".conf",
            "ssh-client": ".conf",
            "ssh-server": ".conf",
            "ansible": ".yaml",
            "terraform": ".tf",
            "kubernetes": ".yaml",
            "podman": ".yaml",
        }
        return ext_map.get(template_type, ".txt")

    def validate(self, content: str, file_type: str) -> ValidationResult:
        return validate_content(content, file_type)

    def preview(self, output: GeneratedOutput, max_lines: int = 30) -> str:
        return self.exporter.preview(output, max_lines)

    def export(self, output: GeneratedOutput, directory: str = ".") -> str:
        return self.exporter.export(output, directory)

    def list_template_categories(self) -> list[str]:
        return self.templates.list_categories()

    def list_templates(self, category: str | None = None) -> list[dict[str, Any]]:
        templates = self.templates.list(category)
        return [t.to_dict() for t in templates]

    def search_templates(self, query: str) -> list[dict[str, Any]]:
        templates = self.templates.search(query)
        return [t.to_dict() for t in templates]

    def get_template(self, name: str) -> dict[str, Any] | None:
        tpl = self.templates.get(name)
        return tpl.to_dict() if tpl else None

    def document(self, output: GeneratedOutput) -> str:
        lines = [
            f"# {output.description}",
            "",
            f"**File:** `{output.filename}{output.extension}`",
            f"**Type:** {output.extension.lstrip('.') if output.extension else 'unknown'}",
            f"**Lines:** {len(output.content.split(chr(10)))}",
            f"**Warnings:** {len(output.warnings)}",
            "",
            "## Warnings",
        ]
        if output.warnings:
            for w in output.warnings:
                lines.append(f"- {w}")
        else:
            lines.append("None")
        lines.extend(
            [
                "",
                "## Content Preview",
                "",
                "```" + (output.extension.lstrip(".") if output.extension else ""),
                output.content[:500],
                "```" if len(output.content) <= 500 else "```\n... (truncated)",
            ]
        )
        return "\n".join(lines)

    def compare(self, output_a: GeneratedOutput, output_b: GeneratedOutput) -> str:
        lines_a = output_a.content.split("\n")
        lines_b = output_b.content.split("\n")
        max_lines = max(len(lines_a), len(lines_b))
        changes = 0
        result = [
            f"# Comparison: {output_a.filename} vs {output_b.filename}",
            "",
            f"**File A:** `{output_a.filename}{output_a.extension}` ({len(lines_a)} lines)",
            f"**File B:** `{output_b.filename}{output_b.extension}` ({len(lines_b)} lines)",
            "",
            "## Differences",
        ]
        for i in range(max_lines):
            la = lines_a[i] if i < len(lines_a) else ""
            lb = lines_b[i] if i < len(lines_b) else ""
            if la != lb:
                changes += 1
                result.append("")
                result.append(f"### Line {i + 1}")
                if la:
                    result.append(f"- A: {la}")
                if lb:
                    result.append(f"- B: {lb}")
        result.append("")
        result.append(f"**Total changes:** {changes}")
        return "\n".join(result)

    def optimize(self, content: str, file_type: str) -> GeneratedOutput:
        validation = self.validate(content, file_type)
        suggestions = validation.suggestions

        optimized = content
        if file_type in ("sh", "bash"):
            if "set -euo pipefail" not in optimized:
                optimized = "set -euo pipefail\n" + optimized
            if (
                "#!/usr/bin/env bash" not in optimized
                and "#!/bin/bash" not in optimized
            ):
                optimized = "#!/usr/bin/env bash\n" + optimized

        warnings = list(validation.warnings) + list(validation.errors)
        ext = f".{file_type}" if not file_type.startswith(".") else file_type
        return GeneratedOutput(
            content=optimized,
            filename="optimized_output",
            extension=ext,
            description="Optimized version",
            warnings=warnings,
            metadata={
                "suggestions": suggestions,
                "original_length": len(content),
                "optimized_length": len(optimized),
            },
        )

    def generate_documentation(self, content: str, file_type: str) -> str:
        lines = content.split("\n")
        doc_lines = [
            "# Generated File Documentation",
            "",
            f"**File Type:** {file_type}",
            f"**Total Lines:** {len(lines)}",
            f"**Non-empty Lines:** {len([l for l in lines if l.strip()])}",
            "",
            "## Structure",
        ]
        if file_type in ("sh", "bash"):
            has_functions = [
                l
                for l in lines
                if l.strip().startswith("function ")
                or (l.strip().endswith("() {") and not l.strip().startswith("#"))
            ]
            if has_functions:
                doc_lines.append("### Functions")
                for f_line in has_functions:
                    doc_lines.append(f"- `{f_line.strip()}`")
            has_vars = [
                l
                for l in lines
                if "=" in l and not l.strip().startswith("#") and "==" not in l
            ]
            if has_vars:
                doc_lines.append("### Variables")
                for v_line in has_vars[:10]:
                    doc_lines.append(f"- `{v_line.strip()}`")
        elif file_type == "service":
            has_exec = [l for l in lines if l.strip().startswith("ExecStart")]
            if has_exec:
                doc_lines.append(
                    f"- ExecStart: `{has_exec[0].split('=', 1)[1].strip()}`"
                )
            has_desc = [l for l in lines if l.strip().startswith("Description")]
            if has_desc:
                doc_lines.append(
                    f"- Description: `{has_desc[0].split('=', 1)[1].strip()}`"
                )
        return "\n".join(doc_lines)
