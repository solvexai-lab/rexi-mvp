FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for Docling/PyMuPDF/sentence-transformers
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
    tesseract-ocr tesseract-ocr-eng git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (used by some NLP pipelines)
RUN python -m spacy download en_core_web_sm || true

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
