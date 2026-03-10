# API Reference

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://yourdomain.com`

## Authentication

All protected endpoints require JWT token in the Authorization header:
```bash
Authorization: Bearer <your_jwt_token>
```

## Interviewer-v2 Validation (Smoke)

Run this end-to-end smoke check to validate CV upload, JD upload, and blueprint generation:

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
- `delivery_mode` (`tts_interviewer_led`)
- non-zero `competency_count` and `question_count`

## Interviewer-v2 Artifact Endpoints

These endpoints require authentication and only return artifacts for the current user.

#### Get Artifact by Session
```http
GET /api/interviewer-v2/sessions/{session_id}/artifact
Authorization: Bearer <token>
```

#### Get Artifact by Artifact ID
```http
GET /api/interviewer-v2/artifacts/{session_artifact_id}
Authorization: Bearer <token>
```

#### List Artifacts (Paginated)
```http
GET /api/interviewer-v2/artifacts?limit=20&offset=0
Authorization: Bearer <token>
```

Optional query params:
- `status` (example: `completed`)
- `readiness_band` (example: `emerging`, `progressing`, `interview_ready`)
- `sort_by` (`created_at`, `average_score`, `interview_readiness_score`)
- `sort_order` (`asc`, `desc`)

Example:

```http
GET /api/interviewer-v2/artifacts?status=completed&sort_by=interview_readiness_score&sort_order=desc&limit=10&offset=0
Authorization: Bearer <token>
```

Sample response shape:

```json
{
  "items": [
    {
      "session_artifact_id": "iv2a_...",
      "session_id": "iv2s_...",
      "blueprint_id": "iv2b_...",
      "status": "completed",
      "turns_answered": 6,
      "average_score": 7.3,
      "overall_signal_coverage_ratio": 0.67,
      "interview_readiness_score": 7.04,
      "readiness_band": "progressing",
      "top_strengths": ["Incident Response"],
      "improvement_focus": ["System Design"],
      "competency_coverage": [],
      "created_at": "2026-03-07T12:00:00Z"
    }
  ],
  "total": 12,
  "limit": 20,
  "offset": 0,
  "has_more": false,
  "status_filter": "completed",
  "readiness_band_filter": null,
  "sort_by": "interview_readiness_score",
  "sort_order": "desc"
}
```

#### Delete Artifact by ID
```http
DELETE /api/interviewer-v2/artifacts/{session_artifact_id}
Authorization: Bearer <token>
```

#### Cleanup Artifacts (Retention)
```http
POST /api/interviewer-v2/artifacts/cleanup
Authorization: Bearer <token>
Content-Type: application/json

{
  "keep_latest": 10,
  "dry_run": false
}
```

Notes:
- `keep_latest` keeps the newest N artifacts and removes older artifacts for the same user.
- `dry_run=true` returns what would be removed without deleting.

## Interviewer-v2 Hardening Notes

- `POST /api/interviewer-v2/sessions/{session_id}/turn` trims `user_response` and rejects empty content.
- Turn submissions apply a short cooldown to reduce rapid repeat requests.
- `GET /api/interviewer-v2/artifacts` enforces bounded query params (`limit` 1-100, `offset` 0-10000) and strict enum values for `readiness_band`, `sort_by`, and `sort_order`.

## Endpoints

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com", 
  "password": "secure_password",
  "full_name": "John Doe"
}
```

#### Login User  
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=john_doe&password=secure_password
```

#### Get Current User (Protected)
```http
GET /api/auth/me
Authorization: Bearer <token>
```

#### Update Profile (Protected)
```http  
PUT /api/auth/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "John Smith",
  "career_track": "cloud_engineering", 
  "experience_level": "mid"
}
```

#### Get Dashboard (Protected)
```http
GET /api/auth/dashboard
Authorization: Bearer <token>
```

### Learning Journey

#### Generate Career Journey (Protected)
```http
POST /api/learning/career-journey
Authorization: Bearer <token>
Content-Type: application/json

{
  "career_track": "cloud_engineering",
  "experience_level": "junior",
  "interests": ["aws", "azure"],
  "goals": ["certification", "promotion"]
}
```

#### Get Learning Paths
```http  
GET /api/learning/paths?career_track=cloud_engineering
```

#### Start Learning Path (Protected)
```http
POST /api/learning/paths/{path_id}/start
Authorization: Bearer <token>
```

