import React, { useState, useEffect } from 'react';
import { 
  FaCloud, FaServer, FaLayerGroup, FaArrowLeft, FaRocket, FaUsers, 
  FaCode, FaChartLine, FaCog, FaShieldAlt, FaGraduationCap, FaRoute,
  FaBookmark, FaHome, FaEye, FaCheckCircle, FaTasks, FaUserCircle
} from 'react-icons/fa';
import { apiService } from '../services/api';

const careerTracks = [
  {
    id: 'cloud_engineering',
    name: 'Cloud Engineering',
    icon: FaCloud,
    gradient: 'from-cyan-500 to-teal-600',
    bgGradient: 'from-cyan-500/10 to-teal-500/10',
    borderGradient: 'from-cyan-500 to-teal-500',
    description: 'Focus on cloud infrastructure, services, and architecture',
    skills: ['Cloud Architecture', 'Infrastructure as Code', 'Networking', 'Security', 'Cost Optimization'],
    platforms: ['AWS', 'Azure', 'GCP'],
    roles: ['Cloud Architect', 'Cloud Engineer', 'Solutions Architect'],
    avgSalary: '$95,000 - $160,000'
  },
  {
    id: 'devops_platform',
    name: 'DevOps & Platform Engineering',
    icon: FaCog,
    gradient: 'from-cyan-500 to-teal-600',
    bgGradient: 'from-cyan-500/10 to-teal-500/10',
    borderGradient: 'from-cyan-500 to-teal-500',
    description: 'Focus on CI/CD, automation, and platform engineering',
    skills: ['CI/CD', 'Containerization', 'Orchestration', 'Monitoring', 'Automation'],
    platforms: ['Kubernetes', 'Docker', 'Jenkins', 'GitLab'],
    roles: ['DevOps Engineer', 'Platform Engineer', 'SRE'],
    avgSalary: '$90,000 - $155,000'
  },
  {
    id: 'hybrid',
    name: 'Hybrid Cloud-DevOps',
    icon: FaLayerGroup,
    gradient: 'from-cyan-500 to-teal-600',
    bgGradient: 'from-cyan-500/10 to-teal-500/10',
    borderGradient: 'from-cyan-500 to-teal-500',
    description: 'Balanced approach covering both cloud and DevOps expertise',
    skills: ['Cloud Platforms', 'DevOps Practices', 'Infrastructure Automation', 'Security', 'Monitoring'],
    platforms: ['AWS', 'Kubernetes', 'Terraform', 'Docker'],
    roles: ['Cloud DevOps Engineer', 'Infrastructure Engineer', 'Technical Lead'],
    avgSalary: '$100,000 - $170,000'
  }
];

const experienceLevels = [
  {
    id: 'junior',
    name: 'Junior',
    description: '0-2 years experience',
    icon: FaGraduationCap,
    color: 'cyan',
    features: ['Fundamentals', 'Guided Learning', 'Basic Concepts']
  },
  {
    id: 'mid',
    name: 'Mid-Level',
    description: '2-5 years experience',
    icon: FaChartLine,
    color: 'teal',
    features: ['Architecture', 'Best Practices', 'Problem Solving']
  },
  {
    id: 'senior',
    name: 'Senior',
    description: '5+ years experience',
    icon: FaUsers,
    color: 'cyan',
    features: ['Leadership', 'System Design', 'Advanced Concepts']
  }
];

