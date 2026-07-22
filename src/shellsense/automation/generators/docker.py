from __future__ import annotations

from typing import Any

from shellsense.automation.generators.bash import GeneratedOutput
from shellsense.automation.templates import TemplateLibrary
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class DockerGenerator:
    def __init__(self, templates: TemplateLibrary) -> None:
        self._templates = templates

    def generate_dockerfile(
        self,
        name: str = "app",
        description: str = "Container image",
        base_image: str = "python",
        base_tag: str = "3.12-slim",
        packages: str = "curl ca-certificates",
        workdir: str = "/app",
        ports: str = "8000",
        maintainer: str = "admin@example.com",
        env_vars: str = "PYTHONUNBUFFERED=1",
        extra_commands: str = "",
        copy_section: str = "COPY . .",
        entrypoint: str = "",
    ) -> GeneratedOutput:
        arg_section = ""
        entrypoint_section = ""
        if entrypoint:
            entrypoint_section = f'ENTRYPOINT ["{entrypoint}"]'
        content = (
            self._templates.render(
                "dockerfile",
                name=name,
                description=description,
                base_image=base_image,
                base_tag=base_tag,
                maintainer=maintainer,
                packages=packages,
                workdir=workdir,
                ports=ports,
                env_vars=env_vars,
                arg_section=arg_section,
                extra_commands=extra_commands,
                copy_section=copy_section,
                entrypoint_section=entrypoint_section,
            )
            or ""
        )
        warnings = []
        if base_tag == "latest":
            warnings.append(
                "Using 'latest' tag - pin to a specific version for production"
            )
        return GeneratedOutput(
            content=content,
            filename="Dockerfile",
            extension="Dockerfile",
            description=f"Dockerfile for {name}",
            warnings=warnings,
        )

    def generate_compose(
        self,
        name: str = "app",
        description: str = "Application stack",
        service_name: str = "web",
        build_context: str = ".",
        image_name: str = "myapp:latest",
        container_name: str = "myapp",
        ports: str = "8000:8000",
        env_vars: str = "DEBUG=false",
        volumes: str = "./data:/data",
        network_name: str = "app-net",
    ) -> GeneratedOutput:
        content = (
            self._templates.render(
                "docker-compose",
                name=name,
                description=description,
                version="3.8",
                service_name=service_name,
                build_context=build_context,
                image_name=image_name,
                container_name=container_name,
                restart_policy="unless-stopped",
                ports=ports,
                env_vars=env_vars,
                volumes=volumes,
                network_name=network_name,
                healthcheck_test='["CMD", "curl", "-f", "http://localhost"]',
                healthcheck_interval="30s",
                healthcheck_timeout="10s",
                healthcheck_retries="3",
                network_driver="bridge",
            )
            or ""
        )
        return GeneratedOutput(
            content=content,
            filename="compose",
            extension="compose.yaml",
            description=f"Docker Compose for {name}",
        )

    def generate(self, template_name: str, **kwargs: Any) -> GeneratedOutput:
        generators = {
            "dockerfile": self.generate_dockerfile,
            "compose": self.generate_compose,
        }
        gen = generators.get(template_name)
        if gen is None:
            return self.generate_dockerfile()
        return gen(**{k: v for k, v in kwargs.items() if k in gen.__code__.co_varnames})
