"""Root-level server entry point — required by openenv validate."""
import uvicorn
from fundlens.server.app import app


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
