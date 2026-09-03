"""Application errors shared across ports and infrastructure adapters."""


class InvalidRequestError(ValueError):
    """Raised when a use-case argument violates an application invariant."""


class AIProviderError(RuntimeError):
    """Base error that prevents provider SDK types leaking across a port."""


class AIProviderUnavailableError(AIProviderError):
    """Raised when an AI provider cannot complete a valid request."""


class AIProviderResponseError(AIProviderError):
    """Raised when a provider returns an unusable or invalid response."""


class AIProviderInputError(AIProviderError, ValueError):
    """Raised when input cannot fit within the provider contract."""


class InvalidGeneratedAnswerError(RuntimeError):
    """Raised when a generated answer violates the grounding contract."""


class DocumentAlreadyExistsError(RuntimeError):
    """Raised when concurrent ingestion wins the content-hash race."""
