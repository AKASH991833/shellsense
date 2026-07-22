from __future__ import annotations

import os
import tempfile

from shellsense.automation.engine import AutomationEngine
from shellsense.automation.exporters import AutomationExporter
from shellsense.automation.generators.bash import BashGenerator, GeneratedOutput
from shellsense.automation.generators.cron import CronGenerator
from shellsense.automation.generators.docker import DockerGenerator
from shellsense.automation.generators.infrastructure import InfrastructureGenerator
from shellsense.automation.generators.python_script import PythonGenerator
from shellsense.automation.generators.ssh import SSHGenerator
from shellsense.automation.generators.systemd import SystemdGenerator
from shellsense.automation.generators.webserver import WebServerGenerator
from shellsense.automation.templates import TemplateInfo, TemplateLibrary
from shellsense.automation.validators import (
    ApacheValidator,
    BashValidator,
    ComposeValidator,
    CronValidator,
    DockerfileValidator,
    NginxValidator,
    PythonValidator,
    SystemdValidator,
    YAMLValidator,
    validate_content,
)


class TestTemplateLibrary:
    def test_initial_count(self) -> None:
        lib = TemplateLibrary()
        assert lib.count >= 15

    def test_get_existing(self) -> None:
        lib = TemplateLibrary()
        tpl = lib.get("backup-script")
        assert tpl is not None
        assert tpl.category == "bash"

    def test_get_nonexistent(self) -> None:
        lib = TemplateLibrary()
        assert lib.get("nonexistent") is None

    def test_register(self) -> None:
        lib = TemplateLibrary()
        tpl = TemplateInfo(name="test", description="test", category="test")
        lib.register(tpl)
        assert lib.get("test") is not None

    def test_list_category(self) -> None:
        lib = TemplateLibrary()
        results = lib.list(category="bash")
        assert len(results) > 0
        assert all(t.category == "bash" for t in results)

    def test_list_tags(self) -> None:
        lib = TemplateLibrary()
        results = lib.list(tag="docker")
        assert len(results) > 0
        assert all("docker" in t.tags for t in results)

    def test_list_categories(self) -> None:
        lib = TemplateLibrary()
        cats = lib.list_categories()
        assert "bash" in cats
        assert "docker" in cats
        assert "systemd" in cats

    def test_search(self) -> None:
        lib = TemplateLibrary()
        results = lib.search("backup")
        assert len(results) >= 1

    def test_render(self) -> None:
        lib = TemplateLibrary()
        result = lib.render(
            "backup-script",
            source="/tmp",
            destination="/backup",
            name="test",
            retention_days="30",
            description="test",
        )
        assert result is not None
        assert "/tmp" in result
        assert "/backup" in result

    def test_remove(self) -> None:
        lib = TemplateLibrary()
        tpl = TemplateInfo(name="remove-test", description="test", category="test")
        lib.register(tpl)
        assert lib.remove("remove-test") is True
        assert lib.remove("nonexistent") is False

    def test_export_import(self) -> None:
        lib = TemplateLibrary()
        data = lib.export()
        assert len(data) >= 15
        lib2 = TemplateLibrary()
        count = lib2.import_templates(data)
        assert count >= 15


