"""Start local-only HTTP server. Override port with NEXORA_PORT."""
import uvicorn
from .config import port

if __name__ == "__main__":
    uvicorn.run("backend.main:app",host="127.0.0.1",port=port(),access_log=False)
