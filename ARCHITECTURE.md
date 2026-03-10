# DevOps AI Tutor - Production Architecture Overview

## Project Structure

```
devops-interview-ai/
├── docker-compose.yml          # Docker compose stack
├── .dockerignore               # Docker build exclusions
├── backend/                    # Python FastAPI backend
│   ├── main.py                 # FastAPI application with auth & learning endpoints
│   ├── config.py               # Configuration and JWT settings
│   ├── database.py             # Async database initialization
│   ├── models.py               # Enums shared across schemas
│   ├── schemas.py              # Pydantic schemas for all endpoints
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile               # Backend container image
│   ├── .env.example            # Environment variables template
│   └── services/               # Business logic services
│       ├── groq_service.py     # Groq API integration
│       ├── interview_engine.py # Interview Q&A logic
│       ├── speech_service.py   # Speech-to-text (Whisper)
│       ├── async_auth_service.py # JWT authentication service
│       └── learning_service.py # Learning journey management
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── App.jsx             # Main app with authentication routing
│   │   ├── main.jsx            # React entry point
│   │   ├── index.css           # Global styles (Tailwind + glassmorphism)
│   │   ├── components/         # React components
│   │   │   ├── HomeScreen.jsx        # Landing page
│   │   │   ├── AuthScreen.jsx        # Login/Registration
│   │   │   ├── CareerJourneyScreen.jsx # Career path selection
│   │   │   ├── SessionSetup.jsx      # Interview setup
│   │   │   ├── InterviewSession.jsx  # Interview interface
│   │   │   ├── SessionSummary.jsx    # Results summary
│   │   │   └── AwsStudyMode.jsx      # AWS study mode
│   │   ├── services/
│   │   │   └── api.js          # Enhanced API client with auth
│   │   └── store/
│   │       └── interviewStore.js # Zustand state management
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── Dockerfile               # Frontend container image
│
├── README.md                   # Project overview
├── SETUP.md                    # Installation guide
└── .gitignore

```

## Technology Stack

