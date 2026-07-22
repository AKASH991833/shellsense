from __future__ import annotations

from dataclasses import dataclass, field

from shellsense.context.state import ShellState
from shellsense.workflows.templates import ALL_TEMPLATES, WorkflowTemplate


@dataclass
class WorkflowSuggestion:
    name: str
    description: str
    category: str
    suggested_command: str
    workflow_name: str
    step_number: int
    total_steps: int


class WorkflowMatcher:

    def __init__(self) -> None:
        self._templates = ALL_TEMPLATES

    def get_suggestions(
        self,
        partial: str,
        state: ShellState | None = None,
        limit: int = 3,
    ) -> list[WorkflowSuggestion]:
        if not partial:
            return []
        results: list[tuple[int, WorkflowSuggestion]] = []

        for tmpl in self._templates:
            if state is not None and not tmpl.matches_context(state):
                continue
            if not tmpl.matches_partial(partial):
                continue

            next_step = tmpl.get_next_step(partial)
            if next_step:
                idx = tmpl.find_current_step(partial)
                score = self._score_match(tmpl, state, partial)
                results.append(
                    (
                        score,
                        WorkflowSuggestion(
                            name=next_step,
                            description=tmpl.description,
                            category=tmpl.category,
                            suggested_command=next_step,
                            workflow_name=tmpl.name,
                            step_number=idx + 2,
                            total_steps=len(tmpl.steps),
                        ),
                    )
                )

        results.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in results[:limit]]

    def _score_match(
        self,
        tmpl: WorkflowTemplate,
        state: ShellState | None,
        partial: str,
    ) -> int:
        score = 10
        if state is None:
            return score
        if state.project_type == tmpl.category:
            score += 20
        if tmpl.context_requirements.get("needs_git") and state.git_root:
            score += 15
        if tmpl.context_requirements.get("needs_kube") and state.kube_context:
            score += 15
        if tmpl.context_requirements.get("needs_dockerfile") and state.has_dockerfile:
            score += 15
        if state.sudo_mode and "sudo" in " ".join(tmpl.triggers):
            score += 10
        partial_len = len(partial.strip().split())
        if partial_len >= 2:
            for step in tmpl.steps:
                if step.startswith(partial.strip()):
                    score += 25
                    break
        return score
