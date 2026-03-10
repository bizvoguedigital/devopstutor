import { create } from 'zustand';

export const useInterviewStore = create((set, get) => ({
  // Current session state
  session: null,
  currentQuestion: null,
  currentQuestionId: null,
  questionHistory: [],
  isRecording: false,
  isProcessing: false,
  currentAnswer: '',
  lastEvaluation: null,

  // Session actions
  setSession: (session) => set({ session }),

  clearSession: () => set({
    session: null,
    currentQuestion: null,
    currentQuestionId: null,
    questionHistory: [],
    currentAnswer: '',
    lastEvaluation: null,
  }),

  // Question actions
  setCurrentQuestion: (question, questionId) => set({
    currentQuestion: question,
    currentQuestionId: questionId,
    currentAnswer: '',
    lastEvaluation: null,
  }),

  addToHistory: (question, answer, evaluation) => {
    const history = get().questionHistory;
    set({
      questionHistory: [
        ...history,
        { question, answer, evaluation, timestamp: new Date() }
      ]
    });
  },

  // Answer actions
  setCurrentAnswer: (answer) => set({ currentAnswer: answer }),

  setLastEvaluation: (evaluation) => set({ lastEvaluation: evaluation }),

  // Recording state
  setIsRecording: (isRecording) => set({ isRecording }),

  setIsProcessing: (isProcessing) => set({ isProcessing }),
}));
