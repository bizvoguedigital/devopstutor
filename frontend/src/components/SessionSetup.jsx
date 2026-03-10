import React, { useState } from 'react';
import { FaAws, FaMicrosoft, FaGoogle, FaDocker, FaArrowLeft, FaRocket, FaStar, FaChartLine, FaUserGraduate, FaBolt, FaCheck } from 'react-icons/fa';
import { apiService } from '../services/api';
import { useInterviewStore } from '../store/interviewStore';

const platforms = [
  { 
    id: 'aws', 
    name: 'AWS', 
    icon: FaAws, 
    color: 'text-cyan-300', 
    gradient: 'from-cyan-500 to-teal-600',
    bgGradient: 'from-cyan-500/10 to-teal-500/10',
    borderGradient: 'from-cyan-500 to-teal-500',
    description: 'Amazon Web Services',
    scenarios: ['EC2 & Auto Scaling', 'Lambda & Serverless', 'VPC & Networking', 'CloudFormation', 'EKS & Containers']
  },
  { 
    id: 'azure', 
    name: 'Azure', 
    icon: FaMicrosoft, 
    color: 'text-cyan-300', 
    gradient: 'from-cyan-500 to-teal-600',
    bgGradient: 'from-cyan-500/10 to-teal-500/10',
    borderGradient: 'from-cyan-500 to-teal-500',
    description: 'Microsoft Azure',
    scenarios: ['Virtual Machines & Scale Sets', 'Azure Functions', 'Resource Manager', 'AKS & Containers', 'DevOps Pipelines']
  },
  { 
    id: 'gcp', 
    name: 'GCP', 
    icon: FaGoogle, 
    color: 'text-cyan-300', 
    gradient: 'from-cyan-500 to-teal-600',
    bgGradient: 'from-cyan-500/10 to-teal-500/10',
    borderGradient: 'from-cyan-500 to-teal-500',
    description: 'Google Cloud Platform',
    scenarios: ['Compute Engine & GKE', 'Cloud Functions', 'VPC & Networking', 'Cloud Build', 'Infrastructure as Code']
  },
  { 
    id: 'devops', 
    name: 'DevOps/Platform', 
    icon: FaDocker, 
    color: 'text-cyan-300', 
    gradient: 'from-cyan-500 to-teal-600',
    bgGradient: 'from-cyan-500/10 to-teal-500/10',
    borderGradient: 'from-cyan-500 to-teal-500',
    description: 'DevOps & Platform Engineering',
    scenarios: ['CI/CD Pipelines', 'Infrastructure as Code', 'Monitoring & Observability', 'Container Orchestration', 'Site Reliability']
  },
];

const difficulties = [
  { 
    id: 'junior', 
    name: 'Junior Developer', 
    description: '0-2 years experience', 
    icon: FaUserGraduate,
    gradient: 'from-teal-500 to-cyan-600',
    bgGradient: 'from-teal-500/10 to-cyan-500/10',
    borderGradient: 'from-teal-500 to-cyan-500',
    features: ['Basic concepts', 'Fundamental questions', 'Entry-level scenarios']
  },
  { 
    id: 'mid', 
    name: 'Mid-Level Engineer', 
    description: '2-5 years experience', 
    icon: FaChartLine,
    gradient: 'from-teal-500 to-cyan-600',
    bgGradient: 'from-teal-500/10 to-cyan-500/10',
    borderGradient: 'from-teal-500 to-cyan-500',
    features: ['Architecture design', 'Best practices', 'Problem-solving']
  },
  { 
    id: 'senior', 
    name: 'Senior Expert', 
    description: '5+ years experience', 
    icon: FaStar,
    gradient: 'from-teal-500 to-cyan-600',
    bgGradient: 'from-teal-500/10 to-cyan-500/10',
    borderGradient: 'from-teal-500 to-cyan-500',
    features: ['System design', 'Leadership scenarios', 'Advanced concepts']
  },
];

