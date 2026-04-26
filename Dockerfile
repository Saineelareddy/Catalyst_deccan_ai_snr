FROM python:3.12-slim

# Install system dependencies for PyMuPDF
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Add auth dependencies
RUN pip install --no-cache-dir -r requirements.txt passlib[bcrypt] python-jose[cryptography]

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
