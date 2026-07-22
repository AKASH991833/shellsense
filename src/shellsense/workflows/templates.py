from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorkflowTemplate:
    name: str
    description: str
    category: str
    triggers: list[str]
    steps: list[str]
    context_requirements: dict[str, object] = field(default_factory=dict)

    def matches_partial(self, partial: str) -> bool:
        for trigger in self.triggers:
            if partial.strip().startswith(trigger):
                return True
        return False

    def find_current_step(self, partial: str) -> int:
        for i, step in enumerate(self.steps):
            base = step.split()[0] if step.split() else ""
            partial_base = partial.split()[0] if partial.split() else ""
            if base and partial_base and partial_base == base:
                return i
        return -1

    def get_next_step(self, partial: str) -> str | None:
        idx = self.find_current_step(partial)
        if idx >= 0 and idx + 1 < len(self.steps):
            return self.steps[idx + 1]
        return None

    def matches_context(self, state: object) -> bool:
        from shellsense.context.state import ShellState

        if not isinstance(state, ShellState):
            return True
        req = self.context_requirements
        if req.get("needs_git") and not state.git_root:
            return False
        if req.get("project_type") and state.project_type != req["project_type"]:
            return False
        if req.get("needs_dockerfile") and not state.has_dockerfile:
            return False
        if req.get("needs_compose") and not state.has_compose:
            return False
        if req.get("needs_kube") and not state.kube_context:
            return False
        if req.get("needs_terraform") and not state.has_terraform:
            return False
        return True


KUBECTL_GET_PODS = WorkflowTemplate(
    name="kubectl-get-pods",
    description="kubectl get pods → logs/describe",
    category="kubernetes",
    triggers=["kubectl get pods", "kubectl get po"],
    steps=[
        "kubectl get pods",
        "kubectl logs -f <pod>",
        "kubectl describe pod <pod>",
    ],
    context_requirements={"needs_kube": True},
)

KUBECTL_GET_DEPLOYMENTS = WorkflowTemplate(
    name="kubectl-get-deployments",
    description="kubectl get deployments → rollout status",
    category="kubernetes",
    triggers=["kubectl get deployments", "kubectl get deploy"],
    steps=[
        "kubectl get deployments",
        "kubectl rollout status deployment/<name>",
        "kubectl describe deployment/<name>",
    ],
    context_requirements={"needs_kube": True},
)

KUBECTL_APPLY = WorkflowTemplate(
    name="kubectl-apply",
    description="kubectl apply → verify pods → logs",
    category="kubernetes",
    triggers=["kubectl apply"],
    steps=[
        "kubectl apply -f <file>",
        "kubectl get pods",
        "kubectl logs -f <pod>",
    ],
    context_requirements={"needs_kube": True},
)

GIT_ADD_COMMIT = WorkflowTemplate(
    name="git-add-commit",
    description="git add → commit → push",
    category="git",
    triggers=["git add"],
    steps=[
        "git add .",
        'git commit -m ""',
        "git push",
    ],
    context_requirements={"needs_git": True},
)

GIT_BRANCH = WorkflowTemplate(
    name="git-branch",
    description="git branch → add → commit → push",
    category="git",
    triggers=["git checkout -b", "git branch"],
    steps=[
        "git checkout -b <branch>",
        "git add .",
        'git commit -m ""',
        "git push -u origin <branch>",
    ],
    context_requirements={"needs_git": True},
)

GIT_PULL_WORKFLOW = WorkflowTemplate(
    name="git-pull",
    description="git pull → rebase or merge",
    category="git",
    triggers=["git pull"],
    steps=[
        "git pull",
        "git log --oneline -5",
    ],
    context_requirements={"needs_git": True},
)

DOCKER_BUILD = WorkflowTemplate(
    name="docker-build",
    description="docker build → run → push",
    category="docker",
    triggers=["docker build"],
    steps=[
        "docker build -t <tag> .",
        "docker run <tag>",
        "docker push <tag>",
    ],
    context_requirements={"needs_dockerfile": True},
)

