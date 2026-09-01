"""Data model for a generation result."""

from dataclasses import dataclass


@dataclass
class ConversationTurn:
    """One exchange in the conversation history sent to the LLM."""

    role: str     # "user" or "assistant"
    content: str


@dataclass
class GenerationResult:
    """The output of a single generation call.

    Carries the answer text, provenance citations, the model used,
    and token usage so callers can monitor latency and quality.
    """

    answer: str
    query: str
    citations: list[str]
    model: str
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def __repr__(self) -> str:
        return (
            f"GenerationResult(model={self.model!r}, "
            f"tokens={self.total_tokens}, "
            f"citations={len(self.citations)})"
        )
