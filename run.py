"""
Nyaya Pramaan - Application Runner
Starts the FastAPI application with Uvicorn.
Usage:
    python run.py [--host 0.0.0.0] [--port 8000] [--reload]
"""

import sys
import os
import argparse
import uvicorn

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.db import init_db
from backend.seed_data import seed_database

def main():
    parser = argparse.ArgumentParser(description="Nyaya Pramaan - Judicial Quote Verification Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    # Ensure database is seeded
    print("Initializing Nyaya Pramaan database and authentic judgment records...")
    init_db()
    seed_database()

    print(f"\n=======================================================")
    print(f"  NYAYA PRAMAAN (न्याय प्रमाण) SERVER STARTING")
    print(f"  URL: http://{args.host}:{args.port}")
    print(f"  Docs: http://{args.host}:{args.port}/docs")
    print(f"=======================================================\n")

    uvicorn.run("backend.main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()