#### Get Progress (Protected)
```http
GET /api/learning/progress
Authorization: Bearer <token>
```

#### Update Module Progress (Protected)  
```http
PUT /api/learning/progress
Authorization: Bearer <token>
Content-Type: application/json

{
  "module_id": 123,
  "status": "completed",
  "time_spent": 1800,
  "notes": "Completed AWS EC2 fundamentals"
}
```

#### Get Achievements (Protected)
```http
GET /api/learning/achievements  
Authorization: Bearer <token>
```

### Interview System

#### Create Session (Protected)
```http
POST /api/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "platform": "aws",
  "difficulty": "junior",
  "topic_focus": "compute"
}
```

#### Generate Question
```http
POST /api/questions/generate
Content-Type: application/json

{
  "session_id": "uuid-string",
  "platform": "aws",
  "difficulty": "junior",
  "context": "Previous questions context"
}
```

#### Submit Answer
```http
POST /api/answers/submit
Content-Type: application/json

{
  "session_id": "uuid-string", 
  "question_id": 1,
  "answer": "User's answer text",
  "audio_data": "base64_encoded_audio_optional"
}
```

#### Transcribe Speech
```http
POST /api/speech/transcribe
Content-Type: multipart/form-data

audio=@audiofile.wav
```

### Health & Utilities

#### Health Check
```http
GET /api/health
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully"
}
```

### Error Response  
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "error description"
    }
  }
}
```

### Authentication Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe"
  }
}
```

## Status Codes

- `200` - Success
- `201` - Created successfully  
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Resource not found
- `422` - Validation error
- `500` - Internal server error

## Rate Limiting

- **Authentication endpoints**: 5 requests per minute
- **General API**: 60 requests per minute  
- **File uploads**: 10 requests per minute

## Data Models

### User
```json
{
  "id": 1,
  "username": "john_doe", 
  "email": "john@example.com",
  "full_name": "John Doe",
  "career_track": "cloud_engineering",
  "experience_level": "junior", 
  "created_at": "2026-02-15T10:00:00Z",
  "last_login": "2026-02-15T11:00:00Z"
}
```

### Learning Path
```json
{
  "id": 1,
  "name": "AWS Cloud Engineering Fundamentals",
  "description": "Master core AWS services",
  "career_track": "cloud_engineering",
  "experience_level": "junior",
  "estimated_duration": "8 weeks",
  "difficulty_level": 3,
  "modules": [
    {
      "id": 1,
      "name": "AWS Basics",
      "description": "Introduction to AWS",
      "estimated_time": 300,
      "order_index": 1
    }
  ]
}
```

### User Progress  
```json
{
  "learning_path_id": 1,
  "status": "in_progress",
  "progress_percentage": 45,
  "modules_completed": 3,
  "total_modules": 8,
  "started_at": "2026-02-01T10:00:00Z",
  "last_activity": "2026-02-15T11:00:00Z"
}
```

### Career Journey Response
```json
{
  "journey": {
    "title": "Cloud Engineering Career Path",
    "description": "Comprehensive journey from junior to expert",
    "estimated_duration": "12 months",
    "career_progression": [
      "Junior Cloud Engineer",
      "Cloud Engineer", 
      "Senior Cloud Engineer",
      "Cloud Architect"
    ], 
    "recommended_paths": [
      {
        "id": 1,
        "name": "AWS Fundamentals",
        "priority": "high"
      }
    ],
    "certifications": [
      "AWS Solutions Architect Associate",
      "Azure Fundamentals"
    ]
  }
}
```

## Interactive Documentation

Visit these URLs when your server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Client Examples

### JavaScript/Axios
```javascript  
// Login
const login = async (username, password) => {
  const response = await axios.post('/api/auth/login', 
    `username=${username}&password=${password}`,
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
  );
  return response.data;
};

// Authenticated request
const getProfile = async (token) => {
  const response = await axios.get('/api/auth/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.data;
};
```

### Python/Requests
```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/auth/login',
    data={'username': 'john_doe', 'password': 'password'}
)
token = response.json()['access_token']

# Authenticated request  
headers = {'Authorization': f'Bearer {token}'}
profile = requests.get(
    'http://localhost:8000/api/auth/me', 
    headers=headers
).json()
```

### cURL
```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=password"

# Get profile  
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer your_token_here"
```