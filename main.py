import sys
import os

# Add src to path for local development/uv run
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from picpurge.cli import app

if __name__ == "__main__":
    app()