const CareerJourneyScreen = ({ onBack, user }) => {
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [selectedPlatform, setSelectedPlatform] = useState('aws');
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [journeyPlan, setJourneyPlan] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1); // 1: Select Track, 2: Select Level, 3: Journey Results
  const [topicProgressMap, setTopicProgressMap] = useState({});
  const [moduleProgressMap, setModuleProgressMap] = useState({});
  const [moduleAssessmentProgressMap, setModuleAssessmentProgressMap] = useState({});
  const [mcqState, setMcqState] = useState({});
  const [moduleAssessmentState, setModuleAssessmentState] = useState({});
  const [activeModule, setActiveModule] = useState(null);
  const [activeTopic, setActiveTopic] = useState(null);
  const [pendingResetModule, setPendingResetModule] = useState(null);

  const overallProgress = Math.round(journeyPlan?.overall_progress || 0);
  const moduleProgressList = journeyPlan?.module_progress || [];
  const completedModules = moduleProgressList.filter((item) => item.is_completed).length;
  const totalModules = journeyPlan?.modules?.length || 0;
  const totalTopics = journeyPlan?.modules?.reduce(
    (sum, module) => sum + (module.topics?.length || 0),
    0
  ) || 0;
  const completedTopics = journeyPlan?.topic_progress?.filter((item) => item.is_completed).length || 0;
  const profileInitials = (user?.full_name || user?.username || 'Guest')
    .split(' ')
    .slice(0, 2)
    .map((name) => name[0]?.toUpperCase())
    .join('') || 'G';

  // Auto-select based on user profile if available
  useEffect(() => {
    if (user?.career_track) {
      setSelectedTrack(user.career_track);
    }
    if (user?.experience_level) {
      setSelectedLevel(user.experience_level);
    }
  }, [user]);

  const handleTrackSelect = (trackId) => {
    setSelectedTrack(trackId);
    if (trackId !== 'cloud_engineering') {
      setSelectedPlatform('aws');
    }
    setError('');
  };

  const handleLevelSelect = (levelId) => {
    setSelectedLevel(levelId);
    setError('');
  };

  const handleGenerateJourney = async () => {
    if (!selectedTrack || !selectedLevel) return;

    setIsLoading(true);
    setError('');

    try {
      const response = await apiService.getJourneyPlan({
        career_track: selectedTrack,
        experience_level: selectedLevel,
        cloud_provider: selectedTrack === 'cloud_engineering' ? selectedPlatform : null,
        preferred_platforms: selectedTrack === 'cloud_engineering' ? [selectedPlatform] : [],
        learning_goals: []
      });

      setJourneyPlan(response);
      hydrateProgress(response);
      setStep(3);
    } catch (err) {
      console.error('Error generating journey:', err);
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string' && detail.trim()) {
        setError(detail);
      } else {
        setError('Failed to generate career journey. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartJourney = async (pathId) => {
    if (!user) {
      setError('Please sign in to save your journey.');
      return;
    }
    try {
      await apiService.startLearningPath(pathId);
      // Save the journey to user profile
      setError('✅ Learning path saved to your profile! You can now view your progress.');
      setTimeout(() => setError(''), 4000);
    } catch (err) {
      console.error('Error starting learning path:', err);
      setError('❌ Failed to start learning path. Please try again.');
    }
  };


  const hydrateProgress = (plan) => {
    const progressMap = {};
    const moduleMap = {};
    const moduleAssessmentMap = {};
    (plan?.topic_progress || []).forEach((item) => {
      progressMap[`${item.module_id}:${item.topic_id}`] = item;
    });
    (plan?.module_progress || []).forEach((item) => {
      moduleMap[item.module_id] = item;
    });
    (plan?.module_assessment_progress || []).forEach((item) => {
      moduleAssessmentMap[item.module_id] = item;
    });
    setTopicProgressMap(progressMap);
    setModuleProgressMap(moduleMap);
    setModuleAssessmentProgressMap(moduleAssessmentMap);
  };

  const refreshJourneyPlan = async () => {
    if (!selectedTrack || !selectedLevel) return;
    try {
      const response = await apiService.getJourneyPlan({
        career_track: selectedTrack,
        experience_level: selectedLevel,
        cloud_provider: selectedTrack === 'cloud_engineering' ? selectedPlatform : null,
        preferred_platforms: selectedTrack === 'cloud_engineering' ? [selectedPlatform] : [],
        learning_goals: []
      });
      setJourneyPlan(response);
      hydrateProgress(response);
    } catch (err) {
      console.error('Error refreshing journey:', err);
    }
  };

  const handleScenarioComplete = async (moduleId, topicId) => {
    if (!user) {
      setError('Please sign in to save progress.');
      return;
    }

    try {
      await apiService.updateTopicProgress({
        module_id: moduleId,
        topic_id: topicId,
        scenario_completed: true,
        time_spent_minutes: 15
      });
      await refreshJourneyPlan();
    } catch (err) {
      console.error('Error updating scenario progress:', err);
      setError('Failed to save scenario progress.');
    }
  };

  const handleMcqSubmit = async (moduleId, topicId, selectedOption) => {
    if (!user) {
      setError('Please sign in to save progress.');
      return;
    }

    setMcqState((prev) => ({
      ...prev,
      [`${moduleId}:${topicId}`]: {
        ...prev[`${moduleId}:${topicId}`],
        selectedOption,
        submitted: true
      }
    }));

    try {
      await apiService.updateTopicProgress({
        module_id: moduleId,
        topic_id: topicId,
        mcq_answer: selectedOption,
        time_spent_minutes: 5
      });
      await refreshJourneyPlan();
    } catch (err) {
      console.error('Error updating MCQ progress:', err);
      setError('Failed to save MCQ progress.');
    }
  };

  const handleModuleMcqSubmit = (moduleId, index, selectedOption) => {
    if (!user) {
      setError('Please sign in to save progress.');
      return;
    }
    setModuleAssessmentState((prev) => {
      const existing = prev[moduleId] || { answers: {} };
      return {
        ...prev,
        [moduleId]: {
          ...existing,
          answers: {
            ...existing.answers,
            [index]: {
              selectedOption,
              submitted: true
            }
          }
        }
      };
    });

    apiService.updateModuleAssessment({
      module_id: moduleId,
      mcq_index: index,
      mcq_answer: selectedOption
    }).then(refreshJourneyPlan).catch((err) => {
      console.error('Error updating module assessment:', err);
      setError('Failed to save module checkpoint progress.');
    });
  };

  const handleModuleScenarioComplete = async (moduleId) => {
    if (!user) {
      setError('Please sign in to save progress.');
      return;
    }

    try {
      await apiService.updateModuleAssessment({
        module_id: moduleId,
        scenario_completed: true
      });
      await refreshJourneyPlan();
    } catch (err) {
      console.error('Error updating module scenario:', err);
      setError('Failed to save module checkpoint progress.');
    }
  };

  const handleModuleAssessmentReset = async (moduleId) => {
    if (!user) {
      setError('Please sign in to save progress.');
      return;
    }

    try {
      await apiService.resetModuleAssessment({ module_id: moduleId });
      setModuleAssessmentState((prev) => ({
        ...prev,
        [moduleId]: { answers: {} }
      }));
      await refreshJourneyPlan();
      setError('✅ Checkpoint reset. You can try again.');
      setTimeout(() => setError(''), 3000);
    } catch (err) {
      console.error('Error resetting module assessment:', err);
      setError('Failed to reset module checkpoint.');
    }
  };

  const selectedTrackData = careerTracks.find(t => t.id === selectedTrack);
  const isCloudTrack = selectedTrack === 'cloud_engineering';
  const platformOptions = [
    { id: 'aws', label: 'AWS' },
    { id: 'azure', label: 'Azure' },
    { id: 'gcp', label: 'GCP' },
  ];

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-32 right-20 w-80 h-80 bg-teal-500/5 rounded-full blur-3xl animate-pulse"></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-5 sm:py-8">
        {/* Header */}
        <div className="journey-header rounded-3xl border border-white/10 px-4 py-5 sm:px-8 sm:py-6 mb-8 sm:mb-10">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-500 via-teal-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <FaRoute className="text-white text-xl" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">DevOps Learning Hub</p>
                <h1 className="text-2xl sm:text-3xl font-semibold text-white">Career Journey Studio</h1>
              </div>
            </div>

            <div className="hidden lg:block flex-1 lg:px-6">
              <div className="flex items-center justify-between text-xs uppercase tracking-[0.25em] text-slate-400">
                <span>Journey Progress</span>
                <span>{overallProgress}%</span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-slate-900/70 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-400 via-teal-400 to-cyan-400 transition-all duration-500"
                  style={{ width: `${overallProgress}%` }}
                ></div>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-300">
                <span className="rounded-full bg-slate-900/60 px-3 py-1 border border-white/5">
                  Modules {completedModules}/{totalModules || 0}
                </span>
                <span className="rounded-full bg-slate-900/60 px-3 py-1 border border-white/5">
                  Topics {completedTopics}/{totalTopics || 0}
                </span>
                <span className="rounded-full bg-slate-900/60 px-3 py-1 border border-white/5">
                  Track {selectedTrackData?.name || 'Not selected'}
                </span>
              </div>
            </div>

            <div className="lg:hidden flex flex-wrap items-center gap-2 text-xs text-slate-300">
              <span className="rounded-full bg-cyan-500/20 px-3 py-1 border border-cyan-400/30 text-cyan-100">
                Progress {overallProgress}%
              </span>
              <span className="rounded-full bg-slate-900/60 px-3 py-1 border border-white/5">
                Modules {completedModules}/{totalModules || 0}
              </span>
              <span className="rounded-full bg-slate-900/60 px-3 py-1 border border-white/5">
                Topics {completedTopics}/{totalTopics || 0}
              </span>
            </div>

            <div className="flex items-center justify-between lg:justify-end gap-3">
              {onBack && (
                <button
                  onClick={() => step === 1 ? onBack() : setStep(step - 1)}
                  className="btn btn-secondary px-3 py-2"
                >
                  <FaArrowLeft className="mr-2" />
                  <span className="text-sm font-semibold">
                    {step === 1 ? 'Back' : 'Previous'}
                  </span>
                </button>
              )}
              <div className="flex items-center gap-3 rounded-2xl bg-slate-900/60 border border-white/10 px-3 py-2">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center text-white text-sm font-semibold">
                  {user ? profileInitials : <FaUserCircle />}
                </div>
                <div className="hidden sm:block">
                  <p className="text-sm font-semibold text-white">
                    {user?.full_name || user?.username || 'Guest Explorer'}
                  </p>
                  <p className="text-xs text-slate-400">
                    {user ? 'Progress synced' : 'Sign in to sync progress'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl sm:text-3xl font-semibold text-white">
                {step === 1 && 'Choose Your Path'}
                {step === 2 && (isCloudTrack ? 'Select Platform & Experience' : 'Select Experience Level')}
                {step === 3 && 'Your Learning Journey'}
              </h2>
              <p className="text-sm sm:text-base text-slate-300">
                {step === 1 && 'Select your career focus to get personalized learning recommendations.'}
                {step === 2 && (isCloudTrack
                  ? 'Pick your cloud provider and experience level for a platform-specific roadmap.'
                  : 'Tell us your experience level for tailored content and checkpoints.')}
                {step === 3 && 'Your roadmap, labs, and checkpoints are ready to run.'}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {step === 3 && journeyPlan && (
                <button
                  onClick={() => handleStartJourney(journeyPlan.path.path_id)}
                  className="btn btn-success hidden md:flex px-4 py-2 text-sm"
                >
                  <FaBookmark />
                  Save Journey
                </button>
              )}
              <button
                onClick={() => setStep(1)}
                className="btn btn-secondary hidden md:flex px-4 py-2 text-sm"
              >
                <FaHome />
                Start Over
              </button>
            </div>
          </div>
        </div>

        {/* Step 1: Career Track Selection */}
        {step === 1 && (
          <div className="grid lg:grid-cols-3 gap-8 mb-12">
            {careerTracks.map((track) => {
              const Icon = track.icon;
              const isSelected = selectedTrack === track.id;
              return (
                <button
                  key={track.id}
                  onClick={() => handleTrackSelect(track.id)}
                  className={`group relative p-8 rounded-3xl transition-all duration-500 text-left
                    ${isSelected
                      ? `select-card select-card-active bg-gradient-to-br ${track.bgGradient} border-2 border-transparent scale-105 shadow-xl shadow-cyan-500/20`
                      : 'select-card border-2 hover:scale-105'
                    }`}
                >
                  {/* Selection Indicator */}
                  {isSelected && (
                    <div className="absolute -top-3 -right-3 w-8 h-8 bg-gradient-to-r from-cyan-400 to-teal-500 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}

                  {/* Card Header */}
                  <div className="flex items-center mb-6">
                    <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${track.gradient} flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-300`}>
                      <Icon className="text-2xl text-white" />
                    </div>
                    <div>
                      <h3 className={`text-xl font-bold mb-1 transition-colors duration-300 ${
                        isSelected ? 'text-white' : 'text-slate-300 group-hover:text-white'
                      }`}>
                        {track.name}
                      </h3>
                      <p className="text-sm text-slate-400">{track.avgSalary}</p>
                    </div>
                  </div>

                  {/* Description */}
                  <p className={`text-sm mb-6 transition-colors duration-300 ${
                    isSelected ? 'text-slate-200' : 'text-slate-400 group-hover:text-slate-300'
                  }`}>
                    {track.description}
                  </p>

                  {/* Core Skills */}
                  <div className="mb-6">
                    <h4 className="text-sm font-semibold text-slate-300 mb-3">Core Skills</h4>
                    <div className="flex flex-wrap gap-2">
                      {track.skills.map((skill, index) => (
                        <span 
                          key={index}
                            className={`chip transition-colors duration-300 ${isSelected ? 'chip-active' : 'group-hover:text-white'}`}
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Career Roles */}
                  <div>
                    <h4 className="text-sm font-semibold text-slate-300 mb-2">Career Roles</h4>
                    <div className="text-xs text-slate-400">
                      {track.roles.join(' • ')}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* Step 2: Experience Level Selection */}
        {step === 2 && selectedTrackData && (
          <div className="max-w-4xl mx-auto">
            {/* Selected Track Summary */}
            <div className="mb-6 sm:mb-8 p-4 sm:p-6 rounded-3xl bg-gradient-to-r from-slate-800/50 to-slate-700/50 border border-white/10">
              <div className="flex items-center">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${selectedTrackData.gradient} flex items-center justify-center mr-4`}>
                  <selectedTrackData.icon className="text-white text-xl" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">{selectedTrackData.name}</h3>
                  <p className="text-slate-400">{selectedTrackData.description}</p>
                </div>
              </div>
            </div>

            {isCloudTrack && (
              <div className="mb-6 sm:mb-8 p-4 sm:p-6 rounded-3xl bg-gradient-to-r from-slate-800/50 to-slate-700/50 border border-white/10">
                <h3 className="text-base sm:text-lg font-semibold text-white mb-3">Cloud Provider</h3>
                <div className="grid md:grid-cols-3 gap-3 sm:gap-4">
                  {platformOptions.map((platform) => {
                    const isSelected = selectedPlatform === platform.id;
                    return (
                      <button
                        key={platform.id}
                        onClick={() => setSelectedPlatform(platform.id)}
                        className={`rounded-2xl border px-4 py-3 text-left transition-all duration-300 ${
                          isSelected
                            ? 'border-cyan-400 bg-cyan-500/20 text-white'
                            : 'border-white/10 bg-slate-900/40 text-slate-300 hover:border-cyan-500/40'
                        }`}
                      >
                        <div className="font-semibold">{platform.label}</div>
                        <div className="text-xs text-slate-400 mt-1">Platform-specific roadmap and docs</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Experience Level Cards */}
            <div className="grid md:grid-cols-3 gap-4 sm:gap-6">
              {experienceLevels.map((level) => {
                const Icon = level.icon;
                const isSelected = selectedLevel === level.id;
                return (
                  <button
                    key={level.id}
                    onClick={() => handleLevelSelect(level.id)}
                    className={`group relative p-4 sm:p-6 rounded-3xl transition-all duration-500 text-left
                      ${isSelected
                        ? `select-card select-card-active bg-gradient-to-br from-${level.color}-500/10 to-${level.color}-600/10 border-2 border-transparent scale-105 shadow-xl`
                        : 'select-card border-2 hover:scale-105'
                      }`}
                  >
                    {isSelected && (
                      <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-r from-cyan-400 to-teal-500 rounded-full flex items-center justify-center">
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}

                    <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br from-${level.color}-500 to-${level.color}-600 flex items-center justify-center mb-3 sm:mb-4 mx-auto group-hover:scale-110 transition-transform duration-300`}>
                      <Icon className="text-2xl text-white" />
                    </div>

                    <h3 className={`text-xl font-bold text-center mb-2 transition-colors duration-300 ${
                      isSelected ? 'text-white' : 'text-slate-300 group-hover:text-white'
                    }`}>
                      {level.name}
                    </h3>

                    <p className={`text-sm text-center mb-3 sm:mb-4 transition-colors duration-300 ${
                      isSelected ? 'text-slate-200' : 'text-slate-400 group-hover:text-slate-300'
                    }`}>
                      {level.description}
                    </p>

                    <div className="flex flex-wrap gap-2 justify-center">
                      {level.features.map((feature, index) => (
                        <span 
                          key={index}
                          className={`chip transition-colors duration-300 ${isSelected ? 'chip-active' : 'group-hover:text-white'}`}
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Step 3: Journey Results */}
        {step === 3 && journeyPlan && (
          <div className="max-w-6xl mx-auto">
            {/* Journey Overview */}
            <div className="mb-6 sm:mb-8 p-5 sm:p-8 rounded-3xl bg-gradient-to-r from-slate-800/50 to-slate-700/50 border border-white/10">
              <div className="text-center">
                <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 sm:mb-4">Your Learning Journey</h2>
                <p className="text-base sm:text-xl text-slate-300 mb-4 sm:mb-6">
                  Estimated Timeline: <span className="text-cyan-300 font-semibold">{journeyPlan.path.estimated_duration}</span>
                </p>

                <div className="flex flex-wrap gap-3 sm:gap-4 justify-center">
                  <div className="panel-soft px-4 py-2 text-slate-300 text-sm">
                    Path: <span className="text-white font-semibold">{journeyPlan.path.name}</span>
                  </div>
                  {journeyPlan.path.selected_platform && (
                    <div className="panel-soft px-4 py-2 text-slate-300 text-sm">
                      Platform: <span className="text-cyan-200 font-semibold uppercase">{journeyPlan.path.selected_platform}</span>
                    </div>
                  )}
                  <div className="panel-soft px-4 py-2 text-slate-300 text-sm">
                    Progress: <span className="text-teal-300 font-semibold">{Math.round(journeyPlan.overall_progress || 0)}%</span>
                  </div>
                  {!user && (
                    <div className="bg-cyan-500/10 border border-cyan-400/30 px-4 py-2 rounded-xl text-cyan-300 text-sm">
                      Sign in to save progress
                    </div>
                  )}
                </div>
                
                {/* Next Steps */}
                <div className="flex flex-wrap gap-3 sm:gap-4 justify-center mt-4 sm:mt-6">
                  {(journeyPlan.path.skills_earned || []).map((skill, index) => (
                    <div key={index} className="flex items-center panel-soft px-4 py-2">
                      <FaCheckCircle className="text-cyan-300 mr-2" />
                      <span className="text-slate-300 text-sm">{skill}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Journey Modules */}
            <div className="space-y-4 sm:space-y-6">
              {journeyPlan.modules.map((module, index) => {
                const moduleProgress = moduleProgressMap[module.module_id] || {};
                const progressValue = moduleProgress.progress_percentage || 0;
                const isActive = activeModule === module.module_id;
                return (
                  <div key={module.module_id} className="glass-dark rounded-3xl border border-white/10">
                    <button
                      onClick={() => setActiveModule(isActive ? null : module.module_id)}
                      className="w-full p-4 sm:p-6 text-left flex items-start justify-between"
                    >
                      <div>
                        <p className="text-sm text-cyan-300 font-semibold mb-2">Module {index + 1}</p>
                        <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">{module.name}</h3>
                        <p className="text-slate-400">{module.description}</p>
                      </div>
                      <div className="text-right">
                        <span className="rounded-full border border-cyan-400/30 bg-slate-950/60 px-3 py-1 text-xs text-cyan-100">
                          {module.estimated_time}
                        </span>
                            <p className="text-cyan-200 font-semibold mt-3">{Math.round(progressValue)}%</p>
                      </div>
                    </button>

                    <div className="px-4 sm:px-6 pb-5 sm:pb-6">
                      <div className="w-full h-2 bg-slate-800/60 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-cyan-500 to-teal-500"
                          style={{ width: `${progressValue}%` }}
                        ></div>
                      </div>
                    </div>

                    {isActive && (
                      <div className="px-4 sm:px-6 pb-6 sm:pb-8 space-y-4 sm:space-y-6">
                        {module.topics.map((topic) => {
                          const topicKey = `${module.module_id}:${topic.topic_id}`;
                          const topicProgress = topicProgressMap[topicKey];
                          const mcqStateEntry = mcqState[topicKey] || {};
                          const mcqCorrect = topicProgress?.mcq_correct;
                          const scenarioDone = topicProgress?.scenario_completed;
                          const isTopicActive = activeTopic === topicKey;
                          return (
                            <div key={topic.topic_id} className="border border-white/10 rounded-2xl p-4 sm:p-5 bg-slate-900/40">
                              <div className="flex items-start justify-between">
                                <div>
                                  <h4 className="text-base sm:text-lg font-semibold text-white mb-2">{topic.title}</h4>
                                  <p className="text-slate-300 text-sm">{topic.teaching}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                  {topicProgress?.is_completed && (
                                    <span className="text-cyan-200 text-sm flex items-center">
                                      <FaCheckCircle className="mr-2" /> Completed
                                    </span>
                                  )}
                                  <button
                                    onClick={() => setActiveTopic(isTopicActive ? null : topicKey)}
                                    className="text-xs text-cyan-300 hover:text-cyan-200"
                                  >
                                    {isTopicActive ? 'Hide' : 'Expand'}
                                  </button>
                                </div>
                              </div>

                              {isTopicActive && (
                                <div className="mt-3 sm:mt-4 space-y-4 sm:space-y-5">
                                  <div className="panel-soft p-3 sm:p-4">
                                    <h5 className="text-sm font-semibold text-slate-200 mb-2">In-App Lesson</h5>
                                    <div className="text-sm text-slate-300 whitespace-pre-line leading-relaxed">
                                      {topic.lesson_content || topic.teaching}
                                    </div>
                                  </div>

                                  <div className="grid md:grid-cols-2 gap-3 sm:gap-4">
                                    <div className="panel-soft p-3 sm:p-4">
                                      <h5 className="text-sm font-semibold text-slate-200 mb-2">Key Points</h5>
                                      <ul className="text-sm text-slate-400 space-y-1">
                                        {topic.key_points.map((point, pointIndex) => (
                                          <li key={pointIndex} className="flex items-start">
                                            <span className="text-cyan-300 mr-2">•</span>
                                            {point}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                    <div className="panel-soft p-3 sm:p-4">
                                      <h5 className="text-sm font-semibold text-slate-200 mb-2">Step-by-Step</h5>
                                      <ol className="text-sm text-slate-400 space-y-1">
                                        {topic.steps.map((stepItem, stepIndex) => (
                                          <li key={stepIndex} className="flex items-start">
                                            <span className="text-teal-300 mr-2">{stepIndex + 1}.</span>
                                            {stepItem}
                                          </li>
                                        ))}
                                      </ol>
                                    </div>
                                  </div>

                                  <div className="panel-soft p-3 sm:p-4">
                                    <div className="flex items-center text-slate-200 mb-2">
                                      <FaTasks className="mr-2 text-teal-300" />
                                      <h5 className="text-sm font-semibold">Hands-on Scenario</h5>
                                    </div>
                                    <p className="text-sm text-slate-300 mb-3">{topic.hands_on.scenario}</p>
                                    <ul className="text-sm text-slate-400 space-y-1 mb-3 sm:mb-4">
                                      {topic.hands_on.tasks.map((task, taskIndex) => (
                                        <li key={taskIndex} className="flex items-start">
                                          <span className="text-cyan-300 mr-2">•</span>
                                          {task}
                                        </li>
                                      ))}
                                    </ul>
                                    <button
                                      onClick={() => handleScenarioComplete(module.module_id, topic.topic_id)}
                                      className={`btn px-4 py-2 text-sm ${scenarioDone ? 'btn-secondary' : 'btn-success'}`}
                                    >
                                      {scenarioDone ? 'Scenario Completed' : 'Mark Scenario Complete'}
                                    </button>
                                  </div>

                                  <div className="panel-soft p-3 sm:p-4">
                                    <h5 className="text-sm font-semibold text-slate-200 mb-3">Quick MCQ Check</h5>
                                    <p className="text-sm text-slate-300 mb-3">{topic.mcq.question}</p>
                                    <div className="grid md:grid-cols-2 gap-2 sm:gap-3">
                                      {topic.mcq.options.map((option, optionIndex) => {
                                        const isSelected = mcqStateEntry.selectedOption === option;
                                        return (
                                          <button
                                            key={optionIndex}
                                            onClick={() => handleMcqSubmit(module.module_id, topic.topic_id, option)}
                                            className={`text-left px-3 py-2 rounded-2xl border text-sm transition-all duration-300 ${
                                              isSelected
                                                ? 'border-cyan-400 bg-cyan-500/20 text-white'
                                                : 'border-white/10 bg-slate-900/40 text-slate-300 hover:border-cyan-500/40'
                                            }`}
                                          >
                                            {option}
                                          </button>
                                        );
                                      })}
                                    </div>
                                    {mcqStateEntry.submitted && (
                                      <div className={`mt-3 text-sm ${mcqCorrect ? 'text-cyan-300' : 'text-teal-300'}`}>
                                        {mcqCorrect ? 'Correct! ' : 'Keep going. '}
                                        {topic.mcq.explanation}
                                      </div>
                                    )}
                                  </div>

                                  {topic.source_urls?.length > 0 && (
                                    <div className="panel-soft p-3 sm:p-4">
                                      <h5 className="text-sm font-semibold text-slate-200 mb-2">Source References</h5>
                                      <div className="text-xs text-slate-400 space-y-1">
                                        {topic.source_urls.map((url, urlIndex) => (
                                          <div key={urlIndex} className="break-all">{url}</div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}

                        {module.assessment && (
                          <div className="border border-white/10 rounded-2xl p-4 sm:p-6 bg-slate-900/60">
                            <div className="flex items-center mb-3 sm:mb-4">
                              <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-600 flex items-center justify-center mr-3">
                                <FaTasks className="text-white" />
                              </div>
                              <div>
                                <h4 className="text-base sm:text-lg font-semibold text-white">Module Checkpoint</h4>
                                <p className="text-sm text-slate-400">Apply what you learned and validate understanding.</p>
                              </div>
                              {moduleAssessmentProgressMap[module.module_id] && (
                                    <div className="ml-auto text-right">
                                  <p className="text-xs text-slate-400">Score</p>
                                  <p className="text-sm text-cyan-200 font-semibold">
                                    {moduleAssessmentProgressMap[module.module_id].mcq_correct}
                                    /{(module.assessment?.mcqs || []).length}
                                  </p>
                                </div>
                              )}
                              {moduleAssessmentProgressMap[module.module_id]?.is_completed && (
                                <span className="ml-4 text-sm text-cyan-200 flex items-center">
                                  <FaCheckCircle className="mr-2" /> Passed
                                </span>
                              )}
                            </div>

                            <div className="panel-soft p-3 sm:p-4 mb-3 sm:mb-4">
                              <h5 className="text-sm font-semibold text-slate-200 mb-2">Practice Lab</h5>
                              <p className="text-sm text-slate-300 mb-3">{module.assessment.scenario}</p>
                              <ul className="text-sm text-slate-400 space-y-1">
                                {module.assessment.tasks.map((task, taskIndex) => (
                                  <li key={taskIndex} className="flex items-start">
                                    <span className="text-cyan-300 mr-2">•</span>
                                    {task}
                                  </li>
                                ))}
                              </ul>
                              <button
                                onClick={() => handleModuleScenarioComplete(module.module_id)}
                                className={`btn mt-4 px-4 py-2 text-sm ${
                                  moduleAssessmentProgressMap[module.module_id]?.scenario_completed
                                    ? 'btn-secondary'
                                    : 'btn-success'
                                }`}
                              >
                                {moduleAssessmentProgressMap[module.module_id]?.scenario_completed
                                  ? 'Lab Completed'
                                  : 'Mark Lab Complete'}
                              </button>
                              <button
                                onClick={() => setPendingResetModule(module.module_id)}
                                className="btn btn-secondary mt-4 ml-3 px-4 py-2 text-sm"
                              >
                                Reset Checkpoint
                              </button>
                            </div>

                            <div className="space-y-4">
                              {(module.assessment.mcqs || []).map((mcq, mcqIndex) => {
                                const answerState = moduleAssessmentState[module.module_id]?.answers?.[mcqIndex] || {};
                                const isCorrect = answerState.submitted && answerState.selectedOption === mcq.correct_option;
                                const savedProgress = moduleAssessmentProgressMap[module.module_id];
                                const showSavedCorrect = savedProgress && !answerState.submitted && savedProgress.mcq_attempts > 0;
                                return (
                                  <div key={mcqIndex} className="panel-soft p-4">
                                    <p className="text-sm text-slate-200 mb-3">{mcq.question}</p>
                                    <div className="grid md:grid-cols-2 gap-3">
                                      {mcq.options.map((option, optionIndex) => {
                                        const isSelected = answerState.selectedOption === option;
                                        return (
                                          <button
                                            key={optionIndex}
                                            onClick={() => handleModuleMcqSubmit(module.module_id, mcqIndex, option)}
                                            className={`text-left px-3 py-2 rounded-2xl border text-sm transition-all duration-300 ${
                                              isSelected
                                                ? 'border-cyan-400 bg-cyan-500/20 text-white'
                                                : 'border-white/10 bg-slate-900/40 text-slate-300 hover:border-cyan-500/40'
                                            }`}
                                          >
                                            {option}
                                          </button>
                                        );
                                      })}
                                    </div>
                                    {answerState.submitted && (
                                      <div className={`mt-3 text-sm ${isCorrect ? 'text-cyan-300' : 'text-teal-300'}`}>
                                        {isCorrect ? 'Correct! ' : 'Review this concept. '}
                                        {mcq.explanation}
                                      </div>
                                    )}
                                    {showSavedCorrect && !answerState.submitted && (
                                      <div className="mt-3 text-sm text-slate-400">
                                        Progress saved for this checkpoint.
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="mt-10 grid md:grid-cols-2 gap-4">
              <button
                onClick={() => handleStartJourney(journeyPlan.path.path_id)}
                className="btn btn-success py-4 px-6"
              >
                <FaBookmark className="mr-2" />
                Save to My Journey
              </button>
              <button
                onClick={() => window.open(`#/learning-path/${journeyPlan.path.path_id}`, '_blank')}
                className="btn btn-secondary py-4 px-6"
              >
                <FaEye className="mr-2" />
                Explore Path
              </button>
            </div>

            {/* Journey Actions */}
            <div className="mt-8 text-center">
              <div className="flex flex-wrap justify-center gap-4">
                <button
                  onClick={() => setStep(1)}
                  className="btn btn-secondary py-3 px-6"
                >
                  <FaArrowLeft className="mr-2" />
                  Explore Other Paths
                </button>
                
                <button
                  onClick={onBack}
                  className="btn btn-info py-3 px-6"
                >
                  <FaHome className="mr-2" />
                  Back to Home
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Message Display */}
        {error && (
          <div className={`max-w-2xl mx-auto mb-8 p-4 rounded-2xl ${
            error.includes('✅') 
              ? 'bg-gradient-to-r from-cyan-500/10 to-teal-500/10 border border-cyan-500/30'
              : 'bg-gradient-to-r from-red-500/10 to-red-500/5 border border-red-500/30'
          }`}>
            <p className={`text-center font-medium ${
              error.includes('✅') ? 'text-cyan-300' : 'text-red-300'
            }`}>{error}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-center mt-12">
          {step === 1 && selectedTrack && (
            <button
              onClick={() => setStep(2)}
              className="btn btn-primary py-4 px-12 text-lg"
            >
              Continue
            </button>
          )}
          
          {step === 2 && selectedLevel && (
            <button
              onClick={handleGenerateJourney}
              disabled={isLoading}
              className={`btn btn-primary py-4 px-12 text-lg ${isLoading ? 'opacity-70' : ''}`}
            >
              {isLoading ? (
                <>
                  <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin mr-3"></div>
                  Generating Journey...
                </>
              ) : (
                <>
                  <FaRocket className="mr-3" />
                  Generate My Journey
                </>
              )}
            </button>
          )}
        </div>
      </div>

      <footer className="relative max-w-7xl mx-auto px-4 sm:px-6 pb-8 sm:pb-12">
        <div className="journey-footer rounded-3xl border border-white/10 px-4 py-6 sm:px-6 sm:py-8">
          <div className="lg:hidden flex flex-col gap-4">
            <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-slate-400">
              <span>Journey Mode</span>
              <span>{journeyPlan?.path?.name || 'Career Journey'}</span>
            </div>
            <p className="text-sm text-slate-300">
              {journeyPlan ? 'Complete one topic lab to keep momentum.' : 'Generate a journey to unlock checkpoints.'}
            </p>
            <div className="flex flex-wrap gap-2 text-xs text-slate-300">
              <span className="rounded-full bg-slate-900/60 px-3 py-1 border border-white/5">Guided Labs</span>
              <span className="rounded-full bg-slate-900/60 px-3 py-1 border border-white/5">Checkpoint MCQs</span>
              <span className="rounded-full bg-slate-900/60 px-3 py-1 border border-white/5">Progress Sync</span>
            </div>
          </div>
          <div className="hidden lg:flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-slate-800 via-slate-700 to-slate-600 flex items-center justify-center">
                <FaRoute className="text-cyan-300 text-lg" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">DevOps Learning Hub</h3>
                <p className="text-sm text-slate-400">Career Journey mode optimized for mobile webview.</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-3 text-xs text-slate-300">
              <span className="rounded-full bg-slate-900/60 px-3 py-1 border border-white/5">Guided Labs</span>
              <span className="rounded-full bg-slate-900/60 px-3 py-1 border border-white/5">Checkpoint MCQs</span>
              <span className="rounded-full bg-slate-900/60 px-3 py-1 border border-white/5">Progress Sync</span>
            </div>
            <div className="text-sm text-slate-400">
              <p className="font-semibold text-slate-200">Next best action</p>
              <p>{journeyPlan ? 'Complete one topic lab to keep momentum.' : 'Generate a journey to unlock checkpoints.'}</p>
            </div>
          </div>
        </div>
      </footer>

      {pendingResetModule && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center z-50 px-4">
          <div className="max-w-md w-full rounded-2xl bg-slate-900 border border-white/10 p-6 shadow-2xl">
            <h3 className="text-xl font-semibold text-white mb-2">Reset checkpoint?</h3>
            <p className="text-sm text-slate-400 mb-6">
              This clears the lab completion and MCQ answers for this module. You can retry anytime.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setPendingResetModule(null)}
                className="btn btn-secondary px-4 py-2 text-sm"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  const moduleId = pendingResetModule;
                  setPendingResetModule(null);
                  await handleModuleAssessmentReset(moduleId);
                }}
                className="btn btn-danger px-4 py-2 text-sm"
              >
                Reset Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CareerJourneyScreen;