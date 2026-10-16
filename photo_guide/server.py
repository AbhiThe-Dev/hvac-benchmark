"""Run the prototype:  .venv/bin/python photo_guide/server.py [--fake]   ->  http://localhost:8745   (phones on the same Wi-Fi: this Mac's address, port 8745)

--fake serves canned answers (no API key, no model call) to exercise the screens only."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn  # noqa: E402

from guide.app import create_app  # noqa: E402
from guide.fake import fake_guidance  # noqa: E402

if __name__ == "__main__":
    fake = "--fake" in sys.argv
    app = create_app(guide_fn=fake_guidance) if fake else create_app()
    uvicorn.run(app, host="0.0.0.0", port=8746 if fake else 8745)
