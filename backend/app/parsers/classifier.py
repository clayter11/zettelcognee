"""Document classifier — determines document type using Gemini Flash.

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


async def classify_document(content: str) -> DocumentType:
    """Classify document content into a DocumentType.

    Uses Gemini Flash for classification (~$0.001 per document).
    Falls back to GENERAL if classification fails.
    """
    if not settings.llm_api_key:
        return DocumentType.GENERAL

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.llm_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = CLASSIFICATION_PROMPT.format(content=content[:2000])
        response = model.generate_content(prompt)
        result = response.text.strip().lower()

        type_map = {
            "proposal": DocumentType.PROPOSAL,
            "contract": DocumentType.CONTRACT,
            "calculation": DocumentType.CALCULATION,
            "drawing": DocumentType.DRAWING,
            "meeting": DocumentType.MEETING,
            "spreadsheet": DocumentType.SPREADSHEET,
        }
        return type_map.get(result, DocumentType.GENERAL)

    except Exception:
        return DocumentType.GENERAL
