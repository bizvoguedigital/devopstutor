# Ops Mentor AI - Setup Guide

This guide will walk you through setting up your cloud-powered DevOps interview practice system.

## Prerequisites

Before you begin, ensure you have the following installed:

### System Requirements
- **Windows 10/11** or **Linux (Ubuntu 20.04+, Debian 11+, or equivalent)**
- **8GB RAM** (minimum 4GB)
- **5GB free disk space**
- **Modern CPU** (Intel i5/AMD Ryzen 5 or equivalent)
- **Internet connection** for Groq API

### Software Requirements

**For All Platforms:**
- **Docker Desktop** ([Download](https://www.docker.com/products/docker-desktop/))
- **Git** ([Download](https://git-scm.com/downloads))

**Manual Setup Only (No Docker):**
- **Python 3.10 or higher** ([Download](https://www.python.org/downloads/))
- **Node.js 18 or higher** ([Download](https://nodejs.org/))

**Ubuntu/Debian Additional Setup:**
```bash
# Update package list
sudo apt update

# Install Python and development tools
sudo apt install python3 python3-pip python3-venv python3-dev

# Install Node.js (if not already installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Git (if not already installed)
sudo apt install git

# Install build essentials for some Python packages
sudo apt install build-essential

# Install audio/media dependencies
sudo apt install ffmpeg portaudio19-dev

# Optional: Install curl for API testing
sudo apt install curl
```

## Step 1: Get Groq API Key

Groq provides lightning-fast LLM inference in the cloud.

### Sign up for Groq

1. **Visit Groq Console**: Go to https://console.groq.com/
2. **Create Account**: Sign up with your email
3. **Generate API Key**: 
   - Click on "API Keys" in the sidebar
   - Click "Create API Key"
   - Give it a name like "Ops Mentor AI"
   - Copy the generated key (starts with `gsk_`)

### Setup Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Navigate to backend directory
cd backend

# Create .env file (Windows)
echo "GROQ_API_KEY=your_actual_api_key_here" > .env
echo "MONGODB_URI=mongodb://localhost:27017/ops_mentor_ai" >> .env
echo "MONGODB_DB_NAME=ops_mentor_ai" >> .env

# Create .env file (Linux/macOS)
echo "GROQ_API_KEY=your_actual_api_key_here" > .env
echo "MONGODB_URI=mongodb://localhost:27017/ops_mentor_ai" >> .env
echo "MONGODB_DB_NAME=ops_mentor_ai" >> .env
```

**Important**: Replace `your_actual_api_key_here` with your real Groq API key.

⚠️ **Security Note**: The `.env` file is automatically ignored by git to keep your API key secure.

## Step 2: Clone or Extract the Project

If you haven't already, navigate to the project directory:

**Windows:**
```bash
cd Documents\BoniAI\ops-mentor-ai
```

**Linux/Ubuntu:**
```bash
cd ~/Documents/BoniAI/ops-mentor-ai
# Or wherever you extracted/cloned the project
```

## Step 3: Run with Docker (Recommended)

```bash
docker compose up --build
```

## Step 4: Access the Application

1. Open your web browser
2. Navigate to: **http://localhost:5173**
3. API docs: **http://localhost:8000/docs**

---

## Manual Setup (No Docker)

### Backend Setup

### 3.1 Create Python Virtual Environment

Open a terminal/command prompt and navigate to the backend folder:

```bash
cd backend
python -m venv venv
```

### 3.2 Activate Virtual Environment

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**Linux/Ubuntu/macOS (Bash/Zsh):**
```bash
source venv/bin/activate
```

You should see `(venv)` appear in your terminal prompt.

### 3.3 Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install FastAPI, Groq client, Whisper, and other dependencies.

### 3.4 Configure Environment Variables (Optional)

If you want to customize settings:

```bash
copy .env.example .env
```

Then edit `.env` with your preferred settings.

### 3.5 Start the Backend Server

```bash
python main.py
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Keep this terminal window open!**

### Frontend Setup

Open a **NEW** terminal/command prompt window.

### 4.1 Navigate to Frontend Folder

```bash
cd Documents\BoniAI\ops-mentor-ai\frontend
```

### 4.2 Install Node Dependencies

```bash
npm install
```

This will install React, Vite, TailwindCSS, and other dependencies.

### 4.3 Start the Development Server

```bash
npm run dev
```

You should see output like:
```
  VITE v5.1.0  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Access the Application

1. Open your web browser
2. Navigate to: **http://localhost:5173**
3. You should see the DevOps Interview AI interface!

## Troubleshooting

### Pre-Push Validation (Recommended)

Enable automatic pre-push checks once (per clone):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-hooks.ps1
```

```bash
bash ./scripts/install-hooks.sh
```

Before pushing to `main`, run the standard validation script from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepush-check.ps1
```

```bash
bash ./scripts/prepush-check.sh
```

What it runs:
- backend test suite (`docker compose exec backend pytest -q`)
- frontend production build (`npm run build`)

Optional flags:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepush-check.ps1 -SkipBackendTests
powershell -ExecutionPolicy Bypass -File .\scripts\prepush-check.ps1 -SkipFrontendBuild
```

```bash
bash ./scripts/prepush-check.sh --skip-backend-tests
bash ./scripts/prepush-check.sh --skip-frontend-build
```

### Issue: PowerShell Execution Policy Error (Windows)

**Error message:**
```
venv\Scripts\activate : File cannot be loaded because running scripts is disabled on this system.
CategoryInfo : SecurityError: (:) [], PSSecurityException
FullyQualifiedErrorId : UnauthorizedAccess
```

**Solution:**

1. **Check your current execution policy:**
   ```powershell
   Get-ExecutionPolicy -List
   ```
   
2. **Set the execution policy for the current user:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
   ```

3. **Verify the change worked:**
   ```powershell
   Get-ExecutionPolicy -List
   ```
   You should now see `CurrentUser` set to `RemoteSigned`

4. **Try activating the virtual environment again:**
   ```powershell
   venv\Scripts\Activate.ps1
   ```

**Alternative solutions if the above doesn't work:**

- Use the full path: `& .\venv\Scripts\Activate.ps1`
- Use Command Prompt instead: `venv\Scripts\activate.bat`
- Use the bypass flag: `powershell -ExecutionPolicy Bypass -File .\venv\Scripts\Activate.ps1`

**What this setting does:**
- `RemoteSigned` allows locally created scripts to run without signing
- `CurrentUser` scope only affects your user account (safer than system-wide changes)
- This is a one-time setup per Windows user account

### Issue: Groq API Connection Error

**Error symptoms:**
- "Cannot connect to LLM service"
- "Invalid API key"
- Connection timeout errors

**Solution:**

1. **Check API key in backend/.env file:**
   ```bash
   cat backend/.env
   # Should show: GROQ_API_KEY=gsk_...
   ```

2. **Test API key manually:**
   ```bash
   curl -H "Authorization: Bearer gsk_your_key_here" https://api.groq.com/openai/v1/models
   ```

3. **Check internet connection:**
   ```bash
   ping api.groq.com
   ```

4. **Verify API key is valid:**
   - Check Groq Console: https://console.groq.com/
   - Make sure API key hasn't expired
   - Try generating a new API key if needed

### Issue: "Cannot connect to LLM service"

**Solution:**
- Check your internet connection
- Verify GROQ_API_KEY is set correctly in .env file
- Try restarting the backend server
- Check Groq service status at https://status.groq.com/

### Issue: "Module not found" errors in Python

**Solution:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

### Issue: Frontend build errors

**Solution:**
```bash
# Delete node_modules and reinstall
rm -rf node_modules
npm install
```

### Issue: Microphone not working

**Solution:**
- **Browser:** Allow microphone permissions when prompted
- **Windows:** Check Settings → Privacy → Microphone
- Use Chrome or Edge (best browser support)

### Issue: Whisper model download fails

**Solution:**
The first time you use speech-to-text, Whisper will auto-download. If it fails:
- Ensure you have a stable internet connection
- Check you have ~1GB free disk space
- Try manually: `pip install --upgrade faster-whisper`

## Using the Application

### Starting an Interview

1. Select your target cloud platform (AWS, Azure, GCP, Kubernetes)
2. Choose difficulty level (Junior, Mid-Level, Senior)
3. Click "Start Interview"

### During the Interview

- **Type answers:** Use the text area
- **Voice answers:** Click "Start Recording," speak your answer, then "Stop Recording"
- **Submit:** Click "Submit Answer" when ready
- **Next question:** After receiving feedback, click "Next Question"

### Ending an Interview

- Click "End Interview" at any time
- You'll receive a comprehensive summary with:
  - Overall score
  - Strengths and improvements
  - Study recommendations
  - Readiness assessment

## Performance Tips

### For Faster Responses

1. Use a smaller Whisper model in `backend/config.py`:
   ```python
   WHISPER_MODEL = "tiny"  # Options: tiny, base, small, medium, large
   ```

2. Adjust Groq temperature for more direct answers:
   ```python
   GROQ_TEMPERATURE = 0.5  # Lower = more deterministic
   ```

### For Better Quality

1. Use a larger Whisper model (if you have time):
   ```python
   WHISPER_MODEL = "medium"
   ```

2. Increase max tokens for longer responses:
   ```python
   GROQ_MAX_TOKENS = 3000
   ```

## Updating the System

### Update Groq API Settings
```bash
# Update your .env file with new API key if needed
echo "GROQ_API_KEY=your_new_key" > backend/.env
```

### Update Backend Dependencies
```bash
cd backend
pip install -r requirements.txt --upgrade
```

### Update Frontend Dependencies
```bash
cd frontend
npm update
```

## Data Storage

**Application Data:**
- **Database:** MongoDB (Docker volume `mongodb_data` or local MongoDB data directory)
- **Audio uploads:** `backend/uploads/audio/`
- **Sessions:** `backend/sessions/`

**Cloud Service Storage:**
- **Groq:** No local model storage required - runs in the cloud
- **API Usage:** Tracked by Groq (check console.groq.com for usage stats)

**Storage Requirements:**
- **Groq API:** No local model storage (cloud-based)
- **Whisper Models:** ~1-3GB (downloaded automatically)
- **Application Data:** <100MB (grows with interview sessions)

To reset your interview history, drop the `ops_mentor_ai` database in MongoDB.

**Note:** Groq handles all model storage in the cloud, so you don't need to worry about local disk space for AI models.

## Security & Privacy

✅ **Local data storage** - Interview data stays on your machine
✅ **Cloud AI processing** - Only prompts/responses go to Groq (encrypted)
✅ **Open source** - Review all code
✅ **Your data** - You control all interview session data
❌ **Internet required** - For AI processing via Groq API

## Next Steps

1. Practice with different platforms and difficulty levels
2. Review your session summaries to identify weak areas
3. Study recommended topics
4. Re-test yourself to track improvement

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Ensure Groq API key is set: `cat .env`
3. Check backend logs in the terminal
4. Check browser console (F12) for frontend errors

## System Requirements Summary

| Component | Requirement |
|-----------|-------------|
| RAM | 8GB (4GB minimum) |
| Storage | ~5GB free space |
| CPU | Modern dual-core (i5 or equivalent) |
| Internet | Required for Groq API |
| OS | Windows 10/11, Linux, macOS |
| Docker | Docker Desktop (recommended) |
| Python | 3.10+ (manual setup) |
| Node.js | 18+ (manual setup) |
| Browser | Chrome, Edge, Firefox (Chromium-based preferred) |

Enjoy practicing your interviews! 🚀