class TestValidators:
    def test_bash_validator_ok(self) -> None:
        v = BashValidator()
        result = v.validate("#!/usr/bin/env bash\necho hello\n")
        assert result.valid is True

    def test_bash_validator_dangerous(self) -> None:
        v = BashValidator()
        result = v.validate("rm -rf /")
        assert len(result.errors) > 0

    def test_python_validator_ok(self) -> None:
        v = PythonValidator()
        result = v.validate("x = 1\nprint(x)\n")
        assert result.valid is True

    def test_python_validator_syntax_error(self) -> None:
        v = PythonValidator()
        result = v.validate("x = ")
        assert result.valid is False
        assert len(result.errors) > 0

    def test_systemd_validator_ok(self) -> None:
        v = SystemdValidator()
        content = "[Unit]\nDescription=test\n\n[Service]\nExecStart=/bin/true\n\n[Install]\nWantedBy=multi-user.target\n"
        result = v.validate(content)
        assert result.valid

    def test_systemd_validator_missing_exec(self) -> None:
        v = SystemdValidator()
        content = "[Unit]\nDescription=test\n\n[Service]\n\n[Install]\nWantedBy=multi-user.target\n"
        result = v.validate(content)
        assert not result.valid

    def test_dockerfile_validator_ok(self) -> None:
        v = DockerfileValidator()
        content = "FROM ubuntu:22.04\nCMD bash\n"
        result = v.validate(content)
        assert result.valid

    def test_dockerfile_validator_no_from(self) -> None:
        v = DockerfileValidator()
        result = v.validate("RUN echo hello\n")
        assert not result.valid
        assert len(result.errors) > 0

    def test_compose_validator_ok(self) -> None:
        v = ComposeValidator()
        result = v.validate("version: '3.8'\nservices:\n  web:\n    image: nginx\n")
        assert result.valid

    def test_cron_validator_ok(self) -> None:
        v = CronValidator()
        result = v.validate("0 0 * * * /usr/bin/backup.sh\n")
        assert result.valid

    def test_cron_validator_invalid(self) -> None:
        v = CronValidator()
        result = v.validate("invalid cron entry\n")
        assert not result.valid

    def test_cron_special_strings(self) -> None:
        v = CronValidator()
        result = v.validate("@daily /usr/bin/backup.sh\n@reboot /usr/bin/check.sh\n")
        assert result.valid

    def test_nginx_validator_ok(self) -> None:
        v = NginxValidator()
        result = v.validate("server {\nlisten 80;\nserver_name example.com;\n}\n")
        assert result.valid

    def test_yaml_validator_tabs(self) -> None:
        v = YAMLValidator()
        result = v.validate("key:\n\tvalue\n")
        assert not result.valid

    def test_apache_validator(self) -> None:
        v = ApacheValidator()
        result = v.validate(
            "<VirtualHost *:80>\nServerName example.com\n</VirtualHost>\n"
        )
        assert result.valid

    def test_validate_content_dispatch(self) -> None:
        result = validate_content("#!/bin/bash\necho hi\n", "sh")
        assert result.valid is True
        result = validate_content("x = 1\n", "py")
        assert result.valid is True
        result = validate_content("invalid content", "unknown")
        assert "No validator" in result.warnings[0]


class TestBashGenerator:
    def setup_method(self) -> None:
        self.lib = TemplateLibrary()
        self.gen = BashGenerator(self.lib)

    def test_backup_script(self) -> None:
        result = self.gen.generate_backup_script(source="/etc", destination="/backup")
        assert "/etc" in result.content
        assert "/backup" in result.content
        assert result.extension == ".sh"

    def test_log_rotation(self) -> None:
        result = self.gen.generate_log_rotation(log_dir="/var/log")
        assert "/var/log" in result.content
        assert result.extension == ".sh"

    def test_disk_cleanup(self) -> None:
        result = self.gen.generate_disk_cleanup(threshold_pct=85)
        assert "85" in result.content

    def test_package_update(self) -> None:
        result = self.gen.generate_package_update()
        assert (
            "apt-get" in result.content
            or "dnf" in result.content
            or "pacman" in result.content
        )

    def test_health_check(self) -> None:
        result = self.gen.generate_health_check(alert_cpu=90)
        assert "90" in result.content
        assert "CPU" in result.content

    def test_user_management(self) -> None:
        result = self.gen.generate_user_management(action="create", username="testuser")
        assert "testuser" in result.content

    def test_network_diagnostics(self) -> None:
        result = self.gen.generate_network_diagnostics()
        assert "ping" in result.content

    def test_service_management(self) -> None:
        result = self.gen.generate_service_management(
            service_name="nginx", action="restart"
        )
        assert "nginx" in result.content
        assert "restart" in result.content

    def test_file_operations(self) -> None:
        result = self.gen.generate_file_operations(
            operation="sync", source="/src", dest="/dst"
        )
        assert "/src" in result.content
        assert "/dst" in result.content

    def test_monitoring(self) -> None:
        result = self.gen.generate_monitoring(interval=300)
        assert "300" in result.content

    def test_custom(self) -> None:
        result = self.gen.generate_custom("test", "test script", "echo hello")
        assert "test script" in result.content
        assert "echo hello" in result.content

    def test_generate_dispatch(self) -> None:
        result = self.gen.generate(
            "backup",
            source="/data",
            destination="/bak",
            name="test",
            retention_days="30",
        )
        assert result.extension == ".sh"

    def test_generated_output(self) -> None:
        output = GeneratedOutput(
            content="test", filename="test", extension=".sh", description="test"
        )
        d = output.to_dict()
        assert d["content"] == "test"
        assert d["filename"] == "test"


class TestPythonGenerator:
    def setup_method(self) -> None:
        self.lib = TemplateLibrary()
        self.gen = PythonGenerator(self.lib)

    def test_generate_script(self) -> None:
        result = self.gen.generate_script(name="test_script", description="Test")
        assert "test_script" in result.content
        assert result.extension == ".py"

    def test_sysadmin(self) -> None:
        result = self.gen.generate_sysadmin()
        assert "System Administration" in result.content

    def test_log_parser(self) -> None:
        result = self.gen.generate_log_parser()
        assert "log" in result.content.lower()

    def test_generate_dispatch(self) -> None:
        result = self.gen.generate("script", name="dispatched")
        assert result.extension == ".py"


