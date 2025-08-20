# 📄 PDF Analyzer Backend

## Overview

The **PDF Analyzer Backend** is a robust FastAPI-based service for:
- Secure PDF upload and persistent storage
- Text extraction (with OCR fallback for scanned/image PDFs)
- Summarization and comparison using LLMs (e.g., OpenAI)
- Token/cost tracking for LLM usage
- API key authentication and CORS
- Automated testing and CI/CD
- Dockerized deployment

---

## ✨ Features
- Upload and store PDF files securely
- Extract text from PDFs (including scanned/image-based via OCR)
- Summarize and compare PDFs using LLMs
- Track LLM token usage and estimated cost
- API key authentication for all endpoints
- CORS support for frontend integration
- Environment variable management with `.env`
- Docker and Docker Compose support
- Automated tests and GitHub Actions CI

---

## 📂 Directory Structure
```
pdf_analyzer_backend/
├── app/
│   ├── main.py
│   ├── routers/
│   │   └── pdf_router.py
│   ├── services/
│   │   └── pdf_service.py
│   ├── utils/
│   │   └── llm_client.py
│   └── ...
├── tests/
│   └── test_health.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

1. **Clone the repo and install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
2. **Set up your `.env` file:**
    - Copy `.env.example` to `.env` and fill in your secrets/config.
3. **Run locally:**
    ```sh
    uvicorn app.main:app --reload
    ```
4. **Or run with Docker Compose:**
    ```sh
    docker-compose up --build
    ```
5. **Access the API docs:**
    - Visit [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing
- Run all tests:
    ```sh
    pytest
    ```

---

## 🔒 Security
- All endpoints require an `X-API-Key` header (see `.env.example`).
- CORS is enabled for all origins by default (restrict in production).
- Secrets and config are managed via `.env` (never commit real secrets).

---

## 🐳 Deployment
- Use the provided `Dockerfile` and `docker-compose.yml` for containerized deployment.
- The app is production-ready and CI/CD enabled via GitHub Actions.

---

## 🤝 Contributions
Contributions are welcome! Please open issues or pull requests for improvements or bug fixes.

---

## 📝 License
MIT License (or your preferred license).
# 📄 PDF Analyzer Backend

## Overview

The **PDF Analyzer Backend** is a FastAPI-based service for:
- Accepting PDF uploads
- Extracting text from PDFs
- Summarizing content using an LLM (OpenAI API)
- Returning a summarized output as JSON

This backend is designed for integration with a frontend (e.g., built with [v0.dev](https://v0.dev/)) to allow users to upload PDFs and view generated summaries.

---

## ✨ Features

- Upload PDF files via HTTP API
- Extract text from PDFs
- Summarize text via OpenAI API
- Configurable chunk size, retry attempts, and timeout limits
- Environment-based configuration for security

---

## 📂 Directory Structure

```
pdf_analyzer_backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   └── pdf_model.py
│   ├── routers/
│   │   └── pdf_router.py
│   ├── services/
│   │   └── pdf_service.py
│   └── utils/
│       └── llm_client.py
│
├── requirements.txt
├── test_pdf_upload.py
├── README.md
└── .gitignore
```

---

## 🚀 Quick Start

1. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

2. **Run the FastAPI server:**
    ```sh
    uvicorn app.main:app --reload
    ```

3. **Test PDF upload:**
    - Use the provided `test_pdf_upload.py` script or a tool like Postman to POST a PDF to `/upload-pdf/`.

---

## 🧪 Testing

- Run `test_pdf_upload.py` to manually test the PDF upload and summarization endpoint.

---

## 🗑️ .gitignore

See below for recommended `.gitignore` contents.

---

## 📝 License

MIT License (add your own license as needed).
