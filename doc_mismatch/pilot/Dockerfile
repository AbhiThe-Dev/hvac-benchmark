# Build context MUST be doc_mismatch/ (one level above this file), not doc_mismatch/pilot/ -- this image
# needs both the reasoning engine (../src) and the pilot app itself, and Docker can't COPY from outside
# its build context. That's why fly.toml lives at doc_mismatch/fly.toml (not pilot/fly.toml): `fly deploy`
# uses the directory holding fly.toml as the build context.
FROM python:3.12-slim

WORKDIR /app

COPY pilot/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY pilot ./pilot

# stay at /app (not /app/pilot): pilot/*.py use relative imports ("from . import config"), so it must be
# run as the package `pilot.app`, the same way it's run locally (`cd doc_mismatch && uvicorn pilot.app:app`).
EXPOSE 8080
CMD ["uvicorn", "pilot.app:app", "--host", "0.0.0.0", "--port", "8080"]
