"""Document classifier tests."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from app.models.document import DocumentType


@pytest.fixture(autouse=True)
def mock_genai():
    """Mock google.generativeai to avoid Anaconda import conflicts."""
    mock_module = MagicMock()
    with patch.dict(sys.modules, {"google.generativeai": mock_module}):
        yield mock_module


async def test_classify_fallback_no_api_key():
    """Without API key, classifier returns GENERAL."""
    from app.parsers.classifier import classify_document

    with patch("app.parsers.classifier.settings") as mock_settings:
        mock_settings.llm_api_key = ""
        result = await classify_document("some content")
        assert result == DocumentType.GENERAL


async def test_classify_proposal(mock_genai):
    """Classifier detects commercial proposal."""
    mock_response = MagicMock()
    mock_response.text = "proposal"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response

    from app.parsers.classifier import classify_document

    with patch("app.parsers.classifier.settings") as mock_settings:
        mock_settings.llm_api_key = "test-key"
        result = await classify_document("Коммерческое предложение для ООО Альфа")
        assert result == DocumentType.PROPOSAL


async def test_classify_contract(mock_genai):
    """Classifier detects contract."""
    mock_response = MagicMock()
    mock_response.text = "contract"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response

    from app.parsers.classifier import classify_document

    with patch("app.parsers.classifier.settings") as mock_settings:
        mock_settings.llm_api_key = "test-key"
        result = await classify_document("Договор подряда №123")
        assert result == DocumentType.CONTRACT


async def test_classify_unknown_returns_general(mock_genai):
    """Unknown classification result returns GENERAL."""
    mock_response = MagicMock()
    mock_response.text = "something_unknown"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response

    from app.parsers.classifier import classify_document

    with patch("app.parsers.classifier.settings") as mock_settings:
        mock_settings.llm_api_key = "test-key"
        result = await classify_document("random text")
        assert result == DocumentType.GENERAL