### Backend
- **Framework**: FastAPI (async Python web framework)
- **Authentication**: JWT tokens with bcrypt password hashing
- **LLM Service**: Groq API (cloud-based LLM inference)
- **Model**: LLaMA 3.1 8B Instant (via Groq's optimized infrastructure)
- **Speech-to-Text**: Faster-Whisper (optimized OpenAI Whisper)
- **Database**: MongoDB with Motor (async)
- **ODM**: Document-based collections (no ORM)
- **Security**: CORS middleware, secure password hashing

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite (fast modern bundler)
- **Styling**: TailwindCSS with glassmorphism design system
- **State Management**: Zustand (lightweight state management)
- **HTTP Client**: Axios with authentication interceptors
- **Icons**: React Icons
- **UI Components**: Custom glassmorphism components

## Key Features

### 1. User Authentication & Management
- **Secure Registration**: bcrypt password hashing, email validation
- **JWT Authentication**: Token-based authentication with refresh capability
- **User Profiles**: Comprehensive user data with career tracking
- **Protected Routes**: Frontend and backend route protection

### 2. Learning Journey System
- **Career Track Selection**: Cloud Engineering, DevOps/Platform, Hybrid paths
- **Experience Level Customization**: Junior, Mid-level, Senior content
- **Learning Path Generation**: AI-powered personalized learning recommendations
- **Module Structure**: Organized learning modules with dependencies

### 3. Progress Tracking & Analytics
- **Module Progress**: Detailed completion tracking per learning module
- **Achievement System**: Badges, certifications, and milestone rewards
- **User Statistics**: Performance metrics, time tracking, success rates
- **Learning Analytics**: Personalized recommendations and weak area identification

### 4. Session Management
- Create interview sessions within learning tracks
- Track session state (active, completed, abandoned)
- Store all Q&A pairs with user context
- Progress integration with learning paths

### 5. AI-Powered Interviews
- Generate contextual questions based on learning progress
- Evaluate answers using AI with structured feedback
- Provide follow-up questions for deeper understanding
- Support multiple cloud platforms (AWS, Azure, GCP, K8s)

### 6. Voice Interaction
- Real-time voice recording in the browser
- Speech-to-text transcription using Whisper
- Text-to-speech for question reading (optional)

### 7. Performance Analytics
- Individual question scoring (0-10)
- Overall session scoring integrated with learning progress
- Strengths and weaknesses analysis
- Study recommendations based on career track
- Readiness assessment for career advancement
Categories include:
- **AWS**: EC2, S3, Lambda, VPC, IAM, CloudFormation, etc.
- **Azure**: VMs, Blob Storage, Functions, VNet, RBAC, etc.
- **GCP**: Compute Engine, Cloud Storage, Cloud Functions, VPC, IAM, etc.
- **Kubernetes**: Pods, Services, Deployments, ConfigMaps, etc.
- **General DevOps**: CI/CD, Docker, Git, Linux, Networking, Security

## API Endpoints

### Health & Status
- `GET /api/health` - Check system health and Groq API connection

### Authentication
- `POST /api/auth/register` - User registration with secure password hashing
- `POST /api/auth/login` - User login with JWT token generation
- `GET /api/auth/me` - Get current user profile (protected)
- `PUT /api/auth/profile` - Update user profile (protected)
- `GET /api/auth/dashboard` - Get user dashboard with progress (protected)

### Learning Journey Management
- `POST /api/learning/career-journey` - Generate personalized career journey
- `GET /api/learning/paths` - Get available learning paths by career track
- `POST /api/learning/paths/{path_id}/start` - Start a learning path (protected)
- `GET /api/learning/progress` - Get user learning progress (protected)
- `PUT /api/learning/progress` - Update module progress (protected)
- `GET /api/learning/achievements` - Get user achievements (protected)

### Session Management
- `POST /api/sessions` - Create new interview session
- `GET /api/sessions/{session_id}` - Get session details
- `POST /api/sessions/{session_id}/complete` - End session and get summary

### Questions
- `POST /api/questions/generate` - Generate next question

### Answers
- `POST /api/answers/submit` - Submit answer and get evaluation

### Speech
- `POST /api/speech/transcribe` - Transcribe audio to text

## Database Schema

### User Management Tables

**users**
- id (PK)  
- username (unique)
- email (unique)
- hashed_password
- full_name
- career_track (cloud_engineering, devops_platform, hybrid)
- experience_level (junior, mid, senior)
- created_at
- updated_at
- last_login

### Learning System Tables

**learning_paths**
- id (PK)
- name
- description
- career_track (enum)
- experience_level (enum)
- estimated_duration
- difficulty_level
- prerequisites (JSON)
- learning_objectives (JSON)
- created_at

**learning_modules**
- id (PK)
- learning_path_id (FK)
- name
- description
- content (JSON)
- order_index
- estimated_time
- is_required
- prerequisites (JSON)

**user_progress**
- id (PK)
- user_id (FK)
- learning_path_id (FK)
- status (not_started, in_progress, completed)
- started_at
- completed_at
- progress_percentage

**module_progress**
- id (PK)
- user_id (FK)
- learning_module_id (FK)
- status (not_started, in_progress, completed)
- started_at
- completed_at
- time_spent
- notes

### Achievement System Tables

**achievements**
- id (PK)
- name
- description
- category
- requirements (JSON)
- badge_icon
- points

**user_achievements**
- id (PK)
- user_id (FK)
- achievement_id (FK)
- earned_at
- progress (JSON)

**user_stats**
- id (PK)
- user_id (FK)
- total_study_time
- modules_completed
- paths_completed
- current_streak
- longest_streak
- total_points
- last_updated

### Interview System Tables (Legacy)

**interview_sessions**
- id (PK)
- session_id (unique)
- user_id (FK) - now linked to users
- platform (aws, azure, gcp, kubernetes, general)
- difficulty (junior, mid, senior)
- started_at
- ended_at
- total_questions
- score
- status

**question_responses**
- id (PK)
- session_id (FK)
- question_number
- question_text
- question_category
- user_answer
- ai_feedback
- score
- timestamp
- audio_path

**question_bank** (expandable)
- id (PK)
- platform
- category
- difficulty
- question
- expected_points (JSON)
- follow_up_questions (JSON)

## Interview Flow

1. **Setup Phase**
   - User selects platform and difficulty
   - System creates session in database

2. **Question Generation**
   - AI generates question based on:
     * Selected platform
     * Difficulty level
     * Previous Q&A context (for relevance)
   - Question saved to database

3. **Answer Collection**
   - User types or speaks their answer
   - If voice: Browser records → Backend transcribes with Whisper
   - Answer stored with question

4. **Answer Evaluation**
   - AI evaluates answer on:
     * Technical accuracy
     * Completeness
     * Clarity
     * Real-world understanding
   - Feedback and score returned
   - Optional follow-up question generated

5. **Repeat or Complete**
   - User can continue with more questions
   - Or end interview and get summary

6. **Summary Generation**
   - AI analyzes all Q&A pairs
   - Generates comprehensive report:
     * Overall score
     * Strengths demonstrated
     * Areas needing improvement
     * Specific topics to study
     * Readiness assessment

## AI Prompting Strategy

### System Prompts

**Interviewer Role**:
- Professional technical interviewer
- Asks clear, realistic questions
- Conversational and friendly
- Tests both knowledge and communication

**Evaluator Role**:
- Expert technical evaluator
- Fair but thorough assessment
- Specific, actionable feedback
- Structured scoring criteria

### Context Management
- Last 3 Q&A pairs included for context
- Prevents repetitive questions
- Enables follow-up questions
- Maintains conversation flow

## Performance Considerations

### Backend Optimization
- Async/await throughout for concurrency
- Lazy loading of Whisper model
- Connection pooling for database
- Streaming responses for real-time feel

### Frontend Optimization
- Component-based architecture
- Efficient state management with Zustand
- Lazy loading of large components
- Optimized audio recording with MediaRecorder API

### LLM Optimization
- Temperature tuning per use case (0.3 for evaluation, 0.7 for questions)
- Token limits to control response length
- Structured output (JSON) for evaluation
- Context window management

## Extensibility

### Adding New Platforms
1. Update platform list in `SessionSetup.jsx`
2. Add platform-specific prompt examples in `interview_engine.py`
3. Optionally add to question bank

### Adding New Features
- **Code evaluation**: Add code execution sandbox
- **Diagram drawing**: Integrate whiteboard component
- **Mock scenarios**: Add practical troubleshooting scenarios
- **Spaced repetition**: Track weak areas and quiz again later

### Model Flexibility
The system uses Groq's optimized models:
- LLaMA 3 8B (default)
- LLaMA 3 70B (available)
- Mixtral 8x7B (available)
- Other Groq-supported models

## Security & Privacy

- ✅ **No external API calls** (after setup)
- ✅ **All data stored locally**
- ✅ **No telemetry or tracking**
- ✅ **Open source code**
- ✅ **User controls all data**

## Future Enhancements

1. **Export capabilities**: PDF/JSON export of session reports
2. **Progress tracking**: Long-term improvement tracking
3. **Custom question banks**: Import your own questions
4. **Multi-language support**: Practice in different languages
5. **Mock coding challenges**: Integrate code editor
6. **Peer comparison**: Anonymous benchmarking (optional)
7. **Certification prep**: Aligned with AWS SAA, CKA, etc.

## License

MIT License - Free to use, modify, and distribute
