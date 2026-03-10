import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

const UserProfile = ({ onNavigate, currentUser, setCurrentUser }) => {
  const apiOrigin = 'http://localhost:8000';
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    career_track: '',
    experience_level: ''
  });
  const [dashboard, setDashboard] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAvatarUploading, setIsAvatarUploading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    if (currentUser) {
      setFormData({
        full_name: currentUser.full_name || '',
        career_track: currentUser.career_track || '',
        experience_level: currentUser.experience_level || ''
      });
    }
  }, [currentUser]);

  useEffect(() => {
    const loadDashboard = async () => {
      if (!currentUser) return;
      try {
        const [dashboardData, analyticsData] = await Promise.all([
          apiService.getDashboard(),
          apiService.getInterviewAnalytics(),
        ]);
        setDashboard(dashboardData);
        setAnalytics(analyticsData);
      } catch (error) {
        console.error('Failed to load dashboard:', error);
      }
    };

    loadDashboard();
  }, [currentUser]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const resolveAvatarUrl = (path) => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    if (path.startsWith('/')) return `${apiOrigin}${path}`;
    return `${apiOrigin}/${path}`;
  };

  const handleAvatarChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsAvatarUploading(true);
    setMessage({ type: '', text: '' });

    try {
      const updatedUser = await apiService.uploadAvatar(file);
      setCurrentUser(updatedUser);
      setMessage({ type: 'success', text: 'Profile photo updated.' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error('Failed to upload avatar:', error);
      setMessage({ type: 'error', text: 'Avatar upload failed. Please try again.' });
    } finally {
      setIsAvatarUploading(false);
      event.target.value = '';
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    setMessage({ type: '', text: '' });
    
    try {
      const updatedUser = await apiService.updateProfile(formData);
      setCurrentUser(updatedUser);
      setIsEditing(false);
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error('Failed to update profile:', error);
      setMessage({ type: 'error', text: 'Failed to update profile. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      full_name: currentUser?.full_name || '',
      career_track: currentUser?.career_track || '',
      experience_level: currentUser?.experience_level || ''
    });
    setIsEditing(false);
    setMessage({ type: '', text: '' });
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-white">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 sm:p-6">
      {/* Header */}
      <div className="max-w-4xl mx-auto mb-6 sm:mb-8">
        <div className="flex items-center justify-between mb-5 sm:mb-6">
          <button 
            onClick={() => onNavigate('home')}
            className="btn btn-ghost px-0 py-0 text-cyan-400 hover:text-cyan-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Home
          </button>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">User Profile</h1>
          <div className="w-16"></div> {/* Spacer */}
        </div>

        {/* Message */}
        {message.text && (
          <div className={`mb-6 p-4 rounded-2xl ${
            message.type === 'success' 
              ? 'bg-cyan-500/20 border border-cyan-500 text-cyan-300' 
              : 'bg-red-500/20 border border-red-500 text-red-400'
          }`}>
            {message.text}
          </div>
        )}
      </div>

      {/* Profile Content */}
      <div className="max-w-4xl mx-auto">
        <div className="glass-dark rounded-3xl border border-white/10 p-5 sm:p-8">
          
          {/* Profile Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 sm:mb-8">
            <div className="flex items-center gap-6">
              <div className="relative">
                <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-cyan-500 to-teal-600 rounded-full flex items-center justify-center overflow-hidden">
                  {currentUser.profile_picture ? (
                    <img
                      src={resolveAvatarUrl(currentUser.profile_picture)}
                      alt="Profile"
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <span className="text-xl sm:text-2xl font-bold text-white">
                      {(currentUser.full_name || currentUser.username || 'U').charAt(0).toUpperCase()}
                    </span>
                  )}
                </div>
                <label className="mt-3 inline-flex cursor-pointer items-center justify-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-slate-200 transition hover:bg-white/10">
                  {isAvatarUploading ? 'Uploading...' : 'Change photo'}
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarChange}
                    className="hidden"
                    disabled={isAvatarUploading}
                  />
                </label>
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-white mb-1">
                  {currentUser.full_name || currentUser.username}
                </h2>
                <p className="text-gray-300">{currentUser.email}</p>
                <p className="text-sm text-gray-400">
                  Member since {new Date(currentUser.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            
            {!isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="btn btn-info px-5 sm:px-6 py-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Edit Profile
              </button>
            )}
          </div>

          {/* Profile Details */}
          <div className="space-y-5 sm:space-y-6">
            
            {/* Full Name */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Full Name
              </label>
              {isEditing ? (
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  className="input-base px-4 py-2.5 sm:py-3"
                  placeholder="Enter your full name"
                />
              ) : (
                <div className="px-4 py-2.5 sm:py-3 bg-white/5 rounded-2xl text-white">
                  {currentUser.full_name || 'Not provided'}
                </div>
              )}
            </div>

            {/* Career Track */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Career Track
              </label>
              {isEditing ? (
                <select
                  name="career_track"
                  value={formData.career_track}
                  onChange={handleInputChange}
                  className="select-base px-4 py-2.5 sm:py-3"
                >
                  <option value="" className="bg-slate-800">Select career track</option>
                  <option value="cloud_engineering" className="bg-slate-800">Cloud Engineering</option>
                  <option value="devops_platform" className="bg-slate-800">DevOps/Platform Engineering</option>
                  <option value="hybrid" className="bg-slate-800">Hybrid (Cloud + DevOps)</option>
                </select>
              ) : (
                <div className="px-4 py-2.5 sm:py-3 bg-white/5 rounded-2xl text-white">
                  {currentUser.career_track ? (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                      {currentUser.career_track === 'cloud_engineering' && '☁️ Cloud Engineering'}
                      {currentUser.career_track === 'devops_platform' && '⚙️ DevOps/Platform Engineering'}
                      {currentUser.career_track === 'hybrid' && '🌐 Hybrid (Cloud + DevOps)'}
                    </span>
                  ) : (
                    'Not selected'
                  )}
                </div>
              )}
            </div>

            {/* Experience Level */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Experience Level
              </label>
              {isEditing ? (
                <select
                  name="experience_level"
                  value={formData.experience_level}
                  onChange={handleInputChange}
                  className="select-base px-4 py-2.5 sm:py-3"
                >
                  <option value="" className="bg-slate-800">Select experience level</option>
                  <option value="junior" className="bg-slate-800">Junior (0-2 years)</option>
                  <option value="mid" className="bg-slate-800">Mid-level (2-5 years)</option>
                  <option value="senior" className="bg-slate-800">Senior (5+ years)</option>
                </select>
              ) : (
                <div className="px-4 py-2.5 sm:py-3 bg-white/5 rounded-2xl text-white">
                  {currentUser.experience_level ? (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-teal-500/20 text-teal-300 border border-teal-500/30">
                      {currentUser.experience_level === 'junior' && '🌱 Junior (0-2 years)'}
                      {currentUser.experience_level === 'mid' && '🌿 Mid-level (2-5 years)'}
                      {currentUser.experience_level === 'senior' && '🌳 Senior (5+ years)'}
                    </span>
                  ) : (
                    'Not selected'
                  )}
                </div>
              )}
            </div>

            {/* Email (Read-only) */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email Address
              </label>
              <div className="px-4 py-2.5 sm:py-3 bg-white/5 rounded-2xl text-gray-400">
                {currentUser.email}
                <span className="text-xs ml-2">(cannot be changed)</span>
              </div>
            </div>

            {/* Username (Read-only) */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Username
              </label>
              <div className="px-4 py-2.5 sm:py-3 bg-white/5 rounded-2xl text-gray-400">
                {currentUser.username}
                <span className="text-xs ml-2">(cannot be changed)</span>
              </div>
            </div>

          </div>

          {dashboard && (
            <div className="mt-8 space-y-6">
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Sessions</p>
                  <p className="mt-2 text-2xl font-semibold text-white">
                    {dashboard.stats.total_sessions}
                  </p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Avg Score</p>
                  <p className="mt-2 text-2xl font-semibold text-white">
                    {dashboard.stats.average_session_score}
                  </p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Current Streak</p>
                  <p className="mt-2 text-2xl font-semibold text-white">
                    {dashboard.stats.current_streak} days
                  </p>
                </div>
              </div>

              {analytics && (
                <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-5">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <h3 className="text-lg font-semibold text-white">Performance Analytics</h3>
                    <span className="text-xs text-slate-400">Updated {new Date(analytics.last_updated).toLocaleString()}</span>
                  </div>

                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Interview Readiness</p>
                      <p className="mt-2 text-2xl font-semibold text-white">{analytics.interview_readiness.toFixed(1)} / 10</p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Questions Analyzed</p>
                      <p className="mt-2 text-2xl font-semibold text-white">{analytics.total_answered_questions}</p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Benchmark Percentile</p>
                      <p className="mt-2 text-2xl font-semibold text-white">{analytics.benchmark_percentile.toFixed(1)}%</p>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <p className="text-sm font-semibold text-white">{analytics.technical_accuracy.name}</p>
                      <p className="mt-1 text-slate-300">Score: {analytics.technical_accuracy.score.toFixed(1)} / 10</p>
                      <p className="text-xs text-slate-400">Benchmark: {analytics.technical_accuracy.benchmark.toFixed(1)} · {analytics.technical_accuracy.status.replaceAll('_', ' ')}</p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <p className="text-sm font-semibold text-white">{analytics.communication_effectiveness.name}</p>
                      <p className="mt-1 text-slate-300">Score: {analytics.communication_effectiveness.score.toFixed(1)} / 10</p>
                      <p className="text-xs text-slate-400">Benchmark: {analytics.communication_effectiveness.benchmark.toFixed(1)} · {analytics.communication_effectiveness.status.replaceAll('_', ' ')}</p>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4">
                      <p className="text-sm font-semibold text-emerald-200">Strength Highlights</p>
                      <ul className="mt-2 space-y-2 text-sm text-slate-200">
                        {(analytics.strengths || []).slice(0, 4).map((item, index) => (
                          <li key={`strength-${index}`} className="flex items-start gap-2">
                            <span className="text-emerald-300">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4">
                      <p className="text-sm font-semibold text-amber-200">Improvement Focus</p>
                      <ul className="mt-2 space-y-2 text-sm text-slate-200">
                        {(analytics.improvement_areas || []).slice(0, 4).map((item, index) => (
                          <li key={`improve-${index}`} className="flex items-start gap-2">
                            <span className="text-amber-300">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-sm font-semibold text-white">Platform Breakdown</p>
                    <div className="mt-3 grid gap-2 sm:grid-cols-3">
                      {(analytics.platform_breakdown || []).length === 0 ? (
                        <p className="text-sm text-slate-400">No platform data yet.</p>
                      ) : (
                        analytics.platform_breakdown.map((item) => (
                          <div key={item.platform} className="rounded-xl border border-white/10 bg-slate-800/60 px-3 py-2">
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{item.platform}</p>
                            <p className="text-sm text-white">{item.average_score.toFixed(1)} avg</p>
                            <p className="text-xs text-slate-400">{item.sessions} sessions</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-5">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">Interview History</h3>
                  <span className="text-xs text-slate-400">Last {dashboard.interview_history.length} sessions</span>
                </div>
                <div className="mt-4 space-y-3">
                  {dashboard.interview_history.length === 0 ? (
                    <p className="text-sm text-slate-400">No sessions yet. Start an interview to build your history.</p>
                  ) : (
                    dashboard.interview_history.map((session) => (
                      <div
                        key={session.session_id}
                        className="flex flex-col gap-2 rounded-2xl border border-white/5 bg-white/5 p-4 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div>
                          <p className="text-sm font-semibold text-white">
                            {session.platform.toUpperCase()} · {session.difficulty}
                          </p>
                          <p className="text-xs text-slate-400">
                            {new Date(session.started_at).toLocaleString()}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-200">
                            {session.status}
                          </span>
                          <span className="text-sm text-slate-200">
                            Score: {session.score ?? 'N/A'}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-5">
                <h3 className="text-lg font-semibold text-white">Recommended Paths</h3>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {dashboard.recommended_paths.length === 0 ? (
                    <p className="text-sm text-slate-400">Recommendations will appear after your first session.</p>
                  ) : (
                    dashboard.recommended_paths.map((path) => (
                      <div key={path.path_id} className="rounded-2xl border border-white/5 bg-white/5 p-4">
                        <p className="text-sm font-semibold text-white">{path.name}</p>
                        <p className="mt-1 text-xs text-slate-400">{path.estimated_duration}</p>
                        <p className="mt-2 text-xs text-slate-300 line-clamp-2">{path.description}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {isEditing && (
            <div className="mt-6 sm:mt-8 flex gap-3 sm:gap-4 justify-end">
              <button
                onClick={handleCancel}
                disabled={isLoading}
                className="btn btn-secondary px-5 sm:px-6 py-2"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isLoading}
                className="btn btn-success px-5 sm:px-6 py-2"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Save Changes
                  </>
                )}
              </button>
            </div>
          )}

          {/* Account Info */}
          <div className="mt-8 pt-6 border-t border-white/20">
            <h3 className="text-lg font-semibold text-white mb-4">Account Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-cyan-400 rounded-full"></div>
                <span className="text-gray-300">Account Active</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-teal-400 rounded-full"></div>
                <span className="text-gray-300">Last Login: {new Date(currentUser.last_login || currentUser.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default UserProfile;