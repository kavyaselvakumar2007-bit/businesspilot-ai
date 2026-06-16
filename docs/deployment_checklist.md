# Production Deployment Checklist

This document is a readiness check for local installation, Docker hosting, and Streamlit Community Cloud deployment.

---

## 1. Local Deployment Checklist
- [ ] Python version >= 3.10 installed (`python --version`)
- [ ] Virtual environment created and activated (`python -m venv .venv`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file copied from `.env.example` and configured
- [ ] Required directories exist and are writable (`logs/`, `data/uploads/`, `data/history/`, `data/reports/`)
- [ ] Run validator passes successfully (`python verify_requirements.py`)
- [ ] Test suites compile and pass (`pytest tests/`)

---

## 2. Docker Deployment Checklist
- [ ] Docker Daemon is running locally
- [ ] Image builds without cache errors (`docker build -t businesspilot-ai .`)
- [ ] Environment variables mapping verified in `docker-compose.yml`
- [ ] Local mount volumes configured for state persistence
- [ ] Container runs successfully (`docker compose up -d`)
- [ ] Port `8501` is exposed and accessible from `http://localhost:8501`

---

## 3. Streamlit Community Cloud Checklist
- [ ] Code committed and pushed to a public/private GitHub repository
- [ ] `requirements.txt` is in the repository root
- [ ] `data/sample_leads.csv` is committed as fallback data
- [ ] Streamlit account connected to GitHub profile
- [ ] App created pointing to `dashboard/app.py` on the `main` branch
- [ ] **Advanced Settings > Secrets** configured with:
  ```toml
  GEMINI_API_KEY = "your-api-key"
  # SMTP settings optional
  ```

---

## 4. Environment Variables Checklist
- [ ] `GEMINI_API_KEY`: Verified and loaded (no plain text exposure)
- [ ] `GEMINI_MODEL`: Set (defaults to `gemini-2.5-flash`)
- [ ] `SMTP_SERVER` / `SMTP_PORT`: Configured if utilizing real notifications
- [ ] `SMTP_USER` / `SMTP_PASSWORD`: Loaded securely from host environment

---

## 5. Security Checklist
- [ ] `.env` file is listed in `.gitignore`
- [ ] API keys are never printed in console output or written to logs
- [ ] Sanitization rules in place for uploaded filenames (prevent path traversal)
- [ ] Enforced maximum lead file upload size (5MB maximum)
- [ ] File extension constraint active (strictly reject non-CSV uploads)

---

## 6. Troubleshooting Checklist
- **Issue: "Gemini API: Missing ❌"**
  * Solution: Check that your `.env` contains `GEMINI_API_KEY="your_key"` and is located in the project root folder.
- **Issue: "fpdf2 UnicodeEncodeError"**
  * Solution: Emojis and special unicode symbols crash standard PDF fonts. Ensure the `clean_pdf_text` helper maps or strips emojis before compilation.
- **Issue: "MCP Subprocess Port/Pipe Blocked"**
  * Solution: FastMCP servers communicate over stdio. Check that your system doesn't block standard pipe operations and logs are writable.
