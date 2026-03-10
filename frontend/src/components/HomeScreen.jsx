import React, { useEffect, useState } from 'react';
import {
  FaUserTie,
  FaUser,
  FaBook,
  FaAws,
  FaRocket,
  FaLightbulb,
  FaBolt,
  FaStar,
  FaChartLine,
  FaRoute,
  FaGraduationCap,
  FaMap,
  FaTrophy,
} from 'react-icons/fa';
import sliderYouth from '../assets/slider/1.jpg';
import sliderLifelong from '../assets/slider/3.jpg';
import sliderMentors from '../assets/slider/4.jpg';

const studyModes = [
  {
    id: 'interview',
    title: 'AI Interview Coach',
    description: 'Master DevOps interviews with personalized AI coaching',
    icon: FaUserTie,
    gradient: 'from-cyan-600 via-teal-600 to-cyan-500',
    bgGradient: 'from-cyan-500/10 via-teal-500/10 to-cyan-500/10',
    buttonGradient: 'from-cyan-600 to-teal-600 hover:from-cyan-700 hover:to-teal-700',
    iconBg: 'bg-gradient-to-br from-cyan-500 to-teal-600',
    features: [
      { icon: FaRocket, text: 'Real-time voice interviews' },
      { icon: FaChartLine, text: 'Detailed performance analytics' },
      { icon: FaLightbulb, text: 'Personalized feedback & tips' },
      { icon: FaBolt, text: 'Multiple difficulty levels' },
      { icon: FaStar, text: 'Cloud platform specialization' },
    ],
  },
  {
    id: 'journey',
    title: 'Career Journey Planner',
    description: 'Build your personalized DevOps learning roadmap',
    icon: FaRoute,
    gradient: 'from-teal-600 via-cyan-600 to-teal-500',
    bgGradient: 'from-teal-500/10 via-cyan-500/10 to-teal-500/10',
    buttonGradient: 'from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700',
    iconBg: 'bg-gradient-to-br from-teal-500 to-cyan-600',
    features: [
      { icon: FaMap, text: 'Personalized learning paths' },
      { icon: FaGraduationCap, text: 'Skill progression tracking' },
      { icon: FaTrophy, text: 'Achievement milestones' },
      { icon: FaChartLine, text: 'Career advancement guidance' },
      { icon: FaRocket, text: 'Industry-aligned curricula' },
    ],
  },
  {
    id: 'aws-study',
    title: 'Cloud Refresher Hub',
    description: 'Quick refresh on AWS services with key points and examples',
    icon: FaBook,
    gradient: 'from-cyan-600 via-teal-600 to-cyan-500',
    bgGradient: 'from-cyan-500/10 via-teal-500/10 to-cyan-500/10',
    buttonGradient: 'from-cyan-600 to-teal-600 hover:from-cyan-700 hover:to-teal-700',
    iconBg: 'bg-gradient-to-br from-cyan-500 to-teal-600',
    features: [
      { icon: FaAws, text: 'Fast key-point summaries' },
      { icon: FaLightbulb, text: 'When to use each service' },
      { icon: FaRocket, text: 'Common architecture patterns' },
      { icon: FaChartLine, text: 'Cost and scaling notes' },
      { icon: FaBolt, text: 'Quick AI refresher' },
    ],
  },
  {
    id: 'exam',
    title: 'AWS Certification Simulator',
    description: 'Practice exam-style questions and score reports',
    icon: FaTrophy,
    gradient: 'from-teal-600 via-cyan-600 to-teal-500',
    bgGradient: 'from-teal-500/10 via-cyan-500/10 to-teal-500/10',
    buttonGradient: 'from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700',
    iconBg: 'bg-gradient-to-br from-teal-500 to-cyan-600',
    features: [
      { icon: FaBook, text: 'Original MCQ practice sets' },
      { icon: FaLightbulb, text: 'Explanations after exam' },
      { icon: FaChartLine, text: 'Score breakdown and pass mark' },
      { icon: FaRocket, text: 'Fast review workflow' },
      { icon: FaBolt, text: 'Certification-ready pacing' },
    ],
  },
];

const FeatureCard = ({ icon: Icon, text }) => (
  <div className="flex items-center group">
    <div className="w-6 h-6 rounded-full bg-gradient-to-r from-cyan-400 to-teal-500 flex items-center justify-center mr-3 group-hover:scale-110 transition-transform duration-200">
      <Icon className="text-xs text-white" />
    </div>
    <span className="text-slate-300 group-hover:text-white transition-colors duration-200">{text}</span>
  </div>
);

const sliderItems = [
  {
    id: 'youths',
    headline: 'Youth learners, bold futures',
    copy: 'Hands-on practice, fast feedback, and confidence-building challenges.',
    gradient: 'from-cyan-500/20 via-teal-500/10 to-cyan-500/20',
    accent: 'text-cyan-200',
    tag: 'New learners',
    image: sliderYouth,
  },
  {
    id: 'lifelong',
    headline: 'Lifelong learners thrive here',
    copy: 'Refresh skills, explore new tools, and stay career-ready.',
    gradient: 'from-teal-500/20 via-cyan-500/10 to-teal-500/20',
    accent: 'text-teal-200',
    tag: 'Career refresh',
    image: sliderLifelong,
  },
  {
    id: 'mentors',
    headline: 'Teams learn across generations',
    copy: 'Shared practice spaces for mentorship and growth.',
    gradient: 'from-cyan-500/20 via-teal-500/10 to-cyan-500/20',
    accent: 'text-cyan-200',
    tag: 'Collaborative',
    image: sliderMentors,
  },
];