DOCKER_COMPOSE_UP = WorkflowTemplate(
    name="docker-compose",
    description="docker-compose up → down → logs",
    category="docker",
    triggers=["docker-compose up", "docker compose up"],
    steps=[
        "docker-compose up -d",
        "docker-compose logs -f",
        "docker-compose down",
    ],
    context_requirements={"needs_compose": True},
)

NPM_TEST = WorkflowTemplate(
    name="npm-test",
    description="npm test → build → publish",
    category="node",
    triggers=["npm test", "npm run test"],
    steps=[
        "npm test",
        "npm run build",
        "npm publish",
    ],
    context_requirements={"project_type": "node"},
)

NPM_INSTALL = WorkflowTemplate(
    name="npm-install",
    description="npm install → build → test",
    category="node",
    triggers=["npm install"],
    steps=[
        "npm install <pkg>",
        "npm run build",
        "npm test",
    ],
    context_requirements={"project_type": "node"},
)

YARN_INSTALL = WorkflowTemplate(
    name="yarn-install",
    description="yarn add → build → test",
    category="node",
    triggers=["yarn add", "yarn install"],
    steps=[
        "yarn add <pkg>",
        "yarn build",
        "yarn test",
    ],
    context_requirements={"project_type": "node"},
)

PIP_INSTALL = WorkflowTemplate(
    name="pip-install",
    description="pip install → freeze requirements",
    category="python",
    triggers=["pip install"],
    steps=[
        "pip install <pkg>",
        "pip freeze > requirements.txt",
    ],
    context_requirements={"project_type": "python"},
)

PYTHON_VENV = WorkflowTemplate(
    name="python-venv",
    description="python -m venv → activate → install deps",
    category="python",
    triggers=["python -m venv", "python3 -m venv"],
    steps=[
        "python -m venv venv",
        "source venv/bin/activate",
        "pip install -r requirements.txt",
    ],
    context_requirements={"project_type": "python"},
)

TERRAFORM_PLAN = WorkflowTemplate(
    name="terraform-plan",
    description="terraform fmt → init → plan → apply",
    category="terraform",
    triggers=["terraform plan", "terraform apply"],
    steps=[
        "terraform fmt",
        "terraform init",
        "terraform plan",
        "terraform apply",
    ],
    context_requirements={"needs_terraform": True},
)

SYSTEMCTL = WorkflowTemplate(
    name="systemd-service",
    description="systemctl start → enable → status",
    category="system",
    triggers=[
        "sudo systemctl start",
        "sudo systemctl restart",
        "systemctl start",
        "systemctl restart",
    ],
    steps=[
        "sudo systemctl start <service>",
        "sudo systemctl enable <service>",
        "sudo systemctl status <service>",
    ],
)

SSH_DEPLOY = WorkflowTemplate(
    name="ssh-deploy",
    description="ssh → pull → restart service",
    category="devops",
    triggers=["ssh"],
    steps=[
        "ssh user@host",
        "cd /var/www/<project>",
        "git pull",
        "sudo systemctl restart <service>",
    ],
)

GCLOUD_AUTH = WorkflowTemplate(
    name="gcloud-auth",
    description="gcloud auth → set project → app creds",
    category="gcloud",
    triggers=["gcloud auth login", "gcloud init"],
    steps=[
        "gcloud auth login",
        "gcloud config set project <project>",
        "gcloud auth application-default login",
    ],
)

ALL_TEMPLATES: list[WorkflowTemplate] = [
    KUBECTL_GET_PODS,
    KUBECTL_GET_DEPLOYMENTS,
    KUBECTL_APPLY,
    GIT_ADD_COMMIT,
    GIT_BRANCH,
    GIT_PULL_WORKFLOW,
    DOCKER_BUILD,
    DOCKER_COMPOSE_UP,
    NPM_TEST,
    NPM_INSTALL,
    YARN_INSTALL,
    PIP_INSTALL,
    PYTHON_VENV,
    TERRAFORM_PLAN,
    SYSTEMCTL,
    SSH_DEPLOY,
    GCLOUD_AUTH,
]
