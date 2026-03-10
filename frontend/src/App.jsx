import React, { useEffect, useMemo, useState } from 'react';
import { FaBars, FaTimes, FaUserEdit, FaSignOutAlt, FaBolt } from 'react-icons/fa';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import HomeScreen from './components/HomeScreen';
import SessionSetupNew from './components/SessionSetupNew';
import InterviewSession from './components/InterviewSession';
import SessionSummary from './components/SessionSummary';
import AwsStudyMode from './components/AwsStudyMode';
import ExamSimulator from './components/ExamSimulator';
import AuthScreen from './components/AuthScreen';
import CareerJourneyScreen from './components/CareerJourneyScreen';
import UserProfile from './components/UserProfile';
import AdminConsole from './components/AdminConsole';
import { apiService } from './services/api';
import { useInterviewStore } from './store/interviewStore';

function App() {
  const sessionSummaryStorageKey = 'devopsai:sessionSummary';
  const sessionStorageKey = 'devopsai:activeSession';
  const [sessionSummary, setSessionSummary] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [healthError, setHealthError] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthenticating, setIsAuthenticating] = useState(true);
  const [authNotice, setAuthNotice] = useState(null);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useInterviewStore((state) => state.setSession);
  const clearSession = useInterviewStore((state) => state.clearSession);
  const session = useInterviewStore((state) => state.session);
  const questionHistory = useInterviewStore((state) => state.questionHistory);

  useEffect(() => {
    checkHealth();
    checkAuthStatus();
  }, []);

  useEffect(() => {
    const storedSummary = localStorage.getItem(sessionSummaryStorageKey);
    if (!storedSummary) return;
    try {
      setSessionSummary(JSON.parse(storedSummary));
    } catch (error) {
      console.warn('Failed to parse stored session summary.', error);
      localStorage.removeItem(sessionSummaryStorageKey);
    }
  }, []);

  useEffect(() => {
    const storedSession = localStorage.getItem(sessionStorageKey);
    if (!storedSession || session) return;
    try {
      setSession(JSON.parse(storedSession));
    } catch (error) {
      console.warn('Failed to parse stored session.', error);
      localStorage.removeItem(sessionStorageKey);
    }
  }, [session, setSession]);

  useEffect(() => {
    if (sessionSummary) {
      localStorage.setItem(sessionSummaryStorageKey, JSON.stringify(sessionSummary));
    } else {
      localStorage.removeItem(sessionSummaryStorageKey);
    }
  }, [sessionSummary]);

  useEffect(() => {
    if (session) {
      localStorage.setItem(sessionStorageKey, JSON.stringify(session));
    } else {
      localStorage.removeItem(sessionStorageKey);
    }
  }, [session]);

  useEffect(() => {
    setIsMobileNavOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const handleSessionExpired = () => {
      setCurrentUser(null);
      setAuthNotice('Session expired. Please sign in again.');
      if (location.pathname !== '/auth') {
        setTimeout(() => {
          navigate('/auth');
        }, 1200);
      }
    };

    window.addEventListener('auth:session-expired', handleSessionExpired);
    return () => window.removeEventListener('auth:session-expired', handleSessionExpired);
  }, [location.pathname, navigate]);

  const checkHealth = async () => {
    try {
      const health = await apiService.checkHealth();
      setHealthStatus(health);
      setHealthError(null);
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({ status: 'error', llm_connected: false });
      setHealthError(error?.message || 'Backend is unreachable');
    }
  };

  const checkAuthStatus = async () => {
    setIsAuthenticating(true);

    const withTimeout = (promise, timeoutMs) => new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('Request timed out')), timeoutMs);
      promise
        .then((value) => {
          clearTimeout(timer);
          resolve(value);
        })
        .catch((err) => {
          clearTimeout(timer);
          reject(err);
        });
    });

    try {
      // Verify token and get user data
      const user = await withTimeout(apiService.getCurrentUser(), 8000);
      setCurrentUser(user);
      setAuthNotice(null);
    } catch (error) {
      if (error?.message === 'Request timed out') {
        setAuthNotice('Auth check timed out. Please retry.');
        setCurrentUser(null);
        return;
      }
      const status = error?.response?.status;
      if (status && status !== 401) {
        console.error('Auth check failed:', error);
        setAuthNotice(null);
      } else if (status === 401) {
        setAuthNotice('Session expired. Please sign in again.');
      }
      setCurrentUser(null);
    } finally {
      setIsAuthenticating(false);
    }
  };

  const handleAuthSuccess = (authResponse) => {
    setCurrentUser(authResponse.user);
    setAuthNotice(null);
    navigate('/');
  };

  const handleLogout = async () => {
    await apiService.logout();
    setCurrentUser(null);
    setAuthNotice(null);
    handleBackToHome();
  };

  const handleModeSelect = (mode) => {
    if (mode === 'interview') {
      // Interview Coach should always go to interview setup
      navigate('/interview-coach');
    } else if (mode === 'journey') {
      if (currentUser) {
        // For authenticated users, go to career journey planning
        navigate('/journey');
      } else {
        // For anonymous users, prompt to authenticate first for career journey
        navigate('/auth');
      }
    } else if (mode === 'aws-study') {
      navigate('/aws-study');
    } else if (mode === 'exam') {
      navigate('/exam');
    } else if (mode === 'auth') {
      navigate('/auth');
    } else if (mode === 'profile') {
      navigate('/profile');
    } else if (mode === 'admin') {
      navigate('/admin');
    }
  };

  const handleBackToHome = () => {
    clearSession();
    setSessionSummary(null);
    navigate('/');
  };


  const handleSessionStart = (session) => {
    navigate('/interview');
  };

  const handleSessionComplete = (summary) => {
    const scores = questionHistory
      .map((item) => Number(item.evaluation?.score ?? 0))
      .filter((value) => Number.isFinite(value));
    const total = scores.reduce((sum, value) => sum + value, 0);
    const average = scores.length ? total / scores.length : 0;

    const mergedSummary = {
      overall_score: Number.isFinite(summary?.overall_score)
        ? summary.overall_score
        : Number(average.toFixed(1)),
      platform: summary?.platform || session?.platform || 'unknown',
      difficulty: summary?.difficulty || session?.difficulty || 'unknown',
      interview_experience_mode: summary?.interview_experience_mode || session?.interview_experience_mode || 'learning',
      total_questions: summary?.total_questions ?? questionHistory.length,
      ...summary,
    };

    setSessionSummary(mergedSummary);
    navigate('/summary');
  };

  const handleRestart = () => {
    clearSession();
    setSessionSummary(null);
    if (currentUser) {
      navigate('/journey'); // Authenticated users go back to journey selection
    } else {
      navigate('/'); // Anonymous users go to home
    }
  };

  const activeMode = useMemo(() => {
    const path = location.pathname;
    if (path.startsWith('/interview-coach') || path.startsWith('/interview') || path.startsWith('/summary')) {
      return 'interview';
    }
    if (path.startsWith('/journey')) return 'journey';
    if (path.startsWith('/aws-study')) return 'aws-study';
    if (path.startsWith('/exam')) return 'exam';
    if (path.startsWith('/auth')) return 'auth';
    if (path.startsWith('/profile')) return 'profile';
    if (path.startsWith('/admin')) return 'admin';
    return 'home';
  }, [location.pathname]);

  const navItems = [
    { id: 'home', label: 'Home', action: handleBackToHome },
    { id: 'interview', label: 'Interview Coach', action: () => handleModeSelect('interview') },
    { id: 'journey', label: 'Career Journey', action: () => handleModeSelect('journey') },
    { id: 'aws-study', label: 'Cloud Refresher', action: () => navigate('/aws-study') },
    { id: 'exam', label: 'Exam Simulator', action: () => navigate('/exam') },
    ...(currentUser?.is_admin ? [{ id: 'admin', label: 'Admin Console', action: () => handleModeSelect('admin') }] : []),
  ];

  const handleNavClick = (action) => {
    action();
    setIsMobileNavOpen(false);
  };

  // Show loading screen while checking authentication
  if (isAuthenticating) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading...</p>
          {healthStatus?.status === 'error' && (
            <div className="mt-4 rounded-2xl border border-red-500/40 bg-red-950/40 px-4 py-3 text-left">
              <p className="text-sm text-red-200">Backend is unreachable. Start the API server and retry.</p>
              <p className="text-xs text-red-300 mt-1">{healthError || 'Health check failed.'}</p>
              <button
                onClick={checkHealth}
                className="mt-3 btn btn-danger px-3 py-1.5 text-xs"
              >
                Retry connection
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  const profileInitials = (currentUser?.full_name || currentUser?.username || 'Guest')
    .split(' ')
    .slice(0, 2)
    .map((name) => name[0]?.toUpperCase())
    .join('') || 'G';

  return (
    <div className="min-h-screen bg-transparent text-white">
      {/* Health Status Banner */}
      {healthStatus && !healthStatus.llm_connected && (
        <div className="bg-rose-500/25 border-b border-rose-300/60 p-4 text-center backdrop-blur-sm">
          {healthStatus.status === 'error' ? (
            <>
              <p className="text-red-200">⚠️ Backend is unreachable. Start the API server and retry.</p>
              <p className="text-sm text-red-300 mt-1">{healthError || 'Health check failed.'}</p>
            </>
          ) : (
            <>
              <p className="text-red-200">
                ⚠️ Cannot connect to AI service. Please check your Groq API key.
              </p>
              <p className="text-sm text-red-300 mt-1">
                Setup: Create <code className="bg-red-950 px-2 py-1 rounded">.env</code> file with <code className="bg-red-950 px-2 py-1 rounded">GROQ_API_KEY=your_key</code>
              </p>
            </>
          )}
          <button
            onClick={checkHealth}
            className="btn btn-danger mt-3 px-3 py-1.5 text-sm"
          >
            Retry connection
          </button>
        </div>
      )}

      {authNotice && location.pathname !== '/auth' && (
        <div className="bg-amber-400/25 border-b border-amber-200/70 p-4 text-center backdrop-blur-sm">
          <p className="text-amber-100">{authNotice}</p>
          <button
            onClick={() => navigate('/auth?mode=signin')}
            className="btn btn-warning mt-3 px-3 py-1.5 text-sm"
          >
            Sign in
          </button>
        </div>
      )}

      <header className="app-header mx-auto max-w-7xl px-4 sm:px-6 pt-5 sm:pt-8">
          <div className="rounded-3xl border border-white/10 px-4 py-4 sm:px-8 sm:py-5">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-4">
                <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-cyan-500 via-teal-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                  <span className="text-white font-bold">D</span>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.35em] text-slate-400">DevOps Learning Hub</p>
                  <h1 className="text-2xl sm:text-3xl font-semibold text-white">AI Study Workspace</h1>
                </div>
              </div>

              <div className="hidden md:block flex-1 md:px-6"></div>

              <div className="flex items-center justify-between md:justify-end gap-3">
                <div className="hidden lg:flex items-center gap-2 rounded-2xl bg-white/10 border border-white/25 px-2 py-2">
                  {navItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleNavClick(item.action)}
                      className={`rounded-xl px-3 py-2 text-xs font-semibold transition-all ${
                        activeMode === item.id
                          ? 'bg-white/10 text-white'
                          : 'text-slate-100 hover:text-white hover:bg-white/15'
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>

                <button
                  onClick={() => setIsMobileNavOpen((prev) => !prev)}
                  className="md:hidden btn btn-secondary px-3 py-2"
                  aria-label="Toggle navigation menu"
                >
                  {isMobileNavOpen ? <FaTimes /> : <FaBars />}
                </button>
                <div className="flex items-center gap-3 rounded-2xl bg-white/10 border border-white/25 px-3 py-2">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-fuchsia-500 to-violet-500 flex items-center justify-center text-white text-sm font-semibold">
                    {profileInitials}
                  </div>
                  <div className="hidden sm:block">
                    <p className="text-sm font-semibold text-white">
                      {currentUser?.full_name || currentUser?.username || 'Guest Explorer'}
                    </p>
                    <p className="text-xs text-slate-400">
                      {currentUser ? 'Signed in' : 'Guest session'}
                    </p>
                  </div>
                </div>
                {!currentUser && (
                  <div className="hidden sm:flex items-center gap-2">
                    <button
                      onClick={() => navigate('/auth?mode=signin')}
                      className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-white transition hover:bg-white/10"
                    >
                      Sign in
                    </button>
                    <button
                      onClick={() => navigate('/auth?mode=signup')}
                      className="rounded-xl bg-gradient-to-r from-fuchsia-500 to-violet-500 px-3 py-2 text-xs font-semibold text-white transition hover:from-fuchsia-400 hover:to-violet-400"
                    >
                      Register
                    </button>
                  </div>
                )}
                {currentUser && (
                  <div className="hidden sm:flex items-center gap-2">
                    <button
                      onClick={() => handleModeSelect('profile')}
                      className="icon-btn hover:border-cyan-500/30 hover:text-cyan-300 hover:bg-cyan-500/5"
                      title="Edit Profile"
                    >
                      <FaUserEdit className="text-lg" />
                    </button>
                    <button
                      onClick={handleLogout}
                      className="icon-btn hover:border-red-500/30 hover:text-red-400 hover:bg-red-500/5"
                      title="Sign Out"
                    >
                      <FaSignOutAlt className="text-lg" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {isMobileNavOpen && (
            <div className="md:hidden fixed inset-0 z-50">
              <button
                className="absolute inset-0 bg-violet-950/75 backdrop-blur-sm"
                onClick={() => setIsMobileNavOpen(false)}
                aria-label="Close navigation overlay"
              ></button>
              <div className="absolute top-24 left-4 right-4 rounded-3xl border border-white/25 bg-violet-900/85 p-5 shadow-2xl">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Navigate</p>
                    <p className="text-lg font-semibold text-white">Choose a mode</p>
                  </div>
                  <button
                    onClick={() => setIsMobileNavOpen(false)}
                    className="btn btn-secondary px-3 py-2"
                    aria-label="Close navigation menu"
                  >
                    <FaTimes />
                  </button>
                </div>
                <div className="grid gap-2">
                  {navItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleNavClick(item.action)}
                      className={`w-full rounded-2xl px-4 py-3 text-left font-semibold transition-all ${
                        activeMode === item.id
                          ? 'bg-white/10 text-white'
                          : 'bg-white/10 text-slate-100 hover:text-white hover:bg-white/20'
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
                {!currentUser && (
                  <div className="mt-4 grid gap-2">
                    <button
                      onClick={() => navigate('/auth?mode=signin')}
                      className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left font-semibold text-white transition hover:bg-white/10"
                    >
                      Sign in
                    </button>
                    <button
                      onClick={() => navigate('/auth?mode=signup')}
                      className="w-full rounded-2xl bg-gradient-to-r from-fuchsia-500 to-violet-500 px-4 py-3 text-left font-semibold text-white transition hover:from-fuchsia-400 hover:to-violet-400"
                    >
                      Register
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
      </header>

      {/* Main Content */}
      <div className="py-5 sm:py-8">
        <Routes>
          <Route
            path="/"
            element={<HomeScreen onModeSelect={handleModeSelect} currentUser={currentUser} />}
          />
          <Route
            path="/auth"
            element={<AuthScreen onAuthSuccess={handleAuthSuccess} onBack={handleBackToHome} />}
          />
          <Route
            path="/journey"
            element={
              currentUser ? (
                <CareerJourneyScreen onBack={handleBackToHome} user={currentUser} />
              ) : (
                <Navigate to="/auth" replace />
              )
            }
          />
          <Route
            path="/interview-coach"
            element={
              <SessionSetupNew
                onSessionStart={handleSessionStart}
                onBack={handleBackToHome}
                currentUser={currentUser}
                onRequireAuth={() => navigate('/auth?mode=signin')}
              />
            }
          />
          <Route path="/setup" element={<Navigate to="/interview-coach" replace />} />
          <Route
            path="/interview"
            element={
              session ? (
                <InterviewSession onComplete={handleSessionComplete} />
              ) : (
                <Navigate to="/interview-coach" replace />
              )
            }
          />
          <Route
            path="/summary"
            element={
              sessionSummary ? (
                <SessionSummary summary={sessionSummary} onRestart={handleRestart} currentUser={currentUser} />
              ) : (
                <Navigate to="/interview-coach" replace />
              )
            }
          />
          <Route path="/aws-study" element={<AwsStudyMode onBack={handleBackToHome} />} />
          <Route path="/exam" element={<ExamSimulator onBack={handleBackToHome} />} />
          <Route
            path="/profile"
            element={
              currentUser ? (
                <UserProfile
                  onNavigate={(next) => navigate(`/${next}`)}
                  currentUser={currentUser}
                  setCurrentUser={setCurrentUser}
                />
              ) : (
                <Navigate to="/auth" replace />
              )
            }
          />
          <Route
            path="/admin"
            element={
              currentUser ? (
                <AdminConsole currentUser={currentUser} onBack={handleBackToHome} />
              ) : (
                <Navigate to="/auth" replace />
              )
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>

      <footer className="app-footer mx-auto max-w-7xl px-4 sm:px-6 pb-6 sm:pb-10">
          <div className="rounded-3xl border border-white/10 px-4 py-6 sm:px-6 sm:py-8">
            <div className="md:hidden flex flex-col gap-4">
              <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-slate-400">
                <span>DevOps Learning Hub</span>
              </div>
              <p className="text-sm text-slate-300">
                AI study platform for interviews, journeys, and certifications.
              </p>
              <div className="flex flex-nowrap gap-2 text-xs text-slate-300 overflow-x-auto">
                {navItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleNavClick(item.action)}
                    className={`rounded-full px-2.5 py-1 border border-white/5 transition-all whitespace-nowrap ${
                      activeMode === item.id
                        ? 'bg-white/10 text-white'
                        : 'bg-white/10 text-slate-100 hover:text-white hover:bg-white/20'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="hidden md:flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="max-w-xs">
                <h3 className="text-lg font-semibold text-white">DevOps Learning Hub</h3>
                <p className="text-sm text-slate-400">AI study platform for interview prep and career growth.</p>
              </div>
              <div className="flex flex-nowrap gap-2 text-xs text-slate-300">
                {navItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleNavClick(item.action)}
                    className={`rounded-full px-2.5 py-1 border border-white/5 transition-all whitespace-nowrap ${
                      activeMode === item.id
                        ? 'bg-white/10 text-white'
                        : 'bg-white/10 text-slate-100 hover:text-white hover:bg-white/20'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
      </footer>
    </div>
  );
}

export default App;
