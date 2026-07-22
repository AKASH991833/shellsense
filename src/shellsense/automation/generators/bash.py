from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shellsense.automation.templates import TemplateLibrary
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GeneratedOutput:
    content: str
    filename: str
    extension: str
    description: str = ""
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "filename": self.filename,
            "extension": self.extension,
            "description": self.description,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


class BashGenerator:
    def __init__(self, templates: TemplateLibrary) -> None:
        self._templates = templates

    def generate_backup_script(
        self,
        name: str = "backup",
        source: str = "/etc",
        destination: str = "/backup",
        retention_days: int = 30,
    ) -> GeneratedOutput:
        content = (
            self._templates.render(
                "backup-script",
                name=name,
                source=source,
                destination=destination,
                retention_days=str(retention_days),
                description=f"Backup script for {source}",
            )
            or ""
        )
        return GeneratedOutput(
            content=content,
            filename=f"{name}_backup",
            extension=".sh",
            description=f"Backup script for {source}",
        )

    def generate_log_rotation(
        self,
        log_dir: str = "/var/log",
        pattern: str = "*.log",
        max_size_mb: int = 100,
        retention_count: int = 7,
    ) -> GeneratedOutput:
        content = (
            self._templates.render(
                "log-rotation",
                name="log-rotation",
                log_dir=log_dir,
                pattern=pattern,
                max_size_mb=str(max_size_mb),
                retention_count=str(retention_count),
            )
            or ""
        )
        return GeneratedOutput(
            content=content,
            filename="log_rotation",
            extension=".sh",
            description=f"Log rotation for {log_dir}",
        )

    def generate_disk_cleanup(
        self, threshold_pct: int = 90, cleanup_dirs: str = "/ /var /home"
    ) -> GeneratedOutput:
        dirs_list = " ".join(cleanup_dirs.split())
        content = (
            self._templates.render(
                "disk-cleanup",
                name="disk-cleanup",
                threshold_pct=str(threshold_pct),
                cleanup_dirs=dirs_list,
            )
            or ""
        )
        return GeneratedOutput(
            content=content,
            filename="disk_cleanup",
            extension=".sh",
            description="Disk cleanup script",
            warnings=["This script cleans package caches and temporary files"],
        )

    def generate_package_update(
        self, log_file: str = "/var/log/packages_update.log"
    ) -> GeneratedOutput:
        content = (
            self._templates.render(
                "package-update", name="package-update", log_file=log_file
            )
            or ""
        )
        return GeneratedOutput(
            content=content,
            filename="update_packages",
            extension=".sh",
            description="System package update script",
            warnings=["Requires root privileges"],
        )

    def generate_health_check(
        self,
        alert_cpu: int = 80,
        alert_mem: int = 80,
        alert_disk: int = 90,
        check_services: str = "ssh nginx",
    ) -> GeneratedOutput:
        services = " ".join(check_services.split())
        content = (
            self._templates.render(
                "health-check",
                name="health-check",
                alert_cpu=str(alert_cpu),
                alert_mem=str(alert_mem),
                alert_disk=str(alert_disk),
                check_services=services,
            )
            or ""
        )
        return GeneratedOutput(
            content=content,
            filename="health_check",
            extension=".sh",
            description="System health check",
        )

    def generate_user_management(
        self, action: str = "create", username: str = "user", groups: str = "sudo"
    ) -> GeneratedOutput:
        actions = {
            "create": "useradd -m",
            "delete": "userdel -r",
            "lock": "usermod -L",
            "unlock": "usermod -U",
        }
        cmd = actions.get(action, "useradd -m")
        content = f"""#!/usr/bin/env bash
# User Management - {action}
set -euo pipefail

USERNAME="{username}"
GROUPS=({groups})

echo "Executing: {action} user '$USERNAME'"
{cmd} "$USERNAME"

for group in "${{GROUPS[@]}}"; do
    usermod -aG "$group" "$USERNAME"
    echo "  Added to group: $group"
done

echo "User {action} complete: $USERNAME"
passwd -S "$USERNAME" 2>/dev/null || echo "Set password with: passwd $USERNAME"
"""
        return GeneratedOutput(
            content=content,
            filename=f"user_{action}_{username}",
            extension=".sh",
            description=f"{action} user: {username}",
            warnings=["Requires root privileges"],
        )

    def generate_network_diagnostics(self) -> GeneratedOutput:
        content = """#!/usr/bin/env bash
# Network Diagnostics Script
set -euo pipefail

echo "=== Network Diagnostics ==="
echo "Hostname: $(hostname)"
echo "Date: $(date)"
echo ""

echo "=== Network Interfaces ==="
ip addr show 2>/dev/null || ifconfig

echo ""
echo "=== Routing Table ==="
ip route show 2>/dev/null || route -n

echo ""
echo "=== DNS Resolution ==="
echo "Nameservers:"
cat /etc/resolv.conf 2>/dev/null || echo "No resolv.conf found"

echo ""
echo "=== Connectivity Tests ==="
for host in "8.8.8.8" "1.1.1.1" "google.com"; do
    if ping -c 2 -W 3 "$host" &>/dev/null; then
        echo "  [OK] $host"
    else
        echo "  [FAIL] $host"
    fi
done

echo ""
echo "=== Open Ports ==="
ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null || echo "Port listing not available"

echo ""
echo "=== DNS Resolution Test ==="
for domain in "google.com" "github.com"; do
    result=$(dig +short "$domain" 2>/dev/null || host "$domain" 2>/dev/null || nslookup "$domain" 2>/dev/null)
    if [ -n "$result" ]; then
        echo "  [OK] $domain -> $result"
    else
        echo "  [FAIL] $domain"
    fi
done

echo ""
echo "Network diagnostics complete"
"""
        return GeneratedOutput(
            content=content,
            filename="network_diagnostics",
            extension=".sh",
            description="Network diagnostic script",
        )

    def generate_service_management(
        self, service_name: str = "nginx", action: str = "status"
    ) -> GeneratedOutput:
        content = f"""#!/usr/bin/env bash
# Service Management - {action} {service_name}
set -euo pipefail

SERVICE="{service_name}"

echo "Service: $SERVICE"
echo "Action: {action}"
echo ""

case "{action}" in
    status)
        systemctl status "$SERVICE" --no-pager || true
        journalctl -u "$SERVICE" --no-pager -n 20 || true
        ;;
    start|stop|restart|reload|enable|disable)
        systemctl {action} "$SERVICE"
        echo "Service $SERVICE {action} completed"
        systemctl status "$SERVICE" --no-pager | head -5
        ;;
    *)
        echo "Usage: $0 {{status|start|stop|restart|reload|enable|disable}}"
        exit 1
        ;;
esac
"""
        return GeneratedOutput(
            content=content,
            filename=f"service_{action}_{service_name}",
            extension=".sh",
            description=f"{action} service: {service_name}",
            warnings=["Requires root privileges for start/stop/restart"],
        )

    def generate_file_operations(
        self,
        operation: str = "sync",
        source: str = "/source",
        dest: str = "/dest",
        pattern: str = "*",
    ) -> GeneratedOutput:
        content = f"""#!/usr/bin/env bash
# File Operations - {operation}
set -euo pipefail

SOURCE="{source}"
DEST="{dest}"
PATTERN="{pattern}"

echo "File operation: {operation}"
echo "Source: $SOURCE"
echo "Destination: $DEST"
echo ""

if [ ! -d "$SOURCE" ]; then
    echo "ERROR: Source directory does not exist: $SOURCE"
    exit 1
fi

mkdir -p "$DEST"

case "{operation}" in
    sync)
        rsync -avh --progress "$SOURCE/" "$DEST/"
        ;;
    backup)
        timestamp=$(date +%Y%m%d_%H%M%S)
        tar -czf "$DEST/backup_$timestamp.tar.gz" -C "$(dirname "$SOURCE")" "$(basename "$SOURCE")"
        echo "Backup created: $DEST/backup_$timestamp.tar.gz"
        ;;
    archive)
        tar -czf "$DEST/archive.tar.gz" -C "$SOURCE" .
        echo "Archive created: $DEST/archive.tar.gz"
        ;;
    *)
        echo "Unknown operation: {operation}"
        exit 1
        ;;
esac

echo "File operation complete"
"""
        return GeneratedOutput(
            content=content,
            filename=f"fileops_{operation}",
            extension=".sh",
            description=f"File {operation} from {source} to {dest}",
        )

    def generate_monitoring(
        self, interval: int = 60, output_dir: str = "/var/log/monitoring"
    ) -> GeneratedOutput:
        content = f"""#!/usr/bin/env bash
# System Monitoring Script
set -euo pipefail

INTERVAL={interval}
OUTPUT_DIR="{output_dir}"

mkdir -p "$OUTPUT_DIR"

monitor() {{
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    logfile="$OUTPUT_DIR/monitor_$(date +%Y%m%d).log"

    {{
        echo "[$timestamp]"
        echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{{print $2}}')%"
        echo "MEM: $(free -h | awk '/^Mem:/ {{print $3}}')"
        echo "DISK: $(df -h / | awk 'NR==2 {{print $5}}')"
        echo "PROCESSES: $(ps aux --no-headers | wc -l)"
        echo "LOAD: $(uptime | awk -F'load average:' '{{print $2}}')"
        echo "---"
    }} >> "$logfile"
}}

echo "Monitoring started (interval: {{INTERVAL}}s)"
echo "Output: $OUTPUT_DIR"
echo ""

while true; do
    monitor
    sleep "$INTERVAL"
done
"""
        return GeneratedOutput(
            content=content,
            filename="system_monitor",
            extension=".sh",
            description=f"System monitoring every {interval}s",
        )

    def generate_custom(
        self, name: str, description: str, content_body: str
    ) -> GeneratedOutput:
        content = f"""#!/usr/bin/env bash
# {name} - {description}
set -euo pipefail

{content_body}
"""
        return GeneratedOutput(
            content=content, filename=name, extension=".sh", description=description
        )

    def generate(self, template_name: str, **kwargs: Any) -> GeneratedOutput:
        generators = {
            "backup": self.generate_backup_script,
            "log-rotation": self.generate_log_rotation,
            "disk-cleanup": self.generate_disk_cleanup,
            "package-update": self.generate_package_update,
            "health-check": self.generate_health_check,
            "user-management": self.generate_user_management,
            "network-diagnostics": self.generate_network_diagnostics,
            "service-management": self.generate_service_management,
            "file-operations": self.generate_file_operations,
            "monitoring": self.generate_monitoring,
            "custom": self.generate_custom,
        }
        gen = generators.get(template_name)
        if gen is None:
            return self.generate_custom(
                template_name, kwargs.get("description", ""), kwargs.get("content", "")
            )
        return gen(**{k: v for k, v in kwargs.items() if k in gen.__code__.co_varnames})
