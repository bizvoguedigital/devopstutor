import React, { useEffect, useMemo, useState } from 'react';
import { FaArrowLeft, FaCheckCircle, FaTimesCircle } from 'react-icons/fa';
import { apiService } from '../services/api';

const certificateOptions = [
  {
    id: 'AWS Cloud Practitioner',
    label: 'AWS Cloud Practitioner',
    description: 'CLF-C02 style practice questions',
  },
  {
    id: 'AWS Solutions Architect Associate',
    label: 'AWS Solutions Architect Associate',
    description: 'SAA-C03 style architecture questions',
  },
  {
    id: 'AWS Developer Associate',
    label: 'AWS Developer Associate',
    description: 'DVA-C02 style development questions',
  },
  {
    id: 'AWS SysOps Administrator Associate',
    label: 'AWS SysOps Administrator Associate',
    description: 'SOA-C02 style operations questions',
  },
  {
    id: 'AWS Solutions Architect Professional',
    label: 'AWS Solutions Architect Professional',
    description: 'SAP-C02 style advanced architecture questions',
  },
  {
    id: 'AWS DevOps Engineer Professional',
    label: 'AWS DevOps Engineer Professional',
    description: 'DOP-C02 style DevOps lifecycle questions',
  },
  {
    id: 'AWS Security Specialty',
    label: 'AWS Security Specialty',
    description: 'Security domain practice questions',
  },
  {
    id: 'AWS Advanced Networking Specialty',
    label: 'AWS Advanced Networking Specialty',
    description: 'Networking domain practice questions',
  },
  {
    id: 'AWS Machine Learning Specialty',
    label: 'AWS Machine Learning Specialty',
    description: 'ML domain practice questions',
  },
  {
    id: 'AWS Data Analytics Specialty',
    label: 'AWS Data Analytics Specialty',
    description: 'Analytics domain practice questions',
  },
  {
    id: 'AWS Database Specialty',
    label: 'AWS Database Specialty',
    description: 'Database domain practice questions',
  },
  {
    id: 'AWS Data Engineer Associate',
    label: 'AWS Data Engineer Associate',
    description: 'DEA-C01 style data engineering questions',
  },
];

const questionCountOptions = [10, 25, 65];