export default function SessionSetup({ onSessionStart, onBack }) {
  const [selectedPlatform, setSelectedPlatform] = useState('aws');
  const [selectedDifficulty, setSelectedDifficulty] = useState('mid');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const setSession = useInterviewStore((state) => state.setSession);

  const handleStartInterview = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const session = await apiService.createSession(selectedPlatform, selectedDifficulty);
      setSession(session);
      onSessionStart(session);
    } catch (err) {
      setError('Failed to start interview. Make sure the backend is running.');
      console.error('Error starting interview:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const selectedPlatformData = platforms.find(p => p.id === selectedPlatform);
  const selectedDifficultyData = difficulties.find(d => d.id === selectedDifficulty);

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-32 right-20 w-80 h-80 bg-teal-500/5 rounded-full blur-3xl animate-pulse"></div>
      </div>

      <div className="relative max-w-6xl mx-auto px-4 sm:px-6 py-5 sm:py-8">
        {/* Header */}
        <div className="flex items-center mb-8 sm:mb-12">
          {onBack && (
            <button
              onClick={onBack}
              className="btn btn-secondary mr-6 px-3 py-2"
            >
              <FaArrowLeft className="mr-2 group-hover:-translate-x-1 transition-transform duration-300" />
              <span className="font-medium">Back to Home</span>
            </button>
          )}
          
          <div className="flex-1">
            <h1 className="text-3xl sm:text-5xl font-bold mb-2 sm:mb-3 bg-gradient-to-r from-white via-cyan-200 to-teal-200 bg-clip-text text-transparent">
              Interview Setup
            </h1>
            <p className="text-base sm:text-xl text-slate-400">
              Configure your AI interview session for the best learning experience
            </p>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-5 sm:gap-8">
          {/* Platform Selection */}
          <div className="lg:col-span-2 space-y-8">
            {/* Cloud Platform Section */}
            <div className="glass-dark rounded-3xl p-5 sm:p-8 border border-white/10">
              <div className="flex items-center mb-6 sm:mb-8">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-r from-cyan-500 to-teal-600 flex items-center justify-center mr-4">
                  <FaBolt className="text-white text-xl" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-white mb-1">🌩️ Cloud Platform & DevOps Focus</h2>
                  <p className="text-slate-400">Choose your specialization for scenario-based interviews</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 sm:gap-6">
                {platforms.map((platform) => {
                  const Icon = platform.icon;
                  const isSelected = selectedPlatform === platform.id;
                  return (
                    <button
                      key={platform.id}
                      onClick={() => setSelectedPlatform(platform.id)}
                      className={`group relative p-4 sm:p-6 rounded-2xl transition-all duration-300 ${
                        isSelected
                          ? `select-card select-card-active bg-gradient-to-br ${platform.bgGradient} border-2 border-transparent scale-105 shadow-lg shadow-cyan-500/20`
                          : 'select-card border-2 hover:scale-105'
                      }`}
                    >
                      {isSelected && (
                        <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-r from-cyan-400 to-teal-500 rounded-full flex items-center justify-center">
                          <FaCheck className="text-white text-sm" />
                        </div>
                      )}
                      
                      <div className={`w-14 h-14 sm:w-16 sm:h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br ${platform.gradient} flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                        <Icon className="text-2xl text-white" />
                      </div>
                      
                      <h3 className={`font-bold text-base sm:text-lg mb-2 transition-colors duration-300 ${
                        isSelected ? 'text-white' : 'text-slate-300 group-hover:text-white'
                      }`}>
                        {platform.name}
                      </h3>
                      
                      <p className={`text-sm transition-colors duration-300 ${
                        isSelected ? 'text-slate-200' : 'text-slate-400 group-hover:text-slate-300'
                      }`}>
                        {platform.description}
                      </p>
                      
                      {/* Scenario Preview */}
                      {isSelected && platform.scenarios && (
                        <div className="mt-4 pt-4 border-t border-white/10">
                          <p className="text-xs text-slate-300 mb-2">Scenario Topics:</p>
                          <div className="flex flex-wrap gap-1">
                            {platform.scenarios.slice(0, 3).map((scenario, idx) => (
                              <span key={idx} className="chip text-xs">
                                {scenario}
                              </span>
                            ))}
                            {platform.scenarios.length > 3 && (
                              <span className="text-xs text-slate-400">+{platform.scenarios.length - 3} more</span>
                            )}
                          </div>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Difficulty Selection */}
            <div className="glass-dark rounded-3xl p-5 sm:p-8 border border-white/10">
              <div className="flex items-center mb-6 sm:mb-8">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-r from-cyan-500 to-teal-600 flex items-center justify-center mr-4">
                  <FaChartLine className="text-white text-xl" />
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-white mb-1">Select Difficulty Level</h2>
                  <p className="text-slate-400">Match your experience level</p>
                </div>
              </div>
              
              <div className="space-y-3 sm:space-y-4">
                {difficulties.map((difficulty) => {
                  const Icon = difficulty.icon;
                  const isSelected = selectedDifficulty === difficulty.id;
                  return (
                    <button
                      key={difficulty.id}
                      onClick={() => setSelectedDifficulty(difficulty.id)}
                      className={`group relative w-full p-4 sm:p-6 rounded-2xl transition-all duration-300 text-left ${
                        isSelected
                          ? `select-card select-card-active bg-gradient-to-br ${difficulty.bgGradient} border-2 border-transparent scale-[1.02] shadow-lg shadow-cyan-500/20`
                          : 'select-card border-2 hover:scale-[1.02]'
                      }`}
                    >
                      {isSelected && (
                        <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-r from-cyan-400 to-teal-500 rounded-full flex items-center justify-center">
                          <FaCheck className="text-white text-sm" />
                        </div>
                      )}
                      
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center mb-3">
                            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${difficulty.gradient} flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300`}>
                              <Icon className="text-white text-lg" />
                            </div>
                            <div>
                              <h3 className={`font-bold text-lg transition-colors duration-300 ${
                                isSelected ? 'text-white' : 'text-slate-300 group-hover:text-white'
                              }`}>
                                {difficulty.name}
                              </h3>
                              <p className={`text-sm transition-colors duration-300 ${
                                isSelected ? 'text-slate-200' : 'text-slate-400 group-hover:text-slate-300'
                              }`}>
                                {difficulty.description}
                              </p>
                            </div>
                          </div>
                          
                          <div className="flex flex-wrap gap-2">
                            {difficulty.features.map((feature, index) => (
                              <span 
                                key={index}
                                className={`chip transition-colors duration-300 ${isSelected ? 'chip-active' : 'group-hover:text-white'}`}
                              >
                                {feature}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Summary & Start Section */}
            <div className="space-y-4 sm:space-y-6">
            {/* Configuration Summary */}
            <div className="glass-dark rounded-3xl p-5 sm:p-8 border border-white/10 sticky top-8">
              <h3 className="text-lg sm:text-xl font-bold mb-4 sm:mb-6 text-center text-white">Interview Configuration</h3>
              
              {/* Selected Platform Summary */}
              <div className="mb-6">
                <div className="flex items-center p-4 rounded-2xl bg-gradient-to-r from-slate-700/50 to-slate-600/50 border border-white/10">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${selectedPlatformData.gradient} flex items-center justify-center mr-4`}>
                    <selectedPlatformData.icon className="text-white text-xl" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">Platform</p>
                    <p className="font-semibold text-white">{selectedPlatformData.name}</p>
                  </div>
                </div>
              </div>

              {/* Selected Difficulty Summary */}
              <div className="mb-8">
                <div className="flex items-center p-4 rounded-2xl bg-gradient-to-r from-slate-700/50 to-slate-600/50 border border-white/10">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${selectedDifficultyData.gradient} flex items-center justify-center mr-4`}>
                    <selectedDifficultyData.icon className="text-white text-xl" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">Difficulty</p>
                    <p className="font-semibold text-white">{selectedDifficultyData.name}</p>
                  </div>
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="mb-6 p-4 bg-gradient-to-r from-red-500/10 to-red-500/5 border border-red-500/30 rounded-2xl">
                  <p className="text-red-300 text-sm">{error}</p>
                </div>
              )}

              {/* Start Button */}
              <button
                onClick={handleStartInterview}
                disabled={isLoading}
                className={`btn w-full py-4 px-8 text-lg ${isLoading ? 'btn-secondary' : 'btn-primary'}`}
              >
                {isLoading ? (
                  <>
                    <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin mr-3"></div>
                    <span>Starting Interview...</span>
                  </>
                ) : (
                  <>
                    <FaRocket className="mr-3 group-hover:animate-pulse" />
                    <span>Start Interview</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
