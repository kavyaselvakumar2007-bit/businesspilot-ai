# Deployment Manual: BusinessPilot AI

This guide contains deployment instructions for hosting BusinessPilot AI locally, via Docker containers, or on Streamlit Community Cloud.

---

## 1. Local Deployment

### Prerequisites
- Python >= 3.10
- Git

### Commands
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/businesspilot-ai.git
cd businesspilot-ai

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
copy .env.example .env

# Run local installation validation checks
python verify_requirements.py

# Launch Streamlit app
streamlit run dashboard/app.py
```

---

## 2. Docker Deployment

### Requirements
- Docker Desktop installed and running
- Docker Compose v2+

### Commands
```bash
# Build the Docker image
docker build -t businesspilot-ai .

# Run the container stand-alone
docker run -p 8501:8501 --env-file .env businesspilot-ai

# Or build and launch with docker-compose (maps persistent volumes)
docker compose up -d

# Verify container status
docker compose ps

# Stop the container
docker compose down
```

### Configured Volumes
Our `docker-compose.yml` mounts four local paths to ensure data persists outside of container lifecycles:
- `./data/reports` ➡️ `/app/data/reports` (PDF/HTML report downloads)
- `./data/history` ➡️ `/app/data/history` (JSON run records)
- `./data/uploads` ➡️ `/app/data/uploads` (Uploaded lead CSV files)
- `./logs` ➡️ `/app/logs` (Debug stdout files)

---

## 3. Streamlit Community Cloud Hosting

1. Push your repository to GitHub.
2. Log in at [share.streamlit.io](https://share.streamlit.io/) with your GitHub profile.
3. Click **New App**, select your branch (`main`), repository, and path (`dashboard/app.py`).
4. Paste your `.env` key-value pairs (like `GEMINI_API_KEY`) into the **Advanced Settings > Secrets** TOML grid.
5. Click **Deploy!**