export default function ExamSimulator({ onBack }) {
  const [certificate, setCertificate] = useState(certificateOptions[0].id);
  const [questionCount, setQuestionCount] = useState(65);
  const [isLoading, setIsLoading] = useState(false);
  const [examSession, setExamSession] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [flagged, setFlagged] = useState({});
  const [remainingSeconds, setRemainingSeconds] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [infoMessage, setInfoMessage] = useState('');

  const totalQuestions = examSession?.questions?.length || 0;
  const currentQuestion = examSession?.questions?.[currentIndex] || null;

  const answeredCount = useMemo(
    () => Object.keys(answers).length,
    [answers]
  );

  const flaggedCount = useMemo(
    () => Object.values(flagged).filter(Boolean).length,
    [flagged]
  );

  const unansweredCount = useMemo(
    () => Math.max(0, totalQuestions - answeredCount),
    [totalQuestions, answeredCount]
  );

  const formattedTime = useMemo(() => {
    if (remainingSeconds === null || remainingSeconds === undefined) return '--:--';
    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = remainingSeconds % 60;
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  }, [remainingSeconds]);

  useEffect(() => {
    if (!examSession || result || isSubmitting || remainingSeconds === null) return;
    if (remainingSeconds <= 0) {
      handleSubmitExam(true);
      return;
    }

    const timer = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev === null || prev <= 0) return 0;
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [examSession, result, remainingSeconds, isSubmitting]);

  const saveProgress = async (override = {}) => {
    if (!examSession || result) return;
    try {
      await apiService.saveExamProgress(examSession.exam_id, {
        answers,
        flagged,
        current_index: currentIndex,
        remaining_seconds: remainingSeconds,
        ...override,
      });
    } catch (err) {
      // Non-blocking autosave
    }
  };

  useEffect(() => {
    if (!examSession || result) return undefined;
    const interval = setInterval(() => {
      saveProgress();
    }, 20000);
    return () => clearInterval(interval);
  }, [examSession, result, answers, flagged, currentIndex, remainingSeconds]);

  const handleStartExam = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const session = await apiService.startExam(certificate, questionCount);
      setExamSession(session);
      setCurrentIndex(0);
      setAnswers({});
      setFlagged({});
      setRemainingSeconds((session.duration_minutes || 130) * 60);
      setInfoMessage('');
    } catch (err) {
      setError('Failed to start exam. Please try again.');
      console.error('Error starting exam:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectOption = (questionId, option) => {
    const next = {
      ...answers,
      [questionId]: option,
    };
    setAnswers((prev) => ({
      ...prev,
      [questionId]: option,
    }));
    saveProgress({ answers: next });
  };

  const toggleFlag = (questionId) => {
    const next = {
      ...flagged,
      [questionId]: !flagged[questionId],
    };
    setFlagged((prev) => ({
      ...prev,
      [questionId]: !prev[questionId],
    }));
    saveProgress({ flagged: next });
  };

  const handleResumeExam = async () => {
    setIsLoading(true);
    setError(null);
    setInfoMessage('');
    try {
      const session = await apiService.getActiveExam();
      if (!session?.exam_id) {
        setInfoMessage('No active exam session found to resume.');
        return;
      }
      setExamSession(session);
      setAnswers(session.answers || {});
      setFlagged(session.flagged || {});
      setCurrentIndex(session.current_index || 0);
      setRemainingSeconds(
        session.remaining_seconds ?? ((session.duration_minutes || 130) * 60)
      );
      setInfoMessage('Resumed your active exam session.');
    } catch (err) {
      const status = err?.response?.status;
      if (status === 404) {
        setInfoMessage('No active exam session found to resume.');
      } else if (status === 401) {
        setInfoMessage('Sign in to use exam resume.');
      } else {
        setError('Failed to resume exam. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handlePauseExam = async () => {
    await saveProgress();
    setExamSession(null);
    setCurrentIndex(0);
    setInfoMessage('Exam paused. Use Resume Active Exam to continue.');
  };

  const handleSubmitExam = async (autoSubmit = false) => {
    if (!examSession) return;
    if (!autoSubmit && unansweredCount > 0) {
      const proceed = window.confirm(`You still have ${unansweredCount} unanswered question(s). Submit anyway?`);
      if (!proceed) return;
    }

    setIsLoading(true);
    setIsSubmitting(true);
    setError(null);

    try {
      const payload = Object.entries(answers).map(([questionId, selectedOption]) => ({
        question_id: String(questionId),
        selected_option: selectedOption,
      }));
      const examResult = await apiService.submitExam(examSession.exam_id, payload);
      setResult(examResult);
      setInfoMessage('');
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string' && detail.trim()) {
        setError(detail);
      } else {
        setError('Failed to submit exam. Please try again.');
      }
      console.error('Error submitting exam:', err);
    } finally {
      setIsLoading(false);
      setIsSubmitting(false);
    }
  };

  const handleRestart = () => {
    setExamSession(null);
    setResult(null);
    setAnswers({});
    setFlagged({});
    setCurrentIndex(0);
    setRemainingSeconds(null);
  };

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-8">
      <div className="flex items-center mb-6 sm:mb-8">
        <button
          onClick={onBack}
          className="btn btn-secondary px-3 py-2 mr-4"
        >
          <FaArrowLeft className="mr-2" />
          Back to Home
        </button>
        <h1 className="text-2xl sm:text-3xl font-bold text-cyan-300">AWS Certification Exam Simulator</h1>
      </div>

      {!examSession && !result && (
        <div className="glass-dark rounded-3xl p-5 sm:p-8 border border-white/10">
          <h2 className="text-xl sm:text-2xl font-semibold mb-4">Exam Setup</h2>
          <p className="text-sm sm:text-base text-gray-300 mb-5 sm:mb-6">
            Practice with original multiple-choice questions and receive a full score report at the end.
          </p>

          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 text-slate-200">Certification</h3>
            <div className="grid md:grid-cols-2 gap-3 sm:gap-4">
              {certificateOptions.map((option) => (
                <button
                  key={option.id}
                  onClick={() => setCertificate(option.id)}
                  className={`text-left p-3 sm:p-4 rounded-2xl border transition-colors ${
                    certificate === option.id
                      ? 'select-card select-card-active bg-cyan-600/20 border-cyan-500 text-white'
                      : 'select-card'
                  }`}
                >
                  <div className="font-semibold">{option.label}</div>
                  <div className="text-sm text-slate-400">{option.description}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 text-slate-200">Question Count</h3>
            <div className="flex flex-wrap gap-2 sm:gap-3">
              {questionCountOptions.map((count) => (
                <button
                  key={count}
                  onClick={() => setQuestionCount(count)}
                  className={`px-3 sm:px-4 py-2 rounded-2xl border transition-colors ${
                    questionCount === count
                      ? 'select-card select-card-active bg-cyan-600/20 border-cyan-500 text-white'
                      : 'select-card'
                  }`}
                >
                  {count} Questions
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-900/50 border border-red-500 rounded-2xl text-red-200">
              {error}
            </div>
          )}

          {infoMessage && (
            <div className="mb-4 p-4 bg-cyan-900/40 border border-cyan-500/40 rounded-2xl text-cyan-200">
              {infoMessage}
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleStartExam}
              disabled={isLoading}
              className="btn btn-info px-5 sm:px-6 py-3"
            >
              {isLoading ? 'Generating Questions...' : 'Start Exam'}
            </button>
            <button
              onClick={handleResumeExam}
              disabled={isLoading}
              className="btn btn-secondary px-5 sm:px-6 py-3"
            >
              {isLoading ? 'Loading...' : 'Resume Active Exam'}
            </button>
          </div>
        </div>
      )}

      {examSession && !result && (
        <div className="space-y-6">
          <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">{examSession.certificate}</h2>
                <p className="text-slate-400 text-sm">Question {currentIndex + 1} of {totalQuestions}</p>
              </div>
              <div className="text-right text-sm space-y-1">
                <div className={`font-semibold ${remainingSeconds !== null && remainingSeconds < 300 ? 'text-red-300' : 'text-cyan-300'}`}>
                  Time left: {formattedTime}
                </div>
                <div className="text-slate-300">Answered {answeredCount} / {totalQuestions}</div>
                <div className="text-amber-300">Flagged: {flaggedCount}</div>
              </div>
            </div>
          </div>

          <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
            <h3 className="text-lg font-semibold mb-4">Question Navigator</h3>
            <div className="flex flex-wrap gap-2">
              {examSession.questions.map((q, idx) => {
                const isCurrent = idx === currentIndex;
                const hasAnswer = Boolean(answers[q.id]);
                const isFlagged = Boolean(flagged[q.id]);
                return (
                  <button
                    key={q.id}
                    onClick={() => {
                      setCurrentIndex(idx);
                      saveProgress({ current_index: idx });
                    }}
                    className={`w-10 h-10 rounded-lg border text-sm font-semibold transition-colors ${
                      isCurrent
                        ? 'border-cyan-400 bg-cyan-600/20 text-cyan-200'
                        : hasAnswer
                          ? 'border-emerald-500/40 bg-emerald-600/20 text-emerald-200'
                          : isFlagged
                            ? 'border-amber-500/40 bg-amber-600/20 text-amber-200'
                            : 'border-white/15 text-slate-300 hover:bg-white/5'
                    }`}
                    title={isFlagged ? 'Flagged for review' : hasAnswer ? 'Answered' : 'Unanswered'}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>
          </div>

          {currentQuestion && (
            <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
              <div className="flex items-start justify-between gap-3 mb-4">
                <h3 className="text-lg font-semibold">{currentQuestion.prompt}</h3>
                <button
                  onClick={() => toggleFlag(currentQuestion.id)}
                  className={`px-3 py-1.5 rounded-lg border text-xs ${
                    flagged[currentQuestion.id]
                      ? 'border-amber-500/40 bg-amber-600/20 text-amber-200'
                      : 'border-white/15 text-slate-300 hover:bg-white/5'
                  }`}
                >
                  {flagged[currentQuestion.id] ? 'Flagged' : 'Flag for review'}
                </button>
              </div>
              <div className="space-y-3">
                {currentQuestion.options.map((option, index) => {
                  const selected = answers[currentQuestion.id] === option;
                  return (
                    <button
                      key={`${currentQuestion.id}-${index}`}
                      onClick={() => handleSelectOption(currentQuestion.id, option)}
                      className={`w-full text-left px-4 py-3 rounded-2xl border transition-colors ${
                        selected
                          ? 'select-card select-card-active bg-cyan-600/20 border-cyan-500 text-white'
                          : 'select-card text-slate-200'
                      }`}
                    >
                      {option}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-900/50 border border-red-500 rounded-2xl text-red-200">
              {error}
            </div>
          )}

          <div className="flex items-center justify-between">
            <button
              onClick={() => {
                const next = Math.max(currentIndex - 1, 0);
                setCurrentIndex(next);
                saveProgress({ current_index: next });
              }}
              disabled={currentIndex === 0}
              className="btn btn-secondary px-4 py-2"
            >
              Previous
            </button>
            <div className="flex items-center gap-3">
              <button
                onClick={handlePauseExam}
                className="btn btn-secondary px-4 py-2"
              >
                Pause & Exit
              </button>
              {currentIndex < totalQuestions - 1 ? (
                <button
                  onClick={() => {
                    const next = Math.min(currentIndex + 1, totalQuestions - 1);
                    setCurrentIndex(next);
                    saveProgress({ current_index: next });
                  }}
                  className="btn btn-info px-4 py-2"
                >
                  Next
                </button>
              ) : (
                <button
                  onClick={() => handleSubmitExam(false)}
                  disabled={isLoading}
                  className="btn btn-success px-4 py-2"
                >
                  {isLoading ? 'Submitting...' : 'Finish Exam'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
            <h2 className="text-2xl font-semibold mb-2">Exam Results</h2>
            <p className="text-slate-400">{result.certificate}</p>
            <div className="mt-4 flex flex-wrap gap-6">
              <div>
                <p className="text-sm text-slate-400">Score</p>
                <p className="text-3xl font-bold text-cyan-300">{result.score_percent}%</p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Correct</p>
                <p className="text-3xl font-bold text-teal-300">{result.correct_count}/{result.total_questions}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Unanswered</p>
                <p className="text-3xl font-bold text-amber-300">{result.unanswered_count}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Result</p>
                <p className={`text-2xl font-semibold ${result.passed ? 'text-cyan-400' : 'text-red-400'}`}>
                  {result.passed ? 'Pass' : 'Needs Review'}
                </p>
              </div>
            </div>
          </div>

          {result.category_breakdown?.length > 0 && (
            <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
              <h3 className="text-xl font-semibold mb-4">Domain Performance</h3>
              <div className="space-y-3">
                {result.category_breakdown.map((item) => (
                  <div key={item.category} className="rounded-2xl border border-white/10 p-3 panel-soft">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-200 capitalize">{item.category.replace(/_/g, ' ')}</span>
                      <span className="text-sm text-slate-300">{item.correct}/{item.total} • {item.accuracy}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.recommendations?.length > 0 && (
            <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
              <h3 className="text-xl font-semibold mb-4">Next Study Actions</h3>
              <ul className="list-disc pl-5 space-y-2 text-slate-300">
                {result.recommendations.map((tip, idx) => (
                  <li key={idx}>{tip}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
            <h3 className="text-xl font-semibold mb-4">Answer Review</h3>
            <div className="space-y-4">
              {result.review.map((item) => (
                <div key={item.question_id} className="border border-white/10 rounded-2xl p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm text-slate-400 mb-2">Question {item.question_number}</p>
                      {item.category && (
                        <p className="text-xs text-cyan-300 mb-2 capitalize">{String(item.category).replace(/_/g, ' ')}</p>
                      )}
                      <p className="text-slate-200 mb-3">{item.prompt}</p>
                    </div>
                    <div className="text-xl">
                      {item.is_correct ? (
                        <FaCheckCircle className="text-cyan-400" />
                      ) : (
                        <FaTimesCircle className="text-red-400" />
                      )}
                    </div>
                  </div>
                  <div className="grid md:grid-cols-2 gap-4 text-sm">
                    <div className="panel-soft p-3">
                      <p className="text-slate-400 mb-1">Your Answer</p>
                      <p className="text-slate-200">{item.selected_option || 'No answer'}</p>
                    </div>
                    <div className="panel-soft p-3">
                      <p className="text-slate-400 mb-1">Correct Answer</p>
                      <p className="text-slate-200">{item.correct_option}</p>
                    </div>
                  </div>
                  <p className="text-slate-300 mt-3">{item.explanation}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            <button
              onClick={handleRestart}
              className="btn btn-info px-6 py-3"
            >
              Start New Exam
            </button>
            <button
              onClick={onBack}
              className="btn btn-secondary px-6 py-3"
            >
              Back to Home
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
