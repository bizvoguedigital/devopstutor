import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 10000,
});

// Add response interceptor to handle auth errors
const AUTH_ENDPOINTS = [
  '/auth/login',
  '/auth/register',
  '/auth/refresh',
  '/auth/request-email-verification',
  '/auth/verify-email',
  '/auth/request-password-reset',
  '/auth/reset-password',
];

const notifySessionExpired = () => {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent('auth:session-expired'));
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const requestPath = originalRequest?.url || '';
    const isAuthEndpoint = AUTH_ENDPOINTS.some((path) => requestPath.includes(path));

    if (error.response?.status === 401 && !originalRequest?._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      try {
        await api.post('/auth/refresh');
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('user');
        notifySessionExpired();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export const apiService = {
  // ============================================================================
  // AUTHENTICATION
  // ============================================================================
  
  // Register new user
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  // Login user
  login: async (loginData) => {
    const response = await api.post('/auth/login', loginData);
    return response.data;
  },

  // Get current user profile
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  refreshSession: async () => {
    const response = await api.post('/auth/refresh');
    return response.data;
  },

  // Update user profile
  updateProfile: async (updateData) => {
    const response = await api.put('/auth/me', updateData);
    return response.data;
  },

  uploadAvatar: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/auth/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getDashboard: async () => {
    const response = await api.get('/auth/dashboard');
    return response.data;
  },

  getInterviewAnalytics: async () => {
    const response = await api.get('/auth/interview-analytics');
    return response.data;
  },

  // Logout user (client-side only)
  logout: async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      localStorage.removeItem('user');
    }
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem('user');
  },

  requestEmailVerification: async (email) => {
    const response = await api.post('/auth/request-email-verification', { email });
    return response.data;
  },

  verifyEmail: async (token) => {
    const response = await api.post('/auth/verify-email', { token });
    return response.data;
  },

  requestPasswordReset: async (email) => {
    const response = await api.post('/auth/request-password-reset', { email });
    return response.data;
  },

  resetPassword: async (token, newPassword) => {
    const response = await api.post('/auth/reset-password', { token, new_password: newPassword });
    return response.data;
  },

  getVoiceRuntimeStatus: async () => {
    const response = await api.get('/voice/runtime');
    return response.data;
  },

  createLivekitVoiceToken: async (sessionId, roomName = null) => {
    const payload = {
      session_id: sessionId,
      room_name: roomName,
    };
    const response = await api.post('/voice/livekit/token', payload);
    return response.data;
  },

  // ============================================================================
  // LEARNING JOURNEYS
  // ============================================================================

  // Get career journey recommendations
  getCareerJourney: async (journeyRequest) => {
    const response = await api.post('/journey/recommend', journeyRequest, {
      timeout: 120000,
    });
    return response.data;
  },

  // Get detailed journey plan
  getJourneyPlan: async (journeyRequest) => {
    const response = await api.post('/journey/plan', journeyRequest, {
      timeout: 120000,
    });
    return response.data;
  },

  // Get all learning paths
  getLearningPaths: async (careerTrack = null) => {
    const params = careerTrack ? { career_track: careerTrack } : {};
    const response = await api.get('/learning/paths', { params });
    return response.data;
  },

  // Start a learning path
  startLearningPath: async (pathId) => {
    const response = await api.post(`/learning/paths/${pathId}/start`);
    return response.data;
  },

  // Get user progress
  getUserProgress: async () => {
    const response = await api.get('/learning/progress');
    return response.data;
  },

  // Update module progress
  updateProgress: async (progressData) => {
    const response = await api.put('/learning/progress', progressData);
    return response.data;
  },

  // Update topic-level progress
  updateTopicProgress: async (progressData) => {
    const response = await api.post('/journey/topics/progress', progressData);
    return response.data;
  },

  // Update module assessment progress
  updateModuleAssessment: async (progressData) => {
    const response = await api.post('/journey/modules/assessment', progressData);
    return response.data;
  },

  // Reset module assessment progress
  resetModuleAssessment: async (resetData) => {
    const response = await api.post('/journey/modules/assessment/reset', resetData);
    return response.data;
  },

  // ============================================================================
  // SESSIONS (Enhanced with user support)
  // ============================================================================

  // Health check
  checkHealth: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  // Session management
  createSession: async (platform, difficulty, careerTrack = null, moduleId = null) => {
    const response = await api.post('/sessions', { 
      platform, 
      difficulty, 
      career_track: careerTrack,
      module_id: moduleId
    });
    return response.data;
  },

  getSession: async (sessionId) => {
    const response = await api.get(`/sessions/${sessionId}`);
    return response.data;
  },

  completeSession: async (sessionId) => {
    const response = await api.post(`/sessions/${sessionId}/complete`);
    return response.data;
  },

  // Interviewer-v2 setup + lifecycle
  uploadInterviewerV2Cv: async (file, rawText = '') => {
    const formData = new FormData();
    formData.append('file', file);
    if (rawText) {
      formData.append('raw_text', rawText);
    }

    const response = await api.post('/interviewer-v2/documents/cv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000,
    });
    return response.data;
  },

  uploadInterviewerV2JobDescription: async (file, rawText = '') => {
    const formData = new FormData();
    formData.append('file', file);
    if (rawText) {
      formData.append('raw_text', rawText);
    }

    const response = await api.post('/interviewer-v2/documents/job-description', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000,
    });
    return response.data;
  },

  generateInterviewerV2Blueprint: async (payload) => {
    const response = await api.post('/interviewer-v2/blueprints/generate', payload, {
      timeout: 120000,
    });
    return response.data;
  },

  startInterviewerV2Session: async (blueprintId) => {
    const response = await api.post('/interviewer-v2/sessions/start', {
      blueprint_id: blueprintId,
    });
    return response.data;
  },

  getInterviewerV2SessionStatus: async (sessionId) => {
    const response = await api.get(`/interviewer-v2/sessions/${sessionId}/status`);
    return response.data;
  },

  submitInterviewerV2Turn: async (sessionId, userResponse) => {
    const response = await api.post(`/interviewer-v2/sessions/${sessionId}/turn`, {
      user_response: userResponse,
    });
    return response.data;
  },

  completeInterviewerV2Session: async (sessionId) => {
    const response = await api.post(`/interviewer-v2/sessions/${sessionId}/complete`);
    return response.data;
  },

  // Interviewer-v2 Artifacts
  listInterviewerV2Artifacts: async (params = {}) => {
    const response = await api.get('/interviewer-v2/artifacts', { params });
    return response.data;
  },

  getInterviewerV2ArtifactById: async (sessionArtifactId) => {
    const response = await api.get(`/interviewer-v2/artifacts/${sessionArtifactId}`);
    return response.data;
  },

  deleteInterviewerV2ArtifactById: async (sessionArtifactId) => {
    const response = await api.delete(`/interviewer-v2/artifacts/${sessionArtifactId}`);
    return response.data;
  },

  cleanupInterviewerV2Artifacts: async (payload) => {
    const response = await api.post('/interviewer-v2/artifacts/cleanup', payload);
    return response.data;
  },

  // Questions
  generateQuestion: async (sessionId, category = 'general') => {
    const response = await api.post('/questions/generate', {
      session_id: sessionId,
      category,
    });
    return response.data;
  },

  // Answers
  submitAnswer: async (sessionId, questionId, answerText, audioPath = null) => {
    const response = await api.post('/answers/submit', {
      session_id: sessionId,
      question_id: questionId,
      answer_text: answerText,
      audio_path: audioPath,
    });
    return response.data;
  },

  // Speech
  transcribeAudio: async (audioBlob) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    const response = await api.post('/speech/transcribe', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    });
    return response.data;
  },

  // TTS
  getTtsStatus: async () => {
    const response = await api.get('/tts/status');
    return response.data;
  },

  getTtsVoices: async () => {
    const response = await api.get('/tts/voices');
    return response.data;
  },

  synthesizeSpeech: async (payload) => {
    const response = await api.post('/tts/synthesize', payload, {
      responseType: 'blob',
      timeout: 60000,
    });
    return response.data;
  },

  // AWS Study Mode
  startAwsLearning: async (serviceName) => {
    const response = await api.post('/aws/learn', {
      service_name: serviceName,
    });
    return response.data;
  },

  // Exam Simulator
  startExam: async (certificate, questionCount) => {
    const response = await api.post('/exams/start', {
      certificate,
      question_count: questionCount,
    });
    return response.data;
  },

  getActiveExam: async () => {
    const response = await api.get('/exams/active');
    return response.data;
  },

  saveExamProgress: async (examId, payload) => {
    const response = await api.put(`/exams/${examId}/progress`, payload);
    return response.data;
  },

  submitExam: async (examId, answers) => {
    const response = await api.post('/exams/submit', {
      exam_id: examId,
      answers,
    });
    return response.data;
  },

  // Admin Console
  getAdminOverview: async () => {
    const response = await api.get('/admin/overview');
    return response.data;
  },

  getAdminConfig: async () => {
    const response = await api.get('/admin/config');
    return response.data;
  },

  updateAdminConfig: async (payload) => {
    const response = await api.put('/admin/config', payload);
    return response.data;
  },

  clearTtsCache: async () => {
    const response = await api.post('/admin/tts/cache/clear');
    return response.data;
  },

  getAdminTtsProviderStatus: async (forceCheck = true) => {
    const response = await api.get('/admin/tts/provider-status', {
      params: { force_check: forceCheck },
    });
    return response.data;
  },

  runAdminTtsTest: async (payload = {}) => {
    const response = await api.post('/admin/tts/test', payload);
    return response.data;
  },

  syncJourneyContent: async (payload) => {
    const response = await api.post('/admin/journey/content/sync', payload, {
      timeout: 300000,
    });
    return response.data;
  },

  startJourneyContentSync: async (payload) => {
    const response = await api.post('/admin/journey/content/sync/start', payload);
    return response.data;
  },

  getJourneyContentSyncStatus: async () => {
    const response = await api.get('/admin/journey/content/sync/status');
    return response.data;
  },
};

export default api;
