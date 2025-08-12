# FastAPI entrypoint
# Delegate to server_enhanced app to avoid duplicated route definitions
from server_enhanced import app  # noqa: F401