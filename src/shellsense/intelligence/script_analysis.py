from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

SECURITY_PATTERNS: list[dict[str, Any]] = [
    {
        "pattern": r"\brm\s+-rf\s+/\s*$",
        "severity": "critical",
        "message": "Recursive force removal of root",
    },
    {
        "pattern": r"\bdd\s+if=.*\s+of=/dev/sd",
        "severity": "critical",
        "message": "Raw disk write",
    },
    {"pattern": r"\bmkfs\b", "severity": "high", "message": "Filesystem creation"},
    {
        "pattern": r"\b>:\)\s*\)\s*\(|:\(\)\s*\{",
        "severity": "critical",
        "message": "Fork bomb detected",
    },
    {
        "pattern": r"\bchmod\s+-R\s+777\s+/",
        "severity": "high",
        "message": "World-writable root permissions",
    },
    {
        "pattern": r"\bcurl\s+.*\s*\|\s*bash\b",
        "severity": "high",
        "message": "Piped curl to shell",
    },
    {
        "pattern": r"\bwget\s+.*\s*-O\s*-\s*\|\s*bash\b",
        "severity": "high",
        "message": "Piped wget to shell",
    },
    {
        "pattern": r"\beval\s",
        "severity": "medium",
        "message": "Use of eval can be dangerous",
    },
    {
        "pattern": r"\bsource\s+.*\$\(.*\)",
        "severity": "medium",
        "message": "Dynamic source path",
    },
    {
        "pattern": r"\bexec\s+\"\$",
        "severity": "medium",
        "message": "Unquoted exec argument",
    },
]


@dataclass
class ScriptAnalysisResult:
    path: str = ""
    content: str = ""
    line_count: int = 0
    complexity: str = "simple"
    potential_bugs: list[str] = field(default_factory=list)
    security_issues: list[dict[str, Any]] = field(default_factory=list)
    performance_improvements: list[str] = field(default_factory=list)
    best_practices: list[str] = field(default_factory=list)
    shebang: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "line_count": self.line_count,
            "complexity": self.complexity,
            "potential_bugs": self.potential_bugs,
            "security_issues": [s["message"] for s in self.security_issues],
            "performance_improvements": self.performance_improvements,
            "best_practices": self.best_practices,
            "shebang": self.shebang,
        }