class TestSystemdGenerator:
    def setup_method(self) -> None:
        self.lib = TemplateLibrary()
        self.gen = SystemdGenerator(self.lib)

    def test_generate_service(self) -> None:
        result = self.gen.generate_service(name="myapp", exec_start="/usr/bin/myapp")
        assert "myapp" in result.content
        assert result.extension == ".service"
        assert "[Service]" in result.content

    def test_generate_timer(self) -> None:
        result = self.gen.generate_timer(name="myapp", unit="myapp.service")
        assert "myapp.service" in result.content
        assert "[Timer]" in result.content

    def test_generate_socket(self) -> None:
        result = self.gen.generate_socket(name="myapp")
        assert "[Socket]" in result.content

    def test_generate_target(self) -> None:
        result = self.gen.generate_target(name="myapp")
        assert "multi-user.target" in result.content


class TestCronGenerator:
    def setup_method(self) -> None:
        self.lib = TemplateLibrary()
        self.gen = CronGenerator(self.lib)

    def test_generate_job(self) -> None:
        result = self.gen.generate_job(
            name="test", schedule="daily", command="/usr/bin/backup"
        )
        assert "0 0 * * *" in result.content or "@daily" in result.content
        assert "/usr/bin/backup" in result.content

    def test_validate_schedule(self) -> None:
        valid, msg = self.gen.validate_schedule("daily")
        assert valid is True
        valid, msg = self.gen.validate_schedule("0 0 * * *")
        assert valid is True


class TestDockerGenerator:
    def setup_method(self) -> None:
        self.lib = TemplateLibrary()
        self.gen = DockerGenerator(self.lib)

    def test_generate_dockerfile(self) -> None:
        result = self.gen.generate_dockerfile(name="myapp", base_image="python")
        assert "FROM python" in result.content
        assert result.extension == "Dockerfile"

    def test_generate_compose(self) -> None:
        result = self.gen.generate_compose(name="myapp")
        assert "services:" in result.content
        assert "compose.yaml" in result.filename or "compose" in result.filename


class TestWebServerGenerator:
    def setup_method(self) -> None:
        self.lib = TemplateLibrary()
        self.gen = WebServerGenerator(self.lib)

    def test_nginx_reverse_proxy(self) -> None:
        result = self.gen.generate_nginx_reverse_proxy(
            server_name="example.com", proxy_pass="http://localhost:8000"
        )
        assert "example.com" in result.content
        assert "proxy_pass" in result.content

    def test_nginx_static(self) -> None:
        result = self.gen.generate_nginx_static(server_name="example.com")
        assert "try_files" in result.content

    def test_nginx_load_balancer(self) -> None:
        result = self.gen.generate_nginx_load_balancer(server_name="example.com")
        assert "upstream" in result.content

    def test_apache_vhost(self) -> None:
        result = self.gen.generate_apache_vhost(server_name="example.com")
        assert "VirtualHost" in result.content


class TestSSHGenerator:
    def setup_method(self) -> None:
        self.lib = TemplateLibrary()
        self.gen = SSHGenerator(self.lib)

    def test_client_config(self) -> None:
        result = self.gen.generate_client_config(hostname="server.example.com")
        assert "server.example.com" in result.content

    def test_server_config(self) -> None:
        result = self.gen.generate_server_config()
        assert "PubkeyAuthentication" in result.content
        assert len(result.warnings) > 0

    def test_key_guidance(self) -> None:
        result = self.gen.generate_key_guidance()
        assert "ssh-keygen" in result.content


class TestInfrastructureGenerator:
    def setup_method(self) -> None:
        self.lib = TemplateLibrary()
        self.gen = InfrastructureGenerator(self.lib)

    def test_ansible(self) -> None:
        result = self.gen.generate_ansible_playbook(name="deploy")
        assert "hosts:" in result.content

    def test_terraform(self) -> None:
        result = self.gen.generate_terraform(name="main")
        assert "terraform" in result.content

    def test_kubernetes(self) -> None:
        result = self.gen.generate_kubernetes(name="myapp")
        assert "Deployment" in result.content or "kind:" in result.content

    def test_podman(self) -> None:
        result = self.gen.generate_podman(name="myapp")
        assert "podman" in result.content or "Podman" in result.content


