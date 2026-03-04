"""Document classifier — determines document type using Claude.

Classifies incoming documents into types (proposal, contract, calculation,
drawing, meeting, spreadsheet, general) to route through type-specific
DataPoints for better structured extraction.
"""

from app.config import settings
from app.models.document import DocumentType

CLASSIFICATION_PROMPT = """Classify this document into ONE of these categories:
- proposal: коммерческое предложение, КП, оферта
- contract: договор, контракт, соглашение, дополнительное соглашение
- calculation: расчёт, смета, калькуляция, ТЭО
- drawing: чертёж, схема, план, проект (графический)
- meeting: протокол встречи, запись совещания, минутки
- spreadsheet: таблица, реестр, список, перечень
- general: всё остальное

Document content (first 2000 chars):
{content}

Reply with ONLY the category name, nothing else."""

TYPE_MAP = {
    "proposal": DocumentType.PROPOSAL,
    "contract": DocumentType.CONTRACT,
    "calculation": DocumentType.CALCULATION,
    "drawing": DocumentType.DRAWING,
    "meeting": DocumentType.MEETING,
    "spreadsheet": DocumentType.SPREADSHEET,
}


async def classify_document(content: str) -> DocumentType:
    """Classify document content into a DocumentType.

    Uses Claude Haiku for classification (fast + cheap).
    Falls back to GENERAL if classification fails.
    """
    api_key = settings.anthropic_api_key or settings.llm_api_key
    if not api_key:
        return DocumentType.GENERAL

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        prompt = CLASSIFICATION_PROMPT.format(content=content[:2000])

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}],
        )
        result = message.content[0].text.strip().lower()
        return TYPE_MAP.get(result, DocumentType.GENERAL)

    except Exception:
        return DocumentType.GENERAL
