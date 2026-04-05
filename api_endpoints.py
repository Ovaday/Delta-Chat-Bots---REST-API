import cgi
import hmac
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from config import API_KEY, MEDIA_DIR
from outbound_requests import to_jsonable


def make_handler(bot):
    class ApiHandler(BaseHTTPRequestHandler):
        rpc = bot.rpc

        def log_message(self, format: str, *args) -> None:
            bot.logger.info("REST API: " + format, *args)

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON body: {exc.msg}") from exc
            if not isinstance(data, dict):
                raise ValueError("JSON body must be an object")
            return data

        def _get_media_dir(self) -> Path:
            media_dir_path = Path(MEDIA_DIR)
            media_dir_path.mkdir(parents=True, exist_ok=True)
            return media_dir_path

        def _sanitize_media_name(self, raw_name: str) -> str:
            return Path(raw_name).name

        def _get_media_file_path(self, name: str) -> Path:
            safe_name = self._sanitize_media_name(name)
            return self._get_media_dir() / safe_name

        def _get_query_param(self, key: str) -> str | None:
            params = parse_qs(urlparse(self.path).query)
            values = params.get(key)
            return values[0] if values else None

        def _read_multipart(self):
            return cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                    "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
                },
                keep_blank_values=True,
            )

        def _handle_media_upload(self) -> None:
            form = self._read_multipart()
            if "file" not in form:
                raise ValueError("missing file field")

            file_field = form["file"]
            if isinstance(file_field, list):
                file_field = file_field[0]
            if not file_field.file:
                raise ValueError("invalid uploaded file")

            # Check for custom filename field, otherwise use the file's filename
            filename_field = form.get("filename")
            if filename_field and filename_field.value:
                file_name = self._sanitize_media_name(filename_field.value)
            elif file_field.filename:
                file_name = self._sanitize_media_name(file_field.filename)
            else:
                raise ValueError("uploaded file must include filename or filename field")

            target_path = self._get_media_file_path(file_name)
            target_path.write_bytes(file_field.file.read())

            self._send_json(
                HTTPStatus.CREATED,
                {
                    "status": "created",
                    "name": file_name,
                },
            )

        def _handle_media_delete(self) -> None:
            file_name = self._get_query_param("name")
            if not file_name:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "bad_request",
                        "detail": "missing required query parameter: name",
                    },
                )
                return

            target_path = self._get_media_file_path(file_name)
            if not target_path.exists():
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {
                        "error": "not_found",
                        "detail": f"media file not found: {file_name}",
                    },
                )
                return

            target_path.unlink()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "deleted",
                    "name": file_name,
                },
            )

        def _is_authorized(self) -> bool:
            provided_key = self.headers.get("X-API-Key", "")
            if not provided_key:
                auth_header = self.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    provided_key = auth_header[7:]
            return bool(API_KEY) and hmac.compare_digest(provided_key, API_KEY)

        def _require_api_key(self) -> bool:
            if self._is_authorized():
                return True
            self._send_json(
                HTTPStatus.UNAUTHORIZED,
                {
                    "error": "unauthorized",
                    "detail": "missing or invalid API key",
                },
            )
            return False

        def do_GET(self) -> None:
            if not self._require_api_key():
                return
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            if path == "/health":
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return

            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": "not_found", "detail": f"unknown endpoint: {path}"},
            )

        def do_POST(self) -> None:
            if not self._require_api_key():
                return
            path = urlparse(self.path).path.rstrip("/") or "/"
            if path == "/media":
                try:
                    self._handle_media_upload()
                except ValueError as exc:
                    self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"error": "bad_request", "detail": str(exc)},
                    )
                except Exception as exc:
                    self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        {"error": "server_error", "detail": str(exc)},
                    )
                return
            if path != "/rpc":
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {"error": "not_found", "detail": f"unknown endpoint: {path}"},
                )
                return

            try:
                payload = self._read_json()
                method = payload["method"]
                params = payload.get("params", [])
            except KeyError as exc:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "bad_request",
                        "detail": f"missing required field: {exc.args[0]}",
                    },
                )
                return
            except (TypeError, ValueError) as exc:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "bad_request", "detail": str(exc)},
                )
                return

            if not isinstance(method, str) or not method or method.startswith("_"):
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "bad_request", "detail": "method must be a public RPC method name"},
                )
                return
            if not isinstance(params, list):
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "bad_request", "detail": "params must be an array"},
                )
                return

            try:
                result = self.rpc.transport.call(method, *params)
            except Exception as exc:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {
                        "error": "rpc_failed",
                        "method": method,
                        "params": to_jsonable(params),
                        "detail": str(exc),
                    },
                )
                return

            self._send_json(
                HTTPStatus.OK,
                {
                    "method": method,
                    "params": to_jsonable(params),
                    "result": to_jsonable(result),
                },
            )

        def do_DELETE(self) -> None:
            if not self._require_api_key():
                return
            path = urlparse(self.path).path.rstrip("/") or "/"
            if path == "/media":
                self._handle_media_delete()
                return

            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": "not_found", "detail": f"unknown endpoint: {path}"},
            )

    return ApiHandler
