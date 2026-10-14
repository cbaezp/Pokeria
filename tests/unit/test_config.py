"""Unit tests for configuration validation, focusing on CORS_ORIGINS parsing."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestCorsOriginsValidation:
    """Test suite for CORS_ORIGINS flexible parsing and strict validation."""

    def test_default_cors_origins(self) -> None:
        settings = Settings(_env_file=None)
        assert settings.CORS_ORIGINS == ["http://localhost:3000", "http://127.0.0.1:3000"]

    def test_comma_delimited_cors_origins(self) -> None:
        settings = Settings(
            CORS_ORIGINS="http://localhost:3000, https://pokerlab.dev, http://127.0.0.1:8080"
        )
        assert settings.CORS_ORIGINS == [
            "http://localhost:3000",
            "https://pokerlab.dev",
            "http://127.0.0.1:8080",
        ]

    def test_json_array_cors_origins(self) -> None:
        settings = Settings(CORS_ORIGINS='["http://localhost:3000", "https://pokerlab.dev"]')
        assert settings.CORS_ORIGINS == ["http://localhost:3000", "https://pokerlab.dev"]

    def test_list_input_cors_origins(self) -> None:
        settings = Settings(CORS_ORIGINS=["http://localhost:3000", "https://app.pokerlab.local"])
        assert settings.CORS_ORIGINS == ["http://localhost:3000", "https://app.pokerlab.local"]

    def test_reject_empty_cors_origins(self) -> None:
        with pytest.raises(ValidationError) as exc:
            Settings(CORS_ORIGINS="")
        assert "CORS_ORIGINS cannot be empty" in str(exc.value)

    def test_reject_malformed_json_cors_origins(self) -> None:
        with pytest.raises(ValidationError) as exc:
            Settings(CORS_ORIGINS='["http://localhost:3000", broken_json')
        assert "Malformed JSON in CORS_ORIGINS" in str(exc.value)

    def test_reject_missing_scheme_in_origin(self) -> None:
        with pytest.raises(ValidationError) as exc:
            Settings(CORS_ORIGINS="localhost:3000")
        assert "must have http:// or https:// scheme" in str(exc.value)

    def test_reject_invalid_scheme_in_origin(self) -> None:
        with pytest.raises(ValidationError) as exc:
            Settings(CORS_ORIGINS="ftp://pokerlab.local")
        assert "must have http:// or https:// scheme" in str(exc.value)

    def test_reject_missing_netloc(self) -> None:
        with pytest.raises(ValidationError) as exc:
            Settings(CORS_ORIGINS="http://")
        assert "must specify a valid hostname/port" in str(exc.value)
