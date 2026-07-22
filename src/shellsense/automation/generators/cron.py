from __future__ import annotations

from typing import Any

from shellsense.automation.generators.bash import GeneratedOutput
from shellsense.automation.templates import TemplateLibrary
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

SCHEDULE_HELP = {
    "hourly": "0 * * * *",
    "daily": "0 0 * * *",
    "weekly": "0 0 * * 0",
    "monthly": "0 0 1 * *",
    "yearly": "0 0 1 1 *",
    "reboot": "@reboot",
    "every-hour": "0 * * * *",
    "every-6-hours": "0 */6 * * *",
    "every-12-hours": "0 */12 * * *",
    "every-30-min": "*/30 * * * *",
    "every-15-min": "*/15 * * * *",
    "every-5-min": "*/5 * * * *",
    "every-minute": "* * * * *",
    "weekdays-9am": "0 9 * * 1-5",
    "midnight": "0 0 * * *",
}


class CronGenerator:
    def __init__(self, templates: TemplateLibrary) -> None:
        self._templates = templates

    def generate_job(
        self,
        name: str = "myjob",
        description: str = "My Cron Job",
        schedule: str = "daily",
        command: str = "/usr/local/bin/script.sh",
    ) -> GeneratedOutput:
        cron_schedule = SCHEDULE_HELP.get(schedule, schedule)
        content = (
            self._templates.render(
                "cron-job",
                name=name,
                description=description,
                schedule=cron_schedule,
                command=command,
            )
            or ""
        )
        warnings = []
        if "{" in content:
            warnings.append("Template contains unresolved placeholders")
        return GeneratedOutput(
            content=content,
            filename=f"cron_{name}",
            extension=".txt",
            description=f"Cron job: {description}",
            warnings=warnings,
        )

    def validate_schedule(self, expression: str) -> tuple[bool, str]:
        if expression in SCHEDULE_HELP:
            return True, "Known schedule alias"
        parts = expression.strip().split()
        if len(parts) != 5 and "@" not in expression:
            return False, "Must have 5 time fields or a @schedule alias"
        return True, "Valid format"

    def generate(self, template_name: str, **kwargs: Any) -> GeneratedOutput:
        return self.generate_job(
            name=kwargs.get("name", "job"),
            description=kwargs.get("description", "Cron job"),
            schedule=kwargs.get("schedule", "daily"),
            command=kwargs.get("command", "/usr/bin/true"),
        )
