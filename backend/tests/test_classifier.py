"""Document classifier tests."""

from unittest.mock import MagicMock, patch

from app.models.document import DocumentType
from app.parsers.classifier import classify_document


async def test_classify_fallback_no_api_key():
    """Without API key, classifier returns GENERAL."""
    with patch("app.parsers.classifier.settings") as mock_settings:
        mock_settings.anthropic_api_key = ""
        mock_settings.llm_api_key = ""
        result = await classify_document("some content")
        assert result == DocumentType.GENERAL


async def test_classify_proposal():
    """Classifier detects commercial proposal."""
    mock_content = MagicMock()
    mock_content.text = "proposal"
    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.parsers.classifier.settings") as mock_settings, \
         patch("anthropic.Anthropic", return_value=mock_client):
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.llm_api_key = ""
        result = await classify_document("Коммерческое предложение для ООО Альфа")
        assert result == DocumentType.PROPOSAL


async def test_classify_contract():
    """Classifier detects contract."""
    mock_content = MagicMock()
    mock_content.text = "contract"
    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.parsers.classifier.settings") as mock_settings, \
         patch("anthropic.Anthropic", return_value=mock_client):
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.llm_api_key = ""
        result = await classify_document("Договор подряда №123")
        assert result == DocumentType.CONTRACT


async def test_classify_unknown_returns_general():
    """Unknown classification result returns GENERAL."""
    mock_content = MagicMock()
    mock_content.text = "something_unknown"
    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.parsers.classifier.settings") as mock_settings, \
         patch("anthropic.Anthropic", return_value=mock_client):
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.llm_api_key = ""
        result = await classify_document("random text")
        assert result == DocumentType.GENERAL
