from __future__ import annotations

from typing import Any

from shellsense.automation.generators.bash import GeneratedOutput
from shellsense.automation.templates import TemplateLibrary
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class SystemdGenerator:
    def __init__(self, templates: TemplateLibrary) -> None:
        self._templates = templates

    def generate_service(
        self,
        name: str = "myapp",
        description: str = "My Application",
        exec_start: str = "/usr/local/bin/myapp",
        user: str = "root",
        group: str = "root",
        after: str = "network.target",
        working_directory: str = "/opt/myapp",
        restart: str = "on-failure",
    ) -> GeneratedOutput:
        content = (
            self._templates.render(
                "systemd-service",
                name=name,
                description=description,
                after=after,
                requires="",
                documentation="",
                type="simple",
                user=user,
                group=group,
                working_directory=working_directory,
                exec_start=exec_start,
                exec_reload="",
                restart=restart,
                restart_sec="5",
                env_file="",
                limit_nofile="65535",
                wanted_by="multi-user.target",
            )
            or ""
        )
        return GeneratedOutput(
            content=content,
            filename=f"{name}",
            extension=".service",
            description=f"Systemd service for {name}",
            warnings=["Review ExecStart path and permissions"],
        )

    def generate_timer(
        self,
        name: str = "myapp",
        description: str = "My Application Timer",
        on_calendar: str = "daily",
        unit: str = "myapp.service",
    ) -> GeneratedOutput:
        content = (
            self._templates.render(
                "systemd-timer",
                name=name,
                description=description,
                requires=unit,
                on_calendar=on_calendar,
                on_boot_sec="",
                on_unit_active_sec="",
                unit=unit,
                persistent="true",
                randomized_delay="5min",
                wanted_by="timers.target",
            )
            or ""
        )
        return GeneratedOutput(
            content=content,
            filename=f"{name}",
            extension=".timer",
            description=f"Systemd timer for {unit}",
            warnings=[f"Ensure {unit} exists"],
        )

    def generate_socket(
        self,
        name: str = "myapp",
        description: str = "My Application Socket",
        listen_stream: str = "/run/myapp.sock",
        service: str = "myapp.service",
    ) -> GeneratedOutput:
        content = f"""[Unit]
Description={description}
Requires={service}

[Socket]
ListenStream={listen_stream}
SocketMode=0660
SocketUser=root
SocketGroup=root
Accept=no

[Install]
WantedBy=sockets.target
"""
        return GeneratedOutput(
            content=content,
            filename=f"{name}",
            extension=".socket",
            description=f"Systemd socket for {service}",
        )

    def generate_target(
        self,
        name: str = "myapp-target",
        description: str = "My Application Target",
        wants: str = "",
        requires: str = "",
    ) -> GeneratedOutput:
        content = f"""[Unit]
Description={description}
Requires={requires}
Wants={wants}
After={requires}

[Install]
WantedBy=multi-user.target
"""
        return GeneratedOutput(
            content=content,
            filename=f"{name}",
            extension=".target",
            description=f"Systemd target: {name}",
        )

    def generate(self, template_name: str, **kwargs: Any) -> GeneratedOutput:
        generators = {
            "service": self.generate_service,
            "timer": self.generate_timer,
            "socket": self.generate_socket,
            "target": self.generate_target,
        }
        gen = generators.get(template_name)
        if gen is None:
            return self.generate_service(
                name=kwargs.get("name", "app"),
                description=kwargs.get("description", ""),
                exec_start=kwargs.get("exec_start", "/usr/bin/app"),
            )
        return gen(**{k: v for k, v in kwargs.items() if k in gen.__code__.co_varnames})
