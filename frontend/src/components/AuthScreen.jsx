import React, { useEffect, useState } from 'react';
import { FaUser, FaEnvelope, FaLock, FaEye, FaEyeSlash, FaRocket, FaArrowLeft } from 'react-icons/fa';
import { useSearchParams } from 'react-router-dom';
import { apiService } from '../services/api';

const AuthScreen = ({ onAuthSuccess, onBack }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    full_name: ''
  });

  useEffect(() => {
    const mode = searchParams.get('mode');
    if (mode === 'signup') {
      setIsLogin(false);
    } else if (mode === 'signin') {
      setIsLogin(true);
    } else {
      return;
    }

    setError('');
    setFormData({
      email: '',
      username: '',
      password: '',
      full_name: ''
    });
  }, [searchParams]);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      let response;
      if (isLogin) {
        response = await apiService.login({
          email: formData.email,
          password: formData.password
        });
      } else {
        response = await apiService.register({
          email: formData.email,
          username: formData.username,
          password: formData.password,
          full_name: formData.full_name
        });
      }

      onAuthSuccess(response);
    } catch (err) {
      console.error('Auth error:', err);
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMode = () => {
    const nextMode = isLogin ? 'signup' : 'signin';
    setSearchParams({ mode: nextMode }, { replace: true });
    setIsLogin(nextMode === 'signin');
    setError('');
    setFormData({
      email: '',
      username: '',
      password: '',
      full_name: ''
    });
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4 sm:p-6">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-20 right-20 w-80 h-80 bg-teal-500/5 rounded-full blur-3xl animate-pulse delay-500"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl animate-pulse"></div>
      </div>

      <div className="relative w-full max-w-md">
        {/* Auth Card */}
        <div className="glass-dark rounded-3xl p-5 sm:p-8 border border-white/10 shadow-2xl">
          {onBack && (
            <button
              onClick={() => {
                setSearchParams({}, { replace: true });
                onBack();
              }}
              className="mb-5 inline-flex items-center text-sm font-semibold text-slate-300 transition hover:text-white"
            >
              <FaArrowLeft className="mr-2" />
              <span>Back to Home</span>
            </button>
          )}
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-14 h-14 sm:w-16 sm:h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-r from-cyan-500 to-teal-600 flex items-center justify-center">
              <FaRocket className="text-white text-2xl" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold mb-2 bg-gradient-to-r from-white via-cyan-200 to-teal-200 bg-clip-text text-transparent">
              {isLogin ? 'Welcome Back!' : 'Join DevOps AI'}
            </h1>
            <p className="text-sm sm:text-base text-slate-400">
              {isLogin ? 'Continue your learning journey' : 'Start your career transformation'}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Field */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <FaEnvelope className="text-slate-400" />
              </div>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Email address"
                required
                className="input-base pl-12 pr-4 py-3 sm:py-4"
              />
            </div>

            {/* Username Field (Register only) */}
            {!isLogin && (
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <FaUser className="text-slate-400" />
                </div>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  placeholder="Username"
                  required
                  className="input-base pl-12 pr-4 py-3 sm:py-4"
                />
              </div>
            )}

            {/* Full Name Field (Register only) */}
            {!isLogin && (
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <FaUser className="text-slate-400" />
                </div>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  placeholder="Full name (optional)"
                  className="input-base pl-12 pr-4 py-3 sm:py-4"
                />
              </div>
            )}

            {/* Password Field */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <FaLock className="text-slate-400" />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Password"
                required
                minLength={8}
                className="input-base pl-12 pr-12 py-3 sm:py-4"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 
                         hover:text-white transition-colors duration-300"
              >
                {showPassword ? <FaEyeSlash /> : <FaEye />}
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-4 bg-gradient-to-r from-red-500/10 to-red-500/5 border border-red-500/30 rounded-2xl">
                <p className="text-red-300 text-sm text-center">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className={`btn w-full py-4 px-8 text-lg ${isLoading ? 'btn-secondary' : 'btn-primary'}`}
            >
              {isLoading ? (
                <>
                  <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin mr-3"></div>
                  <span>{isLogin ? 'Signing in...' : 'Creating account...'}</span>
                </>
              ) : (
                <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
              )}
            </button>
          </form>

          {/* Toggle Mode */}
          <div className="mt-8 text-center">
            <p className="text-slate-400 mb-4">
              {isLogin ? "Don't have an account?" : "Already have an account?"}
            </p>
            <button
              onClick={toggleMode}
              className="text-cyan-400 hover:text-cyan-300 font-semibold transition-colors duration-300 
                       hover:underline underline-offset-4"
            >
              {isLogin ? 'Create Account' : 'Sign In'}
            </button>
          </div>

          {/* Features Preview (Register mode) */}
          {!isLogin && (
            <div className="mt-8 pt-6 border-t border-white/10">
              <p className="text-sm text-slate-400 text-center mb-4">Join DevOps AI and get:</p>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex items-center text-slate-300">
                  <div className="w-2 h-2 bg-cyan-400 rounded-full mr-2"></div>
                  Personalized Learning Paths
                </div>
                <div className="flex items-center text-slate-300">
                  <div className="w-2 h-2 bg-teal-400 rounded-full mr-2"></div>
                  Progress Tracking
                </div>
                <div className="flex items-center text-slate-300">
                  <div className="w-2 h-2 bg-cyan-300 rounded-full mr-2"></div>
                  Career Roadmaps
                </div>
                <div className="flex items-center text-slate-300">
                  <div className="w-2 h-2 bg-teal-300 rounded-full mr-2"></div>
                  Achievement System
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthScreen;