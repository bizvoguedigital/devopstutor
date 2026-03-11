# Ops Mentor AI - Production Learning Platform

A comprehensive AI-powered learning platform for Cloud Engineering and DevOps careers. Features personalized learning journeys, user authentication, progress tracking, and AI interview practice.

## 🚀 Production Features

### 🔐 User Authentication & Management
- **Secure Registration/Login**: JWT-based authentication with bcrypt password hashing
- **User Profiles**: Personalized dashboards with progress tracking
- **Session Management**: Secure token-based API access

### 🛤️ Career Learning Journeys
- **Cloud Engineering Track**: AWS, Azure, GCP specialization paths
- **DevOps/Platform Engineering**: CI/CD, Kubernetes, monitoring focus
- **Hybrid Career Paths**: Combined cloud and DevOps tracks
- **Experience-Level Customization**: Junior, Mid-level, Senior tailored content

### 📈 Progress Tracking & Analytics
- **Module Progress**: Track completion of learning modules
- **Achievement System**: Earn badges and certifications
- **Learning Analytics**: Detailed progress insights and recommendations
- **User Statistics**: Performance metrics and growth tracking

### 🎯 Original AI Interview Features
- 🎤 Voice-based interview simulation
- 🤖 Powered by Groq's lightning-fast LLM inference
- ☁️ Multi-cloud support (AWS, Azure, GCP, Kubernetes)
- 📊 Session recording and performance analytics
- 🎯 Adjustable difficulty levels
- 💾 Comprehensive database with user data

## System Requirements

- 8GB RAM (minimum 4GB)
- Groq API key (free tier available)
- Docker Desktop (recommended)
- Python 3.10+ (manual setup)
- Node.js 18+ (manual setup)

## Quick Start

### 1. Get Groq API Key

1. Visit [Groq Console](https://console.groq.com/)
2. Sign up for a free account
3. Create an API key
4. Copy your API key

### 2. Setup Environment

Create a `.env` file in the `backend/` directory:
```bash
cd backend
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
echo "JWT_SECRET_KEY=your_jwt_secret_key_here" >> .env
echo "JWT_ALGORITHM=HS256" >> .env
echo "JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440" >> .env
echo "MONGODB_URI=mongodb://localhost:27017/ops_mentor_ai" >> .env
echo "MONGODB_DB_NAME=ops_mentor_ai" >> .env
```

**Generate JWT Secret Key:**
```bash
# Linux/macOS
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Windows
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Run with Docker (Recommended)

```bash
docker compose up --build
```

### 4. Open Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. Validate Interviewer-v2 Flow (Optional)
Run the end-to-end CV + JD + blueprint smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_interviewer_v2.ps1
```

Or run the Python smoke test (uses the same API flow and validates session completion artifacts):

```powershell
& "C:\Users\bonito\Documents\BoniAI\.venv\Scripts\python.exe" .\backend\tests\smoke_interviewer_v2.py
```

Optional parameters:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_interviewer_v2.ps1 -BaseUrl http://localhost:8000/api -TargetDurationMinutes 45 -StrictMode
```

For full details and expected output, see `QUICKSTART.md` under **Interviewer-v2 API Smoke Test (CV + JD + Blueprint)**.

### 6. Run Pre-Push Validation (Recommended)

Enable automatic pre-push checks once per clone:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-hooks.ps1
```

```bash
bash ./scripts/install-hooks.sh
```

Run the project pre-push script (backend tests + frontend production build):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepush-check.ps1
```

```bash
bash ./scripts/prepush-check.sh
```

Optional flags:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepush-check.ps1 -SkipBackendTests
powershell -ExecutionPolicy Bypass -File .\scripts\prepush-check.ps1 -SkipFrontendBuild
```

```bash
bash ./scripts/prepush-check.sh --skip-backend-tests
bash ./scripts/prepush-check.sh --skip-frontend-build
```

### 7. Run Backend Unit + Integration Tests (Manual)

```powershell
& "C:\Users\bonito\Documents\BoniAI\.venv\Scripts\python.exe" -m pytest .\backend\tests\test_auth_unit.py -q
& "C:\Users\bonito\Documents\BoniAI\.venv\Scripts\python.exe" -m pytest .\backend\tests\test_auth_integration.py -q
```

## Deployment Runbooks

- General deployment notes: `DEPLOYMENT-GUIDE.md`
- Contabo VPS Docker runbook: `CONTABO-HOSTING.md`
- Authentication implementation roadmap: `AUTHENTICATION-TASKS.md`

### Manual Setup (No Docker)

**Backend (Linux/Ubuntu/macOS):**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Backend (Windows):**
```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1  # PowerShell
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Troubleshooting

### PowerShell Execution Policy Error (Windows)

If you encounter this error when activating the virtual environment:
```
venv\Scripts\activate : File cannot be loaded because running scripts is disabled on this system.
```

**Step-by-step solution:**

1. **Check current execution policy:**
   ```powershell
   Get-ExecutionPolicy -List
   ```

2. **Set execution policy for current user:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
   ```

3. **Verify the change:**
   ```powershell
   Get-ExecutionPolicy -List
   ```
   You should see `CurrentUser` set to `RemoteSigned`

4. **Alternative activation methods:**
   - Use the full path: `& .\venv\Scripts\Activate.ps1`
   - Or use Command Prompt instead: `venv\Scripts\activate.bat`

**What this does:**
- `RemoteSigned` allows locally created scripts to run without signing
- `CurrentUser` scope only affects your user account (safer than system-wide)
- This is a one-time setup per user account

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Authentication**: JWT tokens, bcrypt password hashing
- **Database**: MongoDB with Motor (async)
- **AI Service**: Groq API (Llama 3.1)
- **Speech**: Faster-Whisper (Speech-to-Text)

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: TailwindCSS with glassmorphism design
- **State Management**: Zustand
- **HTTP Client**: Axios

### Production Features
- **Security**: JWT authentication, CORS protection
- **Database Models**: Users, Learning Paths, Progress Tracking
- **API**: RESTful endpoints with comprehensive documentation

## Usage

### Complete User Journey

1. **Registration/Login**
   - Create account with secure password
   - Login with JWT token authentication

2. **Career Path Selection**
   - Choose between Cloud Engineering, DevOps/Platform, or Hybrid
   - Select experience level (Junior, Mid, Senior)
   - Get personalized learning journey recommendations

3. **Learning Progress**
   - Follow structured learning modules
   - Track completion and achievements
   - View progress analytics

4. **AI Interview Practice**
   - Start interview sessions within your learning track
   - Select cloud platform and difficulty
   - Practice with voice or text interaction
   - Receive detailed feedback and scoring

5. **Dashboard & Analytics**
   - Monitor learning progress
   - View achievements and statistics
   - Get personalized recommendations

## License

MIT
