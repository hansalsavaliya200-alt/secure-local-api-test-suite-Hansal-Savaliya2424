"""One error shape for every failure: {"error": {"code", "message", "request_id"}}."""
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, headers: dict | None = None):
        self.status, self.code, self.message, self.headers = status, code, message, headers or {}


def error_response(request, status: int, code: str, message: str, headers: dict | None = None, fields=None):
    body = {"error": {"code": code, "message": message, "request_id": getattr(request.state, "request_id", None)}}
    if fields:
        body["error"]["fields"] = fields
    return JSONResponse(status_code=status, content=body, headers=headers)
