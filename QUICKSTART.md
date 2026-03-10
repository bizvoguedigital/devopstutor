# Quick Start Guide

## Installation (First Time Only)

### 1. Get Groq API Key & Setup Environment
```bash
# 1. Get API key from: https://console.groq.com/
# 2. Create .env file in backend/:
echo "GROQ_API_KEY=your_api_key_here" > backend/.env
echo "MONGODB_URI=mongodb://localhost:27017/devops_interview_ai" >> backend/.env
echo "MONGODB_DB_NAME=devops_interview_ai" >> backend/.env
```

### 2. Start the Application (Docker)

```bash
docker compose up --build
```

### 3. Open Browser
Navigate to: **http://localhost:5173**

---

## Daily Usage

### Starting the System
1. Make sure you have your Groq API key in backend/.env
2. Run `docker compose up --build`
3. Open browser to http://localhost:5173

### Running an Interview
1. **Select Platform**: AWS, Azure, GCP, or Kubernetes
2. **Select Difficulty**: Junior, Mid, or Senior level
3. **Click "Start Interview"**
4. **Answer Questions**:
   - Type in the text area, OR
   - Click "Start Recording" → Speak → "Stop Recording"
5. **Submit Answer** and get instant feedback
6. **Continue** with more questions or **End Interview**
7. **Review Summary** with scores and recommendations

### Tips for Best Results
- Speak clearly when using voice recording
- Take time to think through answers
- Explain your reasoning, not just facts
- Ask for next question after each feedback

### Interviewer-v2 API Smoke Test (CV + JD + Blueprint)
Use this to validate the new Interviewer-v2 backend flow end-to-end.

1. Ensure backend is running (`docker compose up --build -d`)
2. Run the script from repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_interviewer_v2.ps1
```

Optional parameters:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_interviewer_v2.ps1 -BaseUrl http://localhost:8000/api -TargetDurationMinutes 45 -StrictMode
```

Expected output markers:
- `IV2_E2E_RESULT_START`
- `IV2_E2E_RESULT_END`

The JSON between those markers should contain:
- `cv_document_id`
- `jd_document_id`
- `blueprint_id`
- `delivery_mode` (expected: `tts_interviewer_led`)
- non-zero `competency_count` and `question_count`

### Interviewer-v2 End-to-End Smoke Test (Python)
Use this when you want a deterministic pass/fail checklist for the full interview lifecycle.

```powershell
& "C:\Users\bonito\Documents\BoniAI\.venv\Scripts\python.exe" .\backend\tests\smoke_interviewer_v2.py
```

This script validates:
- register/login cookie session
- CV + JD uploads
- blueprint generation
- session start/status
- turn submission
- session completion
- final summary fields (including `turn_reviews`)

### Backend Unit + Integration Tests

```powershell
& "C:\Users\bonito\Documents\BoniAI\.venv\Scripts\python.exe" -m pytest .\backend\tests\test_auth_unit.py -q
& "C:\Users\bonito\Documents\BoniAI\.venv\Scripts\python.exe" -m pytest .\backend\tests\test_auth_integration.py -q
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Red banner: "Cannot connect to LLM" | Check your GROQ_API_KEY in backend/.env |
| Backend won't start | Check if port 8000 is in use |
| Frontend won't start | Check if port 5173 is in use |
| Microphone not working | Allow browser microphone permissions |
| Slow responses | Groq is already very fast! |

---

## File Locations

- **Database**: MongoDB in Docker volume `mongodb_data` (or your local MongoDB instance)
- **Config**: `backend/config.py` or `backend/.env`
- **Logs**: Terminal output

---

## Keyboard Shortcuts

- **Ctrl+C** in terminal: Stop server
- **F12** in browser: Open developer console
- **Ctrl+R** in browser: Refresh page

---

## Common Commands

```bash
# Check Groq API connection
curl -H "Authorization: Bearer $GROQ_API_KEY" https://api.groq.com/openai/v1/models

# Test API key (replace with your key)
curl -H "Authorization: Bearer gsk_..." https://api.groq.com/openai/v1/models

# Reset interview history
# (Drop the database in MongoDB)
```

---

## Manual Development (No Docker)

Terminal 1 (Backend):
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 (Frontend):
```bash
cd frontend
npm install
npm run dev
```

---

## Need Help?

1. Check `SETUP.md` for detailed installation guide
2. Check `ARCHITECTURE.md` for technical details
3. Review backend logs in terminal
4. Check browser console (F12) for errors

---

## Quick Reference: Interview Categories

**AWS**: EC2, S3, Lambda, VPC, IAM, CloudFormation, ECS, RDS
**Azure**: VMs, Blob Storage, Functions, VNet, RBAC, ARM Templates
**GCP**: Compute Engine, Cloud Storage, Cloud Functions, VPC, IAM
**Kubernetes**: Pods, Services, Deployments, Ingress, ConfigMaps, Secrets

---

Happy practicing! 🚀