export default function HomeScreen({ onModeSelect, currentUser }) {
  const [activeSlide, setActiveSlide] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveSlide((prev) => (prev + 1) % sliderItems.length);
    }, 6500);
    return () => clearInterval(timer);
  }, []);


  const goToSlide = (index) => {
    setActiveSlide((index + sliderItems.length) % sliderItems.length);
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-cyan-500/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-32 right-16 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div
          className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-cyan-500/3 to-teal-500/3 rounded-full blur-3xl animate-spin"
          style={{ animationDuration: '60s' }}
        ></div>
      </div>

      <div className="relative px-4 sm:px-6 py-8 sm:py-12">
        {/* Spotlight Slider */}
        <div className="relative mb-12 sm:mb-16 max-w-[1920px] w-full mx-auto">
          <div className="overflow-hidden rounded-[2.5rem] border border-white/10 bg-slate-900/40">
            <div
              className="flex transition-transform duration-700 ease-out"
              style={{ transform: `translateX(-${activeSlide * 100}%)` }}
            >
              {sliderItems.map((slide) => {
                const backgroundImage = slide.image
                  ? `linear-gradient(120deg, rgba(8, 15, 28, 0.55), rgba(8, 15, 28, 0.1)), url(${slide.image})`
                  : 'linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.6))';

                return (
                  <div key={slide.id} className="relative min-w-full">
                    <div className="relative h-[280px] sm:h-[420px] lg:h-[600px] min-[1920px]:h-[750px] w-full">
                      <div
                        className="absolute inset-0"
                        style={{
                          backgroundImage,
                          backgroundSize: 'cover',
                          backgroundPosition: 'center',
                        }}
                      ></div>
                      <div className={`absolute inset-0 bg-gradient-to-br ${slide.gradient}`}></div>
                      <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-slate-950/20"></div>
                      <div className="absolute inset-0 flex items-end">
                        <div className="w-full px-6 sm:px-10 pb-8 sm:pb-10">
                          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-slate-950/70 px-3 py-1 text-xs uppercase tracking-[0.35em] text-cyan-100 shadow-lg shadow-cyan-500/10">
                            {slide.tag}
                          </div>
                          <h2 className={`mt-4 text-3xl sm:text-4xl font-bold ${slide.accent}`}>
                            {slide.headline}
                          </h2>
                          <p className="mt-3 text-base sm:text-lg text-slate-200 max-w-2xl">
                            {slide.copy}
                          </p>
                          <div className="mt-5 flex flex-wrap gap-3 text-xs text-slate-200">
                            <span className="rounded-full border border-cyan-400/20 bg-slate-950/60 px-3 py-1 text-cyan-100">
                              Youths learning
                            </span>
                            <span className="rounded-full border border-cyan-400/20 bg-slate-950/60 px-3 py-1 text-cyan-100">
                              Adults upskilling
                            </span>
                            <span className="rounded-full border border-cyan-400/20 bg-slate-950/60 px-3 py-1 text-cyan-100">
                              Mentors & peers
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex gap-2">
              {sliderItems.map((slide, index) => (
                <button
                  key={slide.id}
                  onClick={() => goToSlide(index)}
                  className={`h-2.5 w-8 rounded-full transition-all ${
                    index === activeSlide ? 'bg-white' : 'bg-white/20 hover:bg-white/40'
                  }`}
                  aria-label={`Go to slide ${index + 1}`}
                ></button>
              ))}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => goToSlide(activeSlide - 1)}
                className="rounded-full border border-cyan-400/30 bg-slate-950/60 px-4 py-2 text-xs font-semibold text-cyan-100 hover:text-white"
              >
                Prev
              </button>
              <button
                onClick={() => goToSlide(activeSlide + 1)}
                className="rounded-full border border-cyan-400/30 bg-slate-950/60 px-4 py-2 text-xs font-semibold text-cyan-100 hover:text-white"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto">

        {/* Hero Section */}
        <div className="text-center mb-12 sm:mb-16">
          <h1 className="text-4xl sm:text-7xl font-bold mb-5 sm:mb-6 bg-gradient-to-r from-white via-cyan-200 to-teal-200 bg-clip-text text-transparent leading-tight">
            DevOps Mastery
            <br />
            <span className="text-3xl sm:text-5xl bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
              Made Simple
            </span>
          </h1>
          
          <p className="text-base sm:text-xl text-slate-400 max-w-4xl mx-auto leading-relaxed">
            Transform your DevOps career with AI-powered learning. Practice interviews,
            master cloud technologies, and build your personalized learning journey.
          </p>
        </div>

        {/* Study Mode Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 sm:gap-8 mb-12 sm:mb-16">
          {studyModes.map((mode, index) => {
            const Icon = mode.icon;
            return (
              <div
                key={mode.id}
                className={`group relative bg-gradient-to-br ${mode.bgGradient} backdrop-blur-sm rounded-3xl p-5 sm:p-8 border border-white/10 hover:border-white/20 transition-all duration-500 hover:transform hover:scale-105 hover:shadow-2xl hover:shadow-cyan-500/10`}
                style={{
                  animationDelay: `${index * 200}ms`,
                  animation: 'fadeInUp 0.6s ease-out forwards',
                }}
              >
                {/* Gradient Overlay */}
                <div className={`absolute inset-0 bg-gradient-to-br ${mode.gradient} opacity-0 group-hover:opacity-5 rounded-3xl transition-opacity duration-500`}></div>
                
                {/* Content */}
                <div className="relative z-10">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-6 sm:mb-8">
                    <div>
                      <div className={`w-14 h-14 sm:w-16 sm:h-16 rounded-2xl ${mode.iconBg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg`}>
                        <Icon className="text-2xl text-white" />
                      </div>
                      <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-slate-200 group-hover:bg-clip-text transition-all duration-300">
                        {mode.title}
                      </h2>
                      <p className="text-slate-400 text-base sm:text-lg leading-relaxed">{mode.description}</p>
                    </div>
                  </div>

                  {/* Features Grid */}
                  <div className="space-y-3 sm:space-y-4 mb-6 sm:mb-8">
                    <h3 className="text-lg font-semibold text-slate-300 mb-4">What You'll Get:</h3>
                    <div className="grid gap-3">
                      {mode.features.map((feature, featureIndex) => (
                        <div 
                          key={featureIndex} 
                          className="opacity-0 animate-fadeInLeft"
                          style={{
                            animationDelay: `${(index * 200) + (featureIndex * 100)}ms`,
                            animationFillMode: 'forwards'
                          }}
                        >
                          <FeatureCard {...feature} />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Action Button */}
                  <button
                    onClick={() => onModeSelect(mode.id)}
                    className={`w-full py-3 sm:py-4 px-6 sm:px-8 bg-gradient-to-r ${mode.buttonGradient} rounded-2xl font-semibold text-base sm:text-lg transition-all duration-300 transform hover:scale-105 hover:shadow-xl flex items-center justify-center group-hover:shadow-lg active:scale-95`}
                  >
                    <Icon className="mr-3 group-hover:animate-pulse" />
                    <span>
                      {mode.id === 'interview' && currentUser ? 'Start Learning Journey' : 'Start Learning'}
                    </span>
                    <FaRocket className="ml-3 group-hover:translate-x-1 transition-transform duration-300" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom CTA Section */}
        <div className="text-center space-y-8">
          {/* Authentication CTA */}
          {!currentUser && (
            <div className="bg-gradient-to-r from-cyan-500/10 to-teal-500/10 backdrop-blur-sm rounded-3xl p-5 sm:p-8 border border-cyan-500/20">
              <div className="flex items-center justify-center mb-4">
                <FaUser className="text-2xl text-cyan-400 mr-3" />
                <FaRoute className="text-2xl text-teal-400 mr-3" />
                <FaChartLine className="text-2xl text-cyan-300" />
              </div>
              <h3 className="text-xl sm:text-2xl font-bold mb-3 bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
                Unlock Your Full Potential
              </h3>
              <p className="text-sm sm:text-base text-slate-400 max-w-3xl mx-auto leading-relaxed mb-5 sm:mb-6">
                Create an account to access personalized learning journeys, track your progress,
                and get career-specific roadmaps tailored to your goals.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <button
                  onClick={() => onModeSelect('auth')}
                  className="px-6 sm:px-8 py-3 sm:py-4 bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-700 hover:to-teal-700 rounded-2xl font-semibold text-base sm:text-lg transition-all duration-300 transform hover:scale-105 active:scale-95 flex items-center"
                >
                  <FaUser className="mr-3" />
                  Create Free Account
                </button>

                <div className="text-sm text-slate-400">
                  Already have an account?{' '}
                  <button
                    onClick={() => onModeSelect('auth')}
                    className="text-cyan-400 hover:text-cyan-300 font-semibold hover:underline"
                  >
                    Sign In
                  </button>
                </div>
              </div>

              {/* Benefits */}
              <div className="grid sm:grid-cols-3 gap-4 mt-8 text-sm">
                <div className="flex items-center justify-center text-slate-300">
                  <FaRoute className="text-cyan-400 mr-2" />
                  Learning Journeys
                </div>
                <div className="flex items-center justify-center text-slate-300">
                  <FaChartLine className="text-teal-400 mr-2" />
                  Progress Tracking
                </div>
                <div className="flex items-center justify-center text-slate-300">
                  <FaStar className="text-cyan-300 mr-2" />
                  Career Roadmaps
                </div>
              </div>
            </div>
          )}
        </div>
        </div>
      </div>
    </div>
  );
}