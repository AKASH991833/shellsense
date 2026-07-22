class ShellSenseError(Exception):
    """Base exception for all ShellSense AI errors."""


class ConfigurationError(ShellSenseError):
    """Raised when there is a configuration-related error."""


class DatabaseError(ShellSenseError):
    """Raised when there is a database-related error."""


class PlatformError(ShellSenseError):
    """Raised when there is a platform compatibility error."""


class CLIError(ShellSenseError):
    """Raised when there is a CLI invocation error."""


class FileOperationError(ShellSenseError):
    """Raised when a file operation fails."""


class InitializationError(ShellSenseError):
    """Raised when the application fails to initialize."""


class KnowledgeError(ShellSenseError):
    """Raised when there is a knowledge engine error."""


class CommandNotFoundError(KnowledgeError):
    """Raised when a command is not found in the knowledge base."""


class SearchError(KnowledgeError):
    """Raised when a search operation fails."""


class CategoryNotFoundError(KnowledgeError):
    """Raised when a category is not found."""


class ShellError(ShellSenseError):
    """Raised when there is a shell integration error."""


class ShellNotSupportedError(ShellError):
    """Raised when the shell is not supported."""


class InstallationError(ShellError):
    """Raised when shell integration installation fails."""


class UninstallationError(ShellError):
    """Raised when shell integration uninstallation fails."""


class DiagnosticError(ShellError):
    """Raised when a diagnostic check fails."""


class AIError(ShellSenseError):
    """Base exception for AI subsystem errors."""


class AIProviderError(AIError):
    """Raised when an AI provider operation fails."""


class AIAuthenticationError(AIError):
    """Raised when AI provider authentication fails."""


class AIQuotaExceededError(AIProviderError):
    """Raised when API quota is exceeded."""


class AIRateLimitError(AIProviderError):
    """Raised when rate limit is hit."""


class AIModelNotFoundError(AIProviderError):
    """Raised when a model is not found."""


class AIStreamingError(AIError):
    """Raised when streaming fails."""


class AIConfigurationError(AIError):
    """Raised when AI configuration is invalid."""
