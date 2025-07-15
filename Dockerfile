# ---------- builder ----------
FROM python:3.14-slim-bookworm AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel -r requirements.txt

# ---------- runtime ----------
FROM python:3.14-slim-bookworm AS runtime
WORKDIR /app
# Copy only wheels and source; no pip cache, no build deps
COPY --from=builder /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]