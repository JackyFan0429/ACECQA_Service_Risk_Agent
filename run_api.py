"""Local entrypoint for Milestone 6 product demo."""

from __future__ import annotations

import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "acecqa_agent.api.main:app",
        host=os.getenv("ACECQA_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ACECQA_RELOAD", "0") == "1",
    )
