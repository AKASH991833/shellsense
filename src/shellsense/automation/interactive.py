from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shellsense.automation.generators.bash import GeneratedOutput
from shellsense.utils.logging import get_logger

if TYPE_CHECKING:
    from shellsense.automation.engine import AutomationEngine

logger = get_logger(__name__)


class InteractiveGenerator:
    def __init__(self, engine: AutomationEngine) -> None:
        self._engine = engine
        self._questions: dict[str, list[dict[str, Any]]] = {
            "backup": [
                {
                    "key": "source",
                    "question": "Source path to back up",
                    "default": "/etc",
                },
                {
                    "key": "destination",
                    "question": "Backup destination directory",
                    "default": "/backup",
                },
                {
                    "key": "retention_days",
                    "question": "Days to retain backups",
                    "default": "30",
                },
                {"key": "name", "question": "Backup name", "default": "backup"},
            ],
            "systemd-service": [
                {"key": "name", "question": "Service name", "default": "myapp"},
                {
                    "key": "description",
                    "question": "Service description",
                    "default": "My Application",
                },
                {
                    "key": "exec_start",
                    "question": "ExecStart path (full path to binary)",
                    "default": "/usr/local/bin/myapp",
                },
                {"key": "user", "question": "Run as user", "default": "root"},
                {
                    "key": "working_directory",
                    "question": "Working directory",
                    "default": "/opt/myapp",
                },
                {
                    "key": "restart",
                    "question": "Restart policy (no, on-success, on-failure, always)",
                    "default": "on-failure",
                },
            ],
            "dockerfile": [
                {"key": "base_image", "question": "Base image", "default": "python"},
                {"key": "base_tag", "question": "Base tag", "default": "3.12-slim"},
                {
                    "key": "packages",
                    "question": "System packages to install (space-separated)",
                    "default": "curl",
                },
                {
                    "key": "workdir",
                    "question": "Working directory in container",
                    "default": "/app",
                },
                {"key": "ports", "question": "Ports to expose", "default": "8000"},
                {"key": "entrypoint", "question": "Entrypoint command", "default": ""},
            ],
            "nginx-proxy": [
                {
                    "key": "server_name",
                    "question": "Server name (domain)",
                    "default": "example.com",
                },
                {
                    "key": "proxy_pass",
                    "question": "Proxy pass URL",
                    "default": "http://localhost:8000",
                },
                {"key": "listen_port", "question": "Listen port", "default": "80"},
                {
                    "key": "ssl",
                    "question": "Enable SSL? (true/false)",
                    "default": "false",
                },
            ],
            "cron-job": [
                {"key": "name", "question": "Job name", "default": "myjob"},
                {
                    "key": "description",
                    "question": "Job description",
                    "default": "Scheduled task",
                },
                {
                    "key": "schedule",
                    "question": "Schedule (daily, hourly, weekly, or cron expression)",
                    "default": "daily",
                },
                {
                    "key": "command",
                    "question": "Command to run",
                    "default": "/usr/local/bin/script.sh",
                },
            ],
            "health-check": [
                {
                    "key": "alert_cpu",
                    "question": "CPU alert threshold (%)",
                    "default": "80",
                },
                {
                    "key": "alert_mem",
                    "question": "Memory alert threshold (%)",
                    "default": "80",
                },
                {
                    "key": "alert_disk",
                    "question": "Disk alert threshold (%)",
                    "default": "90",
                },
                {
                    "key": "check_services",
                    "question": "Services to check (space-separated)",
                    "default": "ssh nginx",
                },
            ],
        }

    def get_questions_for(self, template_type: str) -> list[dict[str, Any]]:
        return self._questions.get(template_type, [])

    def generate_from_answers(
        self, template_type: str, answers: dict[str, str]
    ) -> GeneratedOutput:
        return self._engine.generate(template_type, **answers)

    def list_supported_types(self) -> list[str]:
        return sorted(self._questions.keys()) + [
            "python-script",
            "log-rotation",
            "disk-cleanup",
            "package-update",
            "user-management",
            "network-diagnostics",
            "service-management",
            "file-operations",
            "monitoring",
            "docker-compose",
            "systemd-timer",
            "systemd-socket",
            "apache-vhost",
            "nginx-static",
            "ssh-client",
            "ssh-server",
            "ansible",
            "kubernetes",
            "terraform",
        ]

    def supported_categories(self) -> dict[str, list[str]]:
        return {
            "backup": ["backup"],
            "bash": [
                "backup",
                "log-rotation",
                "disk-cleanup",
                "package-update",
                "health-check",
                "user-management",
                "network-diagnostics",
                "service-management",
                "file-operations",
                "monitoring",
            ],
            "python": ["python-script", "sysadmin", "log-parser"],
            "systemd": ["systemd-service", "systemd-timer", "systemd-socket"],
            "cron": ["cron-job"],
            "docker": ["dockerfile", "docker-compose"],
            "webserver": [
                "nginx-proxy",
                "nginx-static",
                "nginx-load-balancer",
                "apache-vhost",
            ],
            "ssh": ["ssh-client", "ssh-server", "ssh-key-guidance"],
            "infrastructure": ["ansible", "terraform", "kubernetes", "podman"],
        }
