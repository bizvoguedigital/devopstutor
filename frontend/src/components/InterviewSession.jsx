import React, { useState, useEffect, useRef } from 'react';
import { FaMicrophone, FaStop, FaPaperPlane, FaVolumeUp, FaVolumeMute } from 'react-icons/fa';
import { Room } from 'livekit-client';
import { apiService } from '../services/api';
import { useInterviewStore } from '../store/interviewStore';

export default function InterviewSession({ onComplete }) {
  const {
    session,
    currentQuestion,
    currentQuestionId,
    currentAnswer,
    lastEvaluation,
    isRecording,
    isProcessing,
    questionHistory,
    setCurrentQuestion,
    setCurrentAnswer,
    setLastEvaluation,
    setIsRecording,
    setIsProcessing,
    addToHistory,
  } = useInterviewStore();

  const [error, setError] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const audioRef = useRef([]);
  const hasLoadedFirstQuestion = useRef(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [ttsMode, setTtsMode] = useState('api');
  const [ttsBackendAvailable, setTtsBackendAvailable] = useState(false);
  const [ttsAvailabilityReason, setTtsAvailabilityReason] = useState('');
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('');
  const [apiVoices, setApiVoices] = useState([]);
  const [selectedApiVoice, setSelectedApiVoice] = useState('');
  const [speechRate, setSpeechRate] = useState(1);
  const [speechPitch, setSpeechPitch] = useState(1);
  const [pauseMs, setPauseMs] = useState(200);
  const [apiStability, setApiStability] = useState(0.5);
  const [apiSimilarity, setApiSimilarity] = useState(0.75);
  const [isTtsLoading, setIsTtsLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const speakQueueRef = useRef([]);
  const speakTimerRef = useRef(null);
  const ttsAudioRef = useRef(null);
  const ttsObjectUrlRef = useRef(null);
  const userVideoRef = useRef(null);
  const webcamStreamRef = useRef(null);
  const [ttsNotice, setTtsNotice] = useState('');
  const [hasWebcam, setHasWebcam] = useState(true);
  const [hasMicrophone, setHasMicrophone] = useState(true);
  const [userCamEnabled, setUserCamEnabled] = useState(true);
  const [aiCamEnabled, setAiCamEnabled] = useState(true);
  const [webcamError, setWebcamError] = useState('');
  const [remainingSeconds, setRemainingSeconds] = useState(null);
  const [totalDurationSeconds, setTotalDurationSeconds] = useState(null);
  const [isEndingInterview, setIsEndingInterview] = useState(false);
  const hasAutoCompletedRef = useRef(false);
  const [runStartCountdown, setRunStartCountdown] = useState(null);
  const hasStartedRunVoiceRef = useRef(false);
  const [voiceRuntimeStatus, setVoiceRuntimeStatus] = useState(null);
  const [isVoiceRuntimeLoading, setIsVoiceRuntimeLoading] = useState(false);
  const [isLivekitConnecting, setIsLivekitConnecting] = useState(false);
  const [livekitConnected, setLivekitConnected] = useState(false);
  const [livekitError, setLivekitError] = useState('');
  const livekitRoomRef = useRef(null);
  const isInterviewRunMode = Boolean(session?.strict_mode) && session?.interview_experience_mode === 'interview_run';
  const isCountdownActive = Number.isFinite(runStartCountdown) && runStartCountdown >= 0;

  useEffect(() => {
    // Prevent double-loading in React StrictMode
    if (hasLoadedFirstQuestion.current) return;
    hasLoadedFirstQuestion.current = true;

    // Clear any previous question state and load first question
    setCurrentQuestion(null, null);
    setCurrentAnswer('');
    setLastEvaluation(null);
    loadNextQuestion();
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;

    const updateVoices = () => {
      const available = window.speechSynthesis.getVoices();
      setVoices(available);
      if (!selectedVoice && available.length) {
        setSelectedVoice(available[0].voiceURI);
      }
    };

    updateVoices();
    window.speechSynthesis.addEventListener('voiceschanged', updateVoices);

    return () => {
      window.speechSynthesis.removeEventListener('voiceschanged', updateVoices);
    };
  }, [selectedVoice]);

  useEffect(() => {
    const fetchTts = async () => {
      try {
        const status = await apiService.getTtsStatus();
        const available = Boolean(status?.available);
        const availabilityReason = status?.availability_reason || '';
        setTtsBackendAvailable(available);
        setTtsAvailabilityReason(availabilityReason);
        if (!available) {
          if (availabilityReason) {
            setTtsNotice(`ElevenLabs unavailable (${availabilityReason}). Using browser voice.`);
          }
          setTtsMode('browser');
          return;
        }

        try {
          const voicesData = await apiService.getTtsVoices();
          setApiVoices(Array.isArray(voicesData) ? voicesData : []);
          const defaultVoiceId = status?.default_voice_id || '';
          const hasDefaultVoice = defaultVoiceId && voicesData?.some((voice) => voice.voice_id === defaultVoiceId);

          if (hasDefaultVoice) {
            setSelectedApiVoice(defaultVoiceId);
          } else if (!selectedApiVoice && voicesData?.length) {
            setSelectedApiVoice(voicesData[0].voice_id);
          }
          setTtsMode('api');
        } catch (err) {
          setApiVoices([]);
          setTtsMode('api');
        }
      } catch (err) {
        setTtsBackendAvailable(false);
        setTtsAvailabilityReason('status_unavailable');
        setTtsNotice('ElevenLabs unavailable (status_unavailable). Using browser voice.');
        setApiVoices([]);
        setTtsMode('browser');
      }
    };

    fetchTts();
  }, []);

  useEffect(() => {
    const fetchVoiceRuntimeStatus = async () => {
      setIsVoiceRuntimeLoading(true);
      try {
        const status = await apiService.getVoiceRuntimeStatus();
        setVoiceRuntimeStatus(status || null);
      } catch (err) {
        setVoiceRuntimeStatus(null);
      } finally {
        setIsVoiceRuntimeLoading(false);
      }
    };

    fetchVoiceRuntimeStatus();
  }, []);

  useEffect(() => {
    const detectMediaDevices = async () => {
      try {
        if (!navigator?.mediaDevices?.enumerateDevices) return;
        const devices = await navigator.mediaDevices.enumerateDevices();
        const cameraFound = devices.some((device) => device.kind === 'videoinput');
        const micFound = devices.some((device) => device.kind === 'audioinput');
        setHasWebcam(cameraFound);
        setHasMicrophone(micFound);
      } catch (err) {
        console.warn('Unable to detect media devices:', err);
      }
    };

    detectMediaDevices();
  }, []);

  const stopUserWebcam = () => {
    if (webcamStreamRef.current) {
      webcamStreamRef.current.getTracks().forEach((track) => track.stop());
      webcamStreamRef.current = null;
    }
    if (userVideoRef.current) {
      userVideoRef.current.srcObject = null;
    }
  };

  useEffect(() => {
    const startUserWebcam = async () => {
      if (!userCamEnabled) {
        stopUserWebcam();
        setWebcamError('');
        return;
      }

      if (!hasWebcam) {
        setWebcamError('No webcam detected on this device.');
        setUserCamEnabled(false);
        return;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        webcamStreamRef.current = stream;
        if (userVideoRef.current) {
          userVideoRef.current.srcObject = stream;
        }
        setWebcamError('');
      } catch (err) {
        const permissionDenied = err?.name === 'NotAllowedError' || err?.name === 'SecurityError';
        const unavailable = err?.name === 'NotFoundError' || err?.name === 'OverconstrainedError';
        if (permissionDenied) {
          setWebcamError('Webcam access denied. Enable camera permissions to use webcam.');
        } else if (unavailable) {
          setWebcamError('No webcam available.');
        } else {
          setWebcamError('Unable to start webcam.');
        }
        setUserCamEnabled(false);
      }
    };

    startUserWebcam();

    return () => {
      stopUserWebcam();
    };
  }, [userCamEnabled, hasWebcam]);

  useEffect(() => {
    if (!ttsEnabled || !currentQuestion) return;
    speakQuestion(currentQuestion);
  }, [ttsEnabled, currentQuestion, ttsMode]);

  useEffect(() => () => stopSpeaking(), []);

  useEffect(() => {
    return () => {
      stopUserWebcam();
    };
  }, []);

  useEffect(() => {
    return () => {
      if (livekitRoomRef.current) {
        livekitRoomRef.current.disconnect();
        livekitRoomRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (ttsMode === 'api' && !ttsBackendAvailable) {
      setTtsMode('browser');
    }
  }, [ttsMode, ttsBackendAvailable]);

  const loadNextQuestion = async () => {
    setIsProcessing(true);
    setError(null);
    setCurrentQuestion(null, null); // Clear current question while loading

    try {
      if (session?.mode === 'interviewer_v2') {
        const status = await apiService.getInterviewerV2SessionStatus(session.session_id);
        if (status?.status === 'completed') {
          setCurrentQuestion(null, null);
          return;
        }
        setCurrentQuestion(status?.current_question || null, status?.current_turn || null);
      } else {
        const questionData = await apiService.generateQuestion(session.session_id);
        setCurrentQuestion(questionData.question, questionData.question_number);
      }
    } catch (err) {
      setError('Failed to load question. Please try again.');
      console.error('Error loading question:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const connectLivekitRoom = async () => {
    if (!session?.session_id || isLivekitConnecting || livekitConnected) return;

    setLivekitError('');
    setIsLivekitConnecting(true);

    try {
      const tokenResponse = await apiService.createLivekitVoiceToken(session.session_id);
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      room.on('disconnected', () => {
        setLivekitConnected(false);
      });

      await room.connect(tokenResponse.livekit_url, tokenResponse.token);
      livekitRoomRef.current = room;
      setLivekitConnected(true);
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Failed to connect LiveKit room.';
      setLivekitError(String(detail));
      setLivekitConnected(false);
      if (livekitRoomRef.current) {
        livekitRoomRef.current.disconnect();
        livekitRoomRef.current = null;
      }
    } finally {
      setIsLivekitConnecting(false);
    }
  };

  const disconnectLivekitRoom = () => {
    if (!livekitRoomRef.current) {
      setLivekitConnected(false);
      return;
    }
    livekitRoomRef.current.disconnect();
    livekitRoomRef.current = null;
    setLivekitConnected(false);
  };

  const formatDuration = (seconds) => {
    const safe = Math.max(0, Number(seconds || 0));
    const mins = Math.floor(safe / 60).toString().padStart(2, '0');
    const secs = Math.floor(safe % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  const getTimerTone = (seconds) => {
    if (!Number.isFinite(seconds)) return 'text-cyan-300';
    if (seconds <= 60) return 'text-red-300';
    if (seconds <= 300) return 'text-amber-300';
    return 'text-cyan-300';
  };

  const startRecording = async () => {
    try {
      if (!hasMicrophone) {
        setError('No microphone detected. Please type your answer instead.');
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (event) => {
        audioRef.current.push(event.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioRef.current, { type: 'audio/wav' });
        audioRef.current = [];

        // Transcribe audio
        setIsProcessing(true);
        try {
          const transcription = await apiService.transcribeAudio(audioBlob);
          setCurrentAnswer(transcription.text);
        } catch (err) {
          setError('Failed to transcribe audio. Please try typing instead.');
          console.error('Transcription error:', err);
        } finally {
          setIsProcessing(false);
        }

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (err) {
      const permissionDenied = err?.name === 'NotAllowedError' || err?.name === 'SecurityError';
      const deviceMissing = err?.name === 'NotFoundError' || err?.name === 'OverconstrainedError';
      if (permissionDenied) {
        setError('Microphone access denied. Please allow mic access or type your answer.');
      } else if (deviceMissing) {
        setError('No microphone available. Please type your answer instead.');
      } else {
        setError('Failed to access microphone. Please check permissions.');
      }
      console.error('Microphone error:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const stopSpeaking = () => {
    if (speakTimerRef.current) {
      clearTimeout(speakTimerRef.current);
      speakTimerRef.current = null;
    }
    speakQueueRef.current = [];
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    if (ttsAudioRef.current) {
      ttsAudioRef.current.pause();
      ttsAudioRef.current.src = '';
      ttsAudioRef.current = null;
    }
    if (ttsObjectUrlRef.current) {
      URL.revokeObjectURL(ttsObjectUrlRef.current);
      ttsObjectUrlRef.current = null;
    }
    setIsSpeaking(false);
    setIsTtsLoading(false);
  };

  const speakBrowserText = (text) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;
    if (!text) return;

    stopSpeaking();

    // Split on sentence endings to allow adjustable pauses.
    const segments = text.split(/(?<=[.!?])\s+/).filter(Boolean);
    speakQueueRef.current = segments;
    setIsSpeaking(true);

    const speakNext = () => {
      const next = speakQueueRef.current.shift();
      if (!next) {
        setIsSpeaking(false);
        return;
      }

      const utterance = new SpeechSynthesisUtterance(next);
      const voice = voices.find((item) => item.voiceURI === selectedVoice);
      if (voice) {
        utterance.voice = voice;
      }
      utterance.rate = speechRate;
      utterance.pitch = speechPitch;

      utterance.onend = () => {
        speakTimerRef.current = setTimeout(speakNext, pauseMs);
      };
      utterance.onerror = () => {
        setIsSpeaking(false);
      };

      window.speechSynthesis.speak(utterance);
    };

    speakNext();
  };

  const speakApiText = async (text) => {
    if (!text) return;

    setIsTtsLoading(true);
    setIsSpeaking(true);

    try {
      const audioBlob = await apiService.synthesizeSpeech({
        text,
        voice_id: selectedApiVoice || undefined,
        stability: apiStability,
        similarity_boost: apiSimilarity,
      });

      if (ttsObjectUrlRef.current) {
        URL.revokeObjectURL(ttsObjectUrlRef.current);
      }

      const url = URL.createObjectURL(audioBlob);
      ttsObjectUrlRef.current = url;

      const audio = new Audio(url);
      ttsAudioRef.current = audio;

      audio.onended = () => {
        setIsSpeaking(false);
        setIsTtsLoading(false);
      };
      audio.onerror = () => {
        setError('Failed to play TTS audio.');
        setIsSpeaking(false);
        setIsTtsLoading(false);
      };

      await audio.play();
    } catch (err) {
      console.error('TTS generation error:', err?.response?.data || err?.message || err);
      setTtsNotice('ElevenLabs unavailable. Using browser voice.');
      setTtsMode('browser');
      setIsSpeaking(false);
      setIsTtsLoading(false);
      speakBrowserText(text);
    }
  };

  const speakQuestion = (text) => {
    stopSpeaking();

    if (ttsMode === 'api' && ttsBackendAvailable) {
      speakApiText(text);
      return;
    }

    speakBrowserText(text);
  };

  const submitAnswer = async () => {
    if (remainingSeconds !== null && remainingSeconds <= 0) {
      setError('Interview time is over. Finalizing your summary...');
      return;
    }

    if (!currentAnswer.trim()) {
      setError('Please provide an answer before submitting.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      let evaluation;

      if (session?.mode === 'interviewer_v2') {
        const turn = await apiService.submitInterviewerV2Turn(session.session_id, currentAnswer);
        evaluation = {
          score: Number(turn?.score ?? 0),
          feedback: turn?.feedback || turn?.assistant_message || '',
          model_answer: '',
          learning_opportunities: '',
          best_practices: '',
          real_world_insights: '',
          follow_up_question: turn?.next_question || null,
          completed: Boolean(turn?.completed),
          refusal: Boolean(turn?.refusal),
        };
      } else {
        evaluation = await apiService.submitAnswer(
          session.session_id,
          currentQuestionId,
          currentAnswer
        );
      }

      addToHistory(currentQuestion, currentAnswer, evaluation);

      if (session?.mode === 'interviewer_v2' && evaluation?.completed) {
        await handleEndInterview();
        return;
      }

      setCurrentAnswer('');
      await loadNextQuestion();
    } catch (err) {
      setError('Failed to submit answer. Please try again.');
      console.error('Error submitting answer:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleNextQuestion = () => {
    if (session?.mode === 'interviewer_v2' && lastEvaluation?.completed) {
      handleEndInterview();
      return;
    }
    setLastEvaluation(null);
    loadNextQuestion();
  };

  const buildFallbackSummary = (note = '') => {
    const scores = questionHistory
      .map((item) => Number(item.evaluation?.score ?? 0))
      .filter((value) => Number.isFinite(value));
    const total = scores.reduce((sum, value) => sum + value, 0);
    const average = scores.length ? total / scores.length : 0;

    return {
      session_id: session?.session_id,
      overall_score: Number(average.toFixed(1)),
      strengths: [],
      improvements: [],
      study_topics: [],
      readiness: scores.length ? 'Summary generated' : 'No answers recorded',
      summary: note || 'Summary generated from available session data.',
      total_questions: questionHistory.length,
      platform: session?.platform,
      difficulty: session?.difficulty,
    };
  };

  const handleEndInterview = async () => {
    if (isEndingInterview) return;
    setIsEndingInterview(true);
    setIsProcessing(true);
    try {
      const summary = session?.mode === 'interviewer_v2'
        ? await apiService.completeInterviewerV2Session(session.session_id)
        : await apiService.completeSession(session.session_id);

      const normalizedSummary = session?.mode === 'interviewer_v2'
        ? {
            session_id: summary?.session_id,
            overall_score: Number(summary?.average_score ?? 0),
            strengths: Array.isArray(summary?.top_strengths) ? summary.top_strengths : [],
            improvements: Array.isArray(summary?.improvement_focus) ? summary.improvement_focus : [],
            study_topics: [],
            readiness: summary?.readiness_band || 'progressing',
            summary: summary?.summary || 'Interviewer-v2 session completed.',
            total_questions: Number(summary?.turns_answered ?? questionHistory.length),
            platform: session?.platform,
            difficulty: session?.difficulty,
            interview_experience_mode: session?.interview_experience_mode || 'learning',
            interview_readiness_score: summary?.interview_readiness_score,
            session_artifact_id: summary?.session_artifact_id,
            turn_reviews: Array.isArray(summary?.turn_reviews) ? summary.turn_reviews : [],
          }
        : summary;

      if (normalizedSummary && typeof normalizedSummary === 'object') {
        onComplete(normalizedSummary);
      } else {
        onComplete(buildFallbackSummary('Summary unavailable from server, using local results.'));
      }
    } catch (err) {
      setError('Failed to end interview. Please try again.');
      console.error('Error ending interview:', err);
      onComplete(buildFallbackSummary('Summary unavailable from server, using local results.'));
    } finally {
      setIsProcessing(false);
      setIsEndingInterview(false);
    }
  };

  useEffect(() => {
    const durationFromSession = Number(session?.interview_duration_minutes);
    const fallbackByDifficulty = session?.difficulty === 'junior' ? 30 : session?.difficulty === 'senior' ? 60 : 45;
    const minutes = Number.isFinite(durationFromSession) && durationFromSession > 0
      ? durationFromSession
      : fallbackByDifficulty;
    const totalSeconds = minutes * 60;
    setTotalDurationSeconds(totalSeconds);
    setRemainingSeconds(totalSeconds);
    hasAutoCompletedRef.current = false;
  }, [session?.interview_duration_minutes, session?.difficulty]);

  useEffect(() => {
    if (isInterviewRunMode) {
      setRunStartCountdown(5);
      hasStartedRunVoiceRef.current = false;
      return;
    }

    setRunStartCountdown(null);
    hasStartedRunVoiceRef.current = true;
  }, [session?.session_id, isInterviewRunMode]);

  useEffect(() => {
    if (!isCountdownActive) return;

    if (runStartCountdown === 0) {
      if (!hasStartedRunVoiceRef.current) {
        setTtsEnabled(true);
        if (currentQuestion) {
          speakQuestion(currentQuestion);
        }
        hasStartedRunVoiceRef.current = true;
      }

      const doneId = window.setTimeout(() => setRunStartCountdown(-1), 700);
      return () => window.clearTimeout(doneId);
    }

    const tickId = window.setTimeout(() => {
      setRunStartCountdown((previous) => {
        if (!Number.isFinite(previous)) return previous;
        return previous - 1;
      });
    }, 1000);

    return () => window.clearTimeout(tickId);
  }, [isCountdownActive, runStartCountdown, currentQuestion]);

  useEffect(() => {
    if (!Number.isFinite(remainingSeconds) || remainingSeconds === null) return;
    if (remainingSeconds <= 0 || isProcessing || isEndingInterview) return;

    const timerId = window.setInterval(() => {
      setRemainingSeconds((previous) => {
        if (!Number.isFinite(previous) || previous === null) return previous;
        return Math.max(0, previous - 1);
      });
    }, 1000);

    return () => window.clearInterval(timerId);
  }, [remainingSeconds, isProcessing, isEndingInterview]);

  useEffect(() => {
    if (remainingSeconds !== 0) return;
    if (hasAutoCompletedRef.current) return;
    hasAutoCompletedRef.current = true;
    handleEndInterview();
  }, [remainingSeconds]);

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-8">
      {/* Header */}
      <div className="glass-dark rounded-3xl p-4 mb-5 sm:mb-6 flex justify-between items-center border border-white/10">
        <div>
          <h2 className="text-lg sm:text-xl font-semibold">
            {session.platform.toUpperCase()} | {session.difficulty}
          </h2>
          <p className="text-sm text-gray-400">
            {session?.mode === 'interviewer_v2' ? 'Interviewer-v2' : 'Question'} {questionHistory.length + 1}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-wide text-slate-400">Time Remaining</p>
          <p className={`text-lg font-semibold ${getTimerTone(remainingSeconds)}`}>{formatDuration(remainingSeconds)}</p>
          {Number.isFinite(totalDurationSeconds) && Number.isFinite(remainingSeconds) && remainingSeconds <= 300 && (
            <p className="text-[11px] text-amber-300 mt-0.5">
              {remainingSeconds <= 60 ? 'Final minute' : 'Final 5 minutes'}
            </p>
          )}
        </div>
        <button
          onClick={handleEndInterview}
          disabled={isEndingInterview}
          className="btn btn-danger px-4 py-2"
        >
          {isEndingInterview ? 'Ending...' : 'End Interview'}
        </button>
      </div>

      {/* Question Display */}
        <div className="glass-dark rounded-3xl p-5 sm:p-8 mb-5 sm:mb-6 border border-white/10">
          <h3 className="text-base sm:text-lg font-semibold text-cyan-400 mb-4">Question:</h3>
          {currentQuestion ? (
            <p className="text-base sm:text-xl mb-5 sm:mb-6">{currentQuestion}</p>
          ) : (
            <p className="text-base sm:text-xl mb-5 sm:mb-6 text-gray-500 italic">
              {isProcessing ? 'Loading question...' : 'No question available'}
            </p>
          )}

          {/* Answer Input */}
          <div className="panel-soft p-4 mb-5 sm:mb-6">
            <div className="flex flex-wrap items-center gap-3 mb-4">
              <button
                type="button"
                onClick={() => setUserCamEnabled((prev) => !prev)}
                disabled={!hasWebcam}
                className={`btn px-4 py-2 ${userCamEnabled ? 'btn-info' : 'btn-secondary'}`}
              >
                {userCamEnabled ? 'User Webcam On' : 'User Webcam Off'}
              </button>

              <button
                type="button"
                onClick={() => setAiCamEnabled((prev) => !prev)}
                className={`btn px-4 py-2 ${aiCamEnabled ? 'btn-info' : 'btn-secondary'}`}
              >
                {aiCamEnabled ? 'AI Webcam On' : 'AI Webcam Off'}
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-2xl border border-white/10 bg-slate-800/40 p-3">
                <p className="text-xs text-slate-400 mb-2">User Camera</p>
                {userCamEnabled ? (
                  <video
                    ref={userVideoRef}
                    autoPlay
                    muted
                    playsInline
                    className="w-full h-56 lg:h-64 rounded-xl object-cover bg-black"
                  />
                ) : (
                  <div className="w-full h-56 lg:h-64 rounded-xl bg-slate-900/70 border border-white/10 flex items-center justify-center text-xs text-slate-400">
                    Camera is off
                  </div>
                )}
              </div>

              <div className="rounded-2xl border border-white/10 bg-slate-800/40 p-3">
                <p className="text-xs text-slate-400 mb-2">AI Camera</p>
                {aiCamEnabled ? (
                  <div className="w-full h-56 lg:h-64 rounded-xl border border-cyan-500/30 bg-gradient-to-br from-cyan-900/30 to-teal-900/30 flex flex-col items-center justify-center gap-3">
                    <div
                      className={`ai-avatar ${
                        isSpeaking ? 'ai-avatar-speaking' : isTtsLoading ? 'ai-avatar-thinking' : 'ai-avatar-idle'
                      }`}
                    >
                      <div className="ai-avatar-core">
                        <span className="text-cyan-200 text-lg font-semibold">AI</span>
                      </div>
                      {isTtsLoading && <div className="ai-thinking-ring" />}
                    </div>

                    <div className="ai-eq" aria-hidden="true">
                      {[0, 1, 2, 3, 4].map((bar) => (
                        <span
                          key={bar}
                          className={`ai-eq-bar ${isSpeaking ? 'ai-eq-bar-speaking' : 'ai-eq-bar-idle'}`}
                          style={{ animationDelay: `${bar * 0.1}s` }}
                        />
                      ))}
                    </div>

                    <p className="text-xs text-cyan-200">
                      {isTtsLoading ? 'Preparing response...' : isSpeaking ? 'Speaking...' : 'Listening...'}
                    </p>
                  </div>
                ) : (
                  <div className="w-full h-56 lg:h-64 rounded-xl bg-slate-900/70 border border-white/10 flex items-center justify-center text-xs text-slate-400">
                    Camera is off
                  </div>
                )}
              </div>
            </div>

            {webcamError && (
              <p className="text-xs text-amber-300 mt-3">{webcamError}</p>
            )}
          </div>

          <div className="mb-5 sm:mb-6">
            <textarea
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              placeholder="Type your answer here or use voice recording..."
              className="textarea-base h-28 sm:h-32 p-3 sm:p-4"
              disabled={isRecording || isProcessing}
            />
          </div>

          <div className="panel-soft p-4 mb-5 sm:mb-6">
            {!hasWebcam && (
              <div className="mb-4 rounded-xl border border-amber-500/40 bg-amber-500/10 p-3">
                <p className="text-xs text-amber-200">
                  No webcam detected for AI/user video. Interview continues in voice-only mode.
                </p>
              </div>
            )}

            {ttsNotice && (
              <div className="mb-4 rounded-xl border border-amber-500/40 bg-amber-500/10 p-3">
                <p className="text-xs text-amber-200">{ttsNotice}</p>
              </div>
            )}

            {(voiceRuntimeStatus?.enabled || isVoiceRuntimeLoading) && (
              <div className="mb-4 rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-3">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <p className="text-xs text-cyan-100">
                    Live Voice Room (beta): {livekitConnected ? 'Connected' : 'Disconnected'}
                  </p>
                  {voiceRuntimeStatus?.configured === false && (
                    <span className="text-[11px] text-amber-200">Not fully configured</span>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {!livekitConnected ? (
                    <button
                      type="button"
                      onClick={connectLivekitRoom}
                      disabled={
                        isLivekitConnecting ||
                        isVoiceRuntimeLoading ||
                        !voiceRuntimeStatus?.configured ||
                        !session?.session_id
                      }
                      className="btn btn-info px-3 py-2 text-xs"
                    >
                      {isLivekitConnecting ? 'Connecting...' : 'Join Voice Room'}
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={disconnectLivekitRoom}
                      className="btn btn-secondary px-3 py-2 text-xs"
                    >
                      Leave Voice Room
                    </button>
                  )}
                  {voiceRuntimeStatus?.livekit_url && (
                    <span className="text-[11px] text-cyan-100/90 break-all">
                      {voiceRuntimeStatus.livekit_url}
                    </span>
                  )}
                </div>
                {livekitError && <p className="mt-2 text-xs text-rose-200">{livekitError}</p>}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3 mb-4">
              <button
                type="button"
                onClick={() => setTtsEnabled((prev) => !prev)}
                className={`btn px-4 py-2 ${ttsEnabled ? 'btn-info' : 'btn-secondary'}`}
              >
                {ttsEnabled ? <FaVolumeUp /> : <FaVolumeMute />}
                {ttsEnabled ? 'AI Voice On' : 'AI Voice Off'}
              </button>
              <button
                type="button"
                onClick={() => speakQuestion(currentQuestion)}
                disabled={!currentQuestion || isProcessing || isTtsLoading}
                className="btn btn-success px-4 py-2"
              >
                {isTtsLoading ? 'Speaking...' : 'Speak Question'}
              </button>
              <button
                type="button"
                onClick={stopSpeaking}
                disabled={!isSpeaking}
                className="btn btn-danger px-4 py-2"
              >
                Stop Voice
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <label className="text-sm text-gray-300">
                Voice Source
                <select
                  value={ttsMode}
                  onChange={(event) => setTtsMode(event.target.value)}
                  className="input-base mt-2"
                >
                  <option value="browser">Browser</option>
                  <option value="api" disabled={!ttsBackendAvailable}>
                    ElevenLabs
                  </option>
                </select>
              </label>

              <label className="text-sm text-gray-300">
                Voice
                {ttsMode === 'api' ? (
                  <select
                    value={selectedApiVoice}
                    onChange={(event) => setSelectedApiVoice(event.target.value)}
                    className="input-base mt-2"
                    disabled={!ttsBackendAvailable || apiVoices.length === 0}
                  >
                    {apiVoices.length === 0 && <option value="">No API voices</option>}
                    {apiVoices.map((voice) => (
                      <option key={voice.voice_id} value={voice.voice_id}>
                        {voice.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <select
                    value={selectedVoice}
                    onChange={(event) => setSelectedVoice(event.target.value)}
                    className="input-base mt-2"
                  >
                    {voices.length === 0 && <option value="">System Default</option>}
                    {voices.map((voice) => (
                      <option key={voice.voiceURI} value={voice.voiceURI}>
                        {voice.name} ({voice.lang})
                      </option>
                    ))}
                  </select>
                )}
              </label>

              {ttsMode === 'api' && apiVoices.length === 0 && (
                <p className="text-xs text-amber-300">
                  ElevenLabs voices unavailable. Using default voice ID.
                </p>
              )}

              {!ttsBackendAvailable && ttsMode === 'browser' && (
                <p className="text-xs text-amber-300">
                  ElevenLabs unavailable ({ttsAvailabilityReason || 'provider_unavailable'}). Using browser voice.
                </p>
              )}

              <label className="text-sm text-gray-300">
                Speaking Speed: {speechRate.toFixed(2)}
                <input
                  type="range"
                  min="0.6"
                  max="1.4"
                  step="0.05"
                  value={speechRate}
                  onChange={(event) => setSpeechRate(Number(event.target.value))}
                  className="w-full mt-2"
                  disabled={ttsMode === 'api'}
                />
              </label>

              <label className="text-sm text-gray-300">
                Voice Pitch: {speechPitch.toFixed(2)}
                <input
                  type="range"
                  min="0.6"
                  max="1.4"
                  step="0.05"
                  value={speechPitch}
                  onChange={(event) => setSpeechPitch(Number(event.target.value))}
                  className="w-full mt-2"
                  disabled={ttsMode === 'api'}
                />
              </label>

              <label className="text-sm text-gray-300">
                Pause Between Sentences: {pauseMs}ms
                <input
                  type="range"
                  min="0"
                  max="1200"
                  step="50"
                  value={pauseMs}
                  onChange={(event) => setPauseMs(Number(event.target.value))}
                  className="w-full mt-2"
                  disabled={ttsMode === 'api'}
                />
              </label>

              <label className="text-sm text-gray-300">
                Voice Stability: {apiStability.toFixed(2)}
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={apiStability}
                  onChange={(event) => setApiStability(Number(event.target.value))}
                  className="w-full mt-2"
                  disabled={ttsMode !== 'api'}
                />
              </label>

              <label className="text-sm text-gray-300">
                Voice Similarity: {apiSimilarity.toFixed(2)}
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={apiSimilarity}
                  onChange={(event) => setApiSimilarity(Number(event.target.value))}
                  className="w-full mt-2"
                  disabled={ttsMode !== 'api'}
                />
              </label>
            </div>
          </div>

          {/* Controls */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
            {!isRecording ? (
              <button
                onClick={startRecording}
                disabled={isProcessing || isCountdownActive}
                className="btn btn-success px-6 py-3"
              >
                <FaMicrophone /> Start Recording
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="btn btn-danger px-6 py-3 animate-pulse"
              >
                <FaStop /> Stop Recording
              </button>
            )}

            <button
              onClick={submitAnswer}
              disabled={isRecording || isProcessing || !currentAnswer.trim() || remainingSeconds === 0 || isCountdownActive}
              className="btn btn-info px-6 py-3 sm:ml-auto"
            >
              <FaPaperPlane />
              {isProcessing ? 'Processing...' : 'Submit Answer'}
            </button>
          </div>
        </div>


      {isCountdownActive && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
          <div className="rounded-3xl border border-cyan-500/30 bg-slate-900/95 px-8 py-6 text-center shadow-2xl">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400 mb-2">Actual Interview Run</p>
            <p className="text-6xl font-bold text-cyan-300 mb-2">
              {runStartCountdown === 0 ? 'Start' : runStartCountdown}
            </p>
            <p className="text-sm text-slate-300">Stay focused. The AI interviewer is starting now.</p>
          </div>
        </div>
      )}
      {/* Error Display */}
      {error && (
        <div className="bg-red-900/50 border border-red-500 rounded-2xl p-4 mb-5 sm:mb-6">
          <p className="text-red-200">{error}</p>
        </div>
      )}

      {/* Question History */}
      {questionHistory.length > 0 && (
        <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
          <h3 className="text-base sm:text-lg font-semibold mb-4">Question History</h3>
          <div className="space-y-4">
            {questionHistory.map((item, index) => (
              <div key={index} className="border-l-4 border-cyan-500 pl-4">
                <p className="text-sm text-gray-400">Question {index + 1}</p>
                <p className="font-semibold mb-2">{item.question}</p>
                <div className="mb-2">
                  <p className="text-xs uppercase tracking-wide text-gray-500">Your Answer</p>
                  <p className="text-sm text-gray-300 whitespace-pre-wrap">
                    {item.answer || 'No answer recorded.'}
                  </p>
                </div>
                <p className="text-sm text-gray-300 mb-1">
                  Score: {item.evaluation.score}/10
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
