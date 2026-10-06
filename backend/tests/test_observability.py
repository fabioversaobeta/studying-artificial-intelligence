import json
import logging
import sys
import types

import pytest
from fastapi.testclient import TestClient

from app.core import logging as app_logging
from app.core.logging import JsonFormatter, RequestIdFilter, init_sentry, request_id_var


class TestRequestIdMiddleware:
    def test_response_has_generated_request_id(self, client: TestClient):
        response = client.get("/health")
        assert len(response.headers["X-Request-ID"]) >= 16

    def test_incoming_id_is_propagated(self, client: TestClient):
        response = client.get("/health", headers={"X-Request-ID": "abc-123.XYZ_9"})
        assert response.headers["X-Request-ID"] == "abc-123.XYZ_9"

    @pytest.mark.parametrize("bad", ["has space", "x" * 65, "semi;colon", "new\tline"])
    def test_invalid_incoming_id_is_replaced(self, client: TestClient, bad: str):
        response = client.get("/health", headers={"X-Request-ID": bad})
        assert response.headers["X-Request-ID"] != bad
        assert response.headers["X-Request-ID"]

    def test_ids_differ_between_requests(self, client: TestClient):
        a = client.get("/health").headers["X-Request-ID"]
        b = client.get("/health").headers["X-Request-ID"]
        assert a != b

    def test_error_responses_also_carry_the_header(self, client: TestClient):
        response = client.get("/does-not-exist")
        assert response.status_code == 404
        assert "X-Request-ID" in response.headers


class TestAccessLog:
    def test_access_log_has_method_path_status_duration_and_request_id(
        self, client: TestClient, caplog: pytest.LogCaptureFixture
    ):
        with caplog.at_level(logging.INFO, logger="app.access"):
            response = client.get("/health", headers={"X-Request-ID": "rid-1"})
        records = [r for r in caplog.records if r.name == "app.access"]
        assert len(records) == 1
        message = records[0].getMessage()
        assert "GET /health -> 200" in message
        assert " ms)" in message
        # The filter runs on handlers, so check the contextvar-based path via formatter.
        assert response.headers["X-Request-ID"] == "rid-1"

    def test_request_id_context_is_reset_after_request(self, client: TestClient):
        client.get("/health")
        assert request_id_var.get() is None


class TestLogFormatting:
    def _record(self, msg: str = "hello %s") -> logging.LogRecord:
        return logging.LogRecord("my.logger", logging.WARNING, __file__, 1, msg, ("w",), None)

    def test_filter_injects_request_id(self):
        token = request_id_var.set("rid-xyz")
        try:
            record = self._record()
            assert RequestIdFilter().filter(record)
            assert record.request_id == "rid-xyz"  # type: ignore[attr-defined]
        finally:
            request_id_var.reset(token)

    def test_filter_uses_dash_outside_a_request(self):
        record = self._record()
        RequestIdFilter().filter(record)
        assert record.request_id == "-"  # type: ignore[attr-defined]

    def test_json_formatter_fields(self):
        token = request_id_var.set("rid-json")
        try:
            record = self._record()
            RequestIdFilter().filter(record)
            data = json.loads(JsonFormatter().format(record))
        finally:
            request_id_var.reset(token)
        assert set(data) == {"timestamp", "level", "logger", "message", "request_id"}
        assert data["level"] == "WARNING"
        assert data["logger"] == "my.logger"
        assert data["message"] == "hello w"
        assert data["request_id"] == "rid-json"

    def test_json_formatter_null_request_id_and_exception(self):
        try:
            raise ValueError("boom")
        except ValueError:
            record = logging.LogRecord(
                "l", logging.ERROR, __file__, 1, "failed", (), sys.exc_info()
            )
        RequestIdFilter().filter(record)
        data = json.loads(JsonFormatter().format(record))
        assert data["request_id"] is None
        assert "ValueError: boom" in data["exception"]

    def test_configure_logging_selects_formatter_and_is_idempotent(self):
        root = logging.getLogger()
        saved_handlers, saved_level = list(root.handlers), root.level
        try:
            app_logging.configure_logging("DEBUG", "json")
            app_logging.configure_logging("DEBUG", "json")
            ours = [h for h in root.handlers if isinstance(h, app_logging._AppHandler)]
            assert len(ours) == 1
            assert isinstance(ours[0].formatter, JsonFormatter)
            assert root.level == logging.DEBUG
            app_logging.configure_logging("INFO", "text")
            ours = [h for h in root.handlers if isinstance(h, app_logging._AppHandler)]
            assert len(ours) == 1
            assert not isinstance(ours[0].formatter, JsonFormatter)
        finally:
            root.handlers[:] = saved_handlers
            root.setLevel(saved_level)


class TestSentry:
    def test_skipped_without_dsn(self, monkeypatch: pytest.MonkeyPatch):
        fake = types.SimpleNamespace(init=lambda **kw: pytest.fail("must not be called"))
        monkeypatch.setitem(sys.modules, "sentry_sdk", fake)
        assert init_sentry(None, "test") is False
        assert init_sentry("", "test") is False

    def test_init_called_with_dsn(self, monkeypatch: pytest.MonkeyPatch):
        calls: list[dict] = []
        fake = types.SimpleNamespace(init=lambda **kw: calls.append(kw))
        monkeypatch.setitem(sys.modules, "sentry_sdk", fake)
        assert init_sentry("https://key@example.invalid/1", "production") is True
        assert calls == [
            {
                "dsn": "https://key@example.invalid/1",
                "environment": "production",
                "send_default_pii": False,
            }
        ]

    def test_missing_package_does_not_crash(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setitem(sys.modules, "sentry_sdk", None)  # import raises ImportError
        assert init_sentry("https://key@example.invalid/1", "test") is False