class ScriptAnalyzer:
    def __init__(self) -> None:
        self._bash_builtins = {
            "cd",
            "echo",
            "exit",
            "export",
            "source",
            "alias",
            "unset",
            "read",
            "shift",
            "declare",
            "local",
            "return",
            "trap",
            "type",
            "ulimit",
            "umask",
            "wait",
            "exec",
            "eval",
            "set",
            "unset",
        }

    def analyze(self, path: str) -> ScriptAnalysisResult:
        result = ScriptAnalysisResult(path=path)

        if not os.path.isfile(path):
            result.potential_bugs.append("File does not exist")
            return result

        try:
            with open(path) as f:
                content = f.read()
        except Exception as e:
            result.potential_bugs.append(f"Cannot read file: {e}")
            return result

        result.content = content
        lines = content.split("\n")
        result.line_count = len(lines)

        if lines:
            first_line = lines[0].strip()
            if first_line.startswith("#!"):
                result.shebang = first_line

        result.complexity = self._assess_complexity(lines)
        result.potential_bugs = self._find_bugs(lines)
        result.security_issues = self._find_security_issues(content)
        result.performance_improvements = self._find_performance_improvements(lines)
        result.best_practices = self._find_best_practices(lines)

        return result

    def _assess_complexity(self, lines: list[str]) -> str:
        non_empty = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        if len(non_empty) > 200:
            return "complex"
        if len(non_empty) > 50:
            return "moderate"
        if any("for " in l or "while " in l or "case " in l for l in lines):
            if len(non_empty) > 20:
                return "moderate"
        return "simple"

    def _find_bugs(self, lines: list[str]) -> list[str]:
        bugs: list[str] = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "" or stripped.startswith("#"):
                continue

            if "`" in stripped and "$(" in stripped:
                bugs.append(
                    f"Line {i}: Mixing backticks with $() - use $() consistently"
                )

            if re.search(r"\[\[.*&&.*\]\]", stripped):
                bugs.append(f"Line {i}: Possible logic error in [[ ]] with &&")

            if re.search(r"\$\[.*\]", stripped):
                bugs.append(f"Line {i}: Deprecated $[] arithmetic. Use $(( )) instead")

            if "rm " in stripped and not stripped.startswith("#"):
                if re.search(r"\$\{?\w*\}?\s*/\s*$", stripped):
                    bugs.append(f"Line {i}: Possible empty variable in rm path")

        return bugs

    def _find_security_issues(self, content: str) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        for pattern in SECURITY_PATTERNS:
            if re.search(pattern["pattern"], content, re.MULTILINE):
                issues.append(
                    {
                        "pattern": pattern["pattern"],
                        "severity": pattern["severity"],
                        "message": pattern["message"],
                    }
                )
        return issues

    def _find_performance_improvements(self, lines: list[str]) -> list[str]:
        improvements: list[str] = []
        has_loop = False
        has_pipe_to_while = False
        for line in lines:
            if re.search(r"\bfor\s+\w+\s+in\s+\$\(.*cat\b", line):
                improvements.append(
                    "Use input redirection instead of `cat` in for loop"
                )
            if re.search(r"\bgrep\b.*\|\s*\bgrep\b", line):
                improvements.append(
                    "Multiple grep pipes can often be combined with regex"
                )
            if re.search(r"\bcat\b.*\s*\|\s*\bgrep\b", line):
                improvements.append("Replace `cat file | grep` with `grep file`")
            if re.search(r"\bsed\b.*\|\s*\bsed\b", line):
                improvements.append("Multiple sed invocations can be combined with -e")
            if "while" in line and "read" in line and "|" in line:
                has_pipe_to_while = True
            if "for " in line or "while " in line:
                has_loop = True
        if has_pipe_to_while:
            improvements.append(
                "Consider using process substitution instead of pipe to while-read"
            )
        if has_loop and any("grep" in l or "awk" in l or "sed" in l for l in lines):
            improvements.append("Move grep/awk/sed outside loops when possible")
        return improvements

    def _find_best_practices(self, lines: list[str]) -> list[str]:
        practices: list[str] = []
        has_quotes_check = False
        has_exit_check = False
        has_set_e = False
        has_shebang = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if i == 0 and stripped.startswith("#!"):
                has_shebang = True
            if "set -e" in stripped or "set -o errexit" in stripped:
                has_set_e = True
            if re.search(r'\$\{?\w+\}?"', stripped) or '"$' in stripped:
                has_quotes_check = True
            if re.search(r"\btrap\b", stripped):
                has_exit_check = True

        if not has_shebang:
            practices.append("Add a shebang (#!) line for script type")
        if not has_set_e:
            practices.append("Consider `set -e` to exit on errors")
        if not has_quotes_check:
            practices.append("Always quote variables to prevent word-splitting")
        if not has_exit_check:
            practices.append("Consider adding a trap handler for cleanup")
        if not any("#!/usr/bin/env" in l for l in lines if l.strip().startswith("#!")):
            if has_shebang:
                practices.append("Use `#!/usr/bin/env bash` for better portability")

        variables = set()
        for line in lines:
            for m in re.finditer(r"^([a-zA-Z_]\w*)=", line):
                variables.add(m.group(1))
        uppercase_vars = [v for v in variables if v.isupper()]
        lowercase_vars = [v for v in variables if v.islower()]
        if lowercase_vars:
            practices.append(
                "Use UPPERCASE for exported/environment variables, lowercase for locals"
            )

        return practices


def analyze_script(path: str) -> ScriptAnalysisResult:
    analyzer = ScriptAnalyzer()
    return analyzer.analyze(path)