class TestAutomationExporter:
    def test_export(self) -> None:
        exporter = AutomationExporter()
        output = GeneratedOutput(
            content="test", filename="export_test", extension=".sh"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = exporter.export(output, tmpdir)
            assert os.path.isfile(path)
            with open(path) as f:
                assert f.read() == "test"

    def test_to_markdown(self) -> None:
        exporter = AutomationExporter()
        output = GeneratedOutput(
            content="echo hi", filename="test", extension=".sh", description="Test"
        )
        md = exporter.to_markdown(output)
        assert "Test" in md
        assert "echo hi" in md

    def test_preview(self) -> None:
        exporter = AutomationExporter()
        output = GeneratedOutput(
            content="line1\nline2\nline3", filename="test", extension=".sh"
        )
        preview = exporter.preview(output, max_lines=2)
        assert "line1" in preview
        assert "more lines" in preview

    def test_supported_formats(self) -> None:
        exporter = AutomationExporter()
        fmts = exporter.supported_formats()
        assert "sh" in fmts
        assert "py" in fmts
        assert "yaml" in fmts


class TestAutomationEngine:
    def setup_method(self) -> None:
        self.engine = AutomationEngine()

    def test_engine_creation(self) -> None:
        assert self.engine.templates is not None
        assert self.engine.bash is not None
        assert self.engine.exporter is not None
        assert self.engine.interactive is not None

    def test_generate_backup(self) -> None:
        result = self.engine.generate(
            "backup",
            source="/data",
            destination="/backup",
            name="test",
            retention_days="30",
        )
        assert result.extension == ".sh"
        assert result.filename == "test_backup"

    def test_generate_dockerfile(self) -> None:
        result = self.engine.generate("dockerfile", base_image="ubuntu")
        assert "FROM ubuntu" in result.content

    def test_generate_systemd(self) -> None:
        result = self.engine.generate(
            "systemd-service", name="myapp", exec_start="/usr/bin/app"
        )
        assert "[Service]" in result.content

    def test_generate_unknown_falls_back(self) -> None:
        result = self.engine.generate(
            "nonexistent-type", description="fallback", content="echo hi"
        )
        assert result.extension == ".sh"

    def test_validate_bash(self) -> None:
        result = self.engine.validate("#!/bin/bash\necho hi\n", "sh")
        assert result.valid is True

    def test_validate_python_error(self) -> None:
        result = self.engine.validate("x = ", "py")
        assert result.valid is False

    def test_preview(self) -> None:
        output = GeneratedOutput(content="a\nb\nc", filename="test", extension=".sh")
        preview = self.engine.preview(output, max_lines=2)
        assert "a" in preview

    def test_export(self) -> None:
        output = GeneratedOutput(content="test", filename="exported", extension=".sh")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self.engine.export(output, tmpdir)
            assert os.path.isfile(path)

    def test_list_template_categories(self) -> None:
        cats = self.engine.list_template_categories()
        assert "bash" in cats

    def test_list_templates(self) -> None:
        templates = self.engine.list_templates("bash")
        assert len(templates) > 0
        assert all(t["category"] == "bash" for t in templates)

    def test_search_templates(self) -> None:
        results = self.engine.search_templates("backup")
        assert len(results) > 0

    def test_get_template(self) -> None:
        tpl = self.engine.get_template("backup-script")
        assert tpl is not None
        assert tpl["name"] == "backup-script"

    def test_document(self) -> None:
        output = GeneratedOutput(
            content="hello world",
            filename="test",
            extension=".sh",
            description="Test doc",
        )
        doc = self.engine.document(output)
        assert "Test doc" in doc
        assert "hello world" in doc

    def test_compare_identical(self) -> None:
        a = GeneratedOutput(content="same", filename="a", extension=".txt")
        b = GeneratedOutput(content="same", filename="b", extension=".txt")
        cmp = self.engine.compare(a, b)
        assert "0" in cmp.split("**Total changes:**")[1].strip()

    def test_compare_different(self) -> None:
        a = GeneratedOutput(content="hello", filename="a", extension=".txt")
        b = GeneratedOutput(content="world", filename="b", extension=".txt")
        cmp = self.engine.compare(a, b)
        assert "1" in cmp.split("**Total changes:**")[1].strip()

    def test_optimize_bash(self) -> None:
        result = self.engine.optimize("echo hi", "sh")
        assert "set -euo pipefail" in result.content

    def test_generate_documentation(self) -> None:
        doc = self.engine.generate_documentation("#!/bin/bash\necho hi", "sh")
        assert "File Type" in doc
        assert "bash" in doc or "sh" in doc

    def test_generate_with_ai_no_ai(self) -> None:
        result = self.engine.generate_with_ai("backup", "Create a backup script")
        assert result.extension == ".sh"
