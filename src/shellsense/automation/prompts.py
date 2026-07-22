from __future__ import annotations

AUTOMATION_SYSTEM_PROMPT = """You are ShellSense AI's automation generator.

Generate production-ready automation files based on the user's requirements.

RULES:
- Output complete, working files
- Include comments explaining important sections
- Use best practices for the target platform
- Clearly label placeholders that need user review
- Never include real secrets or credentials
- Warn about destructive operations
- Prefer safe defaults
- Mark AI-generated content clearly"""


GENERATION_PROMPTS: dict[str, str] = {
    "bash": """Generate a bash script for the following requirement:

{requirement}

Requirements:
- Use set -euo pipefail for safety
- Include usage() function with help text
- Validate arguments
- Handle errors gracefully
- Follow bash best practices
- Comment non-obvious sections""",
    "python": """Generate a Python script for the following requirement:

{requirement}

Requirements:
- Use argparse for argument parsing
- Include proper logging
- Handle errors with try/except
- Follow PEP 8 style
- Include type hints where appropriate
- Main function should return int exit code""",
    "systemd": """Generate a systemd unit file for:

{requirement}

Requirements:
- Include [Unit], [Service], and [Install] sections
- Use appropriate service type
- Set proper resource limits
- Include security hardening where possible""",
    "dockerfile": """Generate a Dockerfile for:

{requirement}

Requirements:
- Use specific version tags, not 'latest'
- Minimize layer count
- Use multi-stage builds where appropriate
- Include HEALTHCHECK
- Follow Docker best practices""",
    "docker-compose": """Generate a Docker Compose file for:

{requirement}

Requirements:
- Use version 3.8 or later
- Include health checks
- Define networks and volumes
- Use environment variables for configuration""",
    "nginx": """Generate an Nginx configuration for:

{requirement}

Requirements:
- Include listen, server_name, and location blocks
- Set proper security headers
- Configure access and error logs
- Include SSL configuration if applicable""",
    "apache": """Generate an Apache configuration for:

{requirement}

Requirements:
- Include VirtualHost block
- Set DocumentRoot and Directory permissions
- Configure logging
- Include SSL configuration if applicable""",
    "ansible": """Generate an Ansible playbook for:

{requirement}

Requirements:
- Use YAML format
- Include name, hosts, become, and tasks
- Use idempotent modules
- Include handlers where appropriate""",
    "kubernetes": """Generate Kubernetes manifests for:

{requirement}

Requirements:
- Include Deployment and Service resources
- Set resource requests and limits
- Include health probes
- Use recommended labels""",
    "terraform": """Generate Terraform configuration for:

{requirement}

Requirements:
- Use Terraform >= 1.0 syntax
- Define required providers
- Output relevant information
- Use variables for customization""",
}


def get_generation_prompt(category: str, requirement: str) -> str:
    template = GENERATION_PROMPTS.get(category, GENERATION_PROMPTS["bash"])
    return template.format(requirement=requirement)


def get_automation_system_prompt() -> str:
    return AUTOMATION_SYSTEM_PROMPT
