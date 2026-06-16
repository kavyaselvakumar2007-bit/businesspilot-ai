# Streamlit Community Cloud Deployment Guide

This guide describes how to deploy BusinessPilot AI publicly on Streamlit Community Cloud.

---

## 1. Prerequisites & GitHub Preparation

1. **Push Code to GitHub**: Follow the [GitHub Portfolio Guide](./github_publish_guide.md) to initialize your repository and push to GitHub.
2. **Verify Repository Structure**: Ensure your repository root has these key directories and files:
   ```text
   ├── dashboard/
   │   └── app.py
   ├── data/
   │   └── sample_leads.csv
   ├── requirements.txt
   └── .gitignore
   ```

---

## 2. Secrets Configuration

Streamlit Community Cloud hosts apps in public environments, so API keys must not be hardcoded or committed to git.

1. In your Streamlit Cloud Dashboard, go to your app settings.
2. Navigate to the **Secrets** section.
3. Add your secrets in TOML format:
   ```toml
   GEMINI_API_KEY = "AIzaSy..."
   
   # Optional: Configure SMTP settings for real notification emails
   SMTP_SERVER = "smtp.gmail.com"
   SMTP_PORT = "587"
   SMTP_USER = "your-email@gmail.com"
   SMTP_PASSWORD = "your-app-password"
   ```

The Streamlit runtime automatically injects these values into `os.environ` so `python-dotenv` and our configurations load them seamlessly.

---

## 3. Step-by-Step Deployment

1. Visit [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **New App** in the upper right.
3. Select your repository (`YOUR_USERNAME/businesspilot-ai`), branch (`main`), and main file path:
   `dashboard/app.py`
4. Click **Advanced Settings** if you need to configure the python version (choose Python 3.10 or higher).
5. Click **Deploy!**

Your application will boot, install requirements, and go live.

---

## 4. Troubleshooting Cloud Issues

- **Issue: App fails to start with ModuleNotFoundError**:
  * Solution: Double check that all required packages (e.g. `google-genai`, `mcp`, `fpdf2`) are listed in `requirements.txt` in the root folder.
- **Issue: FileNotWritable / FileNotFoundError**:
  * Solution: Streamlit Community Cloud has a read-only filesystem except for the `/tmp` folder. However, BusinessPilot AI automatically runs permissions tests on local directories and creates folders. Ensure that directories `data/uploads`, `data/history`, and `data/reports` are resolved using paths relative to the current file workspace.
- **Issue: Subprocess / Port failures**:
  * Solution: Streamlit Community Cloud supports standard OS subprocess spawning. Our FastMCP servers launch on dynamic standard output/input (`stdio`) pipes and do not bind to system ports, preventing port collisions on shared host environments.
