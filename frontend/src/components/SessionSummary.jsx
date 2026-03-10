import React, { useCallback, useEffect, useState } from 'react';
import { FaTrophy, FaCheckCircle, FaExclamationCircle, FaBook } from 'react-icons/fa';
import { apiService } from '../services/api';

const ARTIFACT_VIEW_PREFS_VERSION = 'v1';
const ARTIFACT_VIEW_PREFS_STORAGE_PREFIX = `devopsai:iv2-artifacts-view:${ARTIFACT_VIEW_PREFS_VERSION}`;
const DEFAULT_ARTIFACT_VIEW_PREFS = {
  statusFilter: '',
  readinessFilter: '',
  sortBy: 'created_at',
  sortOrder: 'desc',
  keepLatest: 10,
  pageSize: 20,
  currentPage: 1,
};

const ALLOWED_STATUS_FILTERS = new Set(['', 'completed']);
const ALLOWED_READINESS_FILTERS = new Set(['', 'emerging', 'progressing', 'interview_ready']);
const ALLOWED_SORT_BY = new Set(['created_at', 'average_score', 'interview_readiness_score']);
const ALLOWED_SORT_ORDER = new Set(['asc', 'desc']);
const ALLOWED_PAGE_SIZES = new Set([10, 20, 50, 100]);

function sanitizeArtifactViewPrefs(raw) {
  const candidate = raw && typeof raw === 'object' ? raw : {};
  const statusFilter = ALLOWED_STATUS_FILTERS.has(candidate.statusFilter)
    ? candidate.statusFilter
    : DEFAULT_ARTIFACT_VIEW_PREFS.statusFilter;

  const readinessFilter = ALLOWED_READINESS_FILTERS.has(candidate.readinessFilter)
    ? candidate.readinessFilter
    : DEFAULT_ARTIFACT_VIEW_PREFS.readinessFilter;

  const sortBy = ALLOWED_SORT_BY.has(candidate.sortBy)
    ? candidate.sortBy
    : DEFAULT_ARTIFACT_VIEW_PREFS.sortBy;

  const sortOrder = ALLOWED_SORT_ORDER.has(candidate.sortOrder)
    ? candidate.sortOrder
    : DEFAULT_ARTIFACT_VIEW_PREFS.sortOrder;

  const keepLatestRaw = Number(candidate.keepLatest);
  const keepLatest = Number.isFinite(keepLatestRaw)
    ? Math.max(0, Math.min(1000, Math.round(keepLatestRaw)))
    : DEFAULT_ARTIFACT_VIEW_PREFS.keepLatest;

  const pageSizeRaw = Number(candidate.pageSize);
  const pageSize = ALLOWED_PAGE_SIZES.has(pageSizeRaw)
    ? pageSizeRaw
    : DEFAULT_ARTIFACT_VIEW_PREFS.pageSize;

  const currentPageRaw = Number(candidate.currentPage);
  const currentPage = Number.isFinite(currentPageRaw)
    ? Math.max(1, Math.round(currentPageRaw))
    : DEFAULT_ARTIFACT_VIEW_PREFS.currentPage;

  return {
    statusFilter,
    readinessFilter,
    sortBy,
    sortOrder,
    keepLatest,
    pageSize,
    currentPage,
  };
}

export default function SessionSummary({ summary, onRestart, currentUser }) {
  const safeSummary = {
    overall_score: 0,
    strengths: [],
    improvements: [],
    study_topics: [],
    turn_reviews: [],
    readiness: '',
    summary: '',
    total_questions: 0,
    platform: 'unknown',
    difficulty: 'unknown',
    ...(summary || {}),
  };

  const [artifacts, setArtifacts] = useState([]);
  const [artifactTotal, setArtifactTotal] = useState(0);
  const [artifactLoading, setArtifactLoading] = useState(false);
  const [artifactError, setArtifactError] = useState('');
  const [artifactNotice, setArtifactNotice] = useState('');
  const [statusFilter, setStatusFilter] = useState(DEFAULT_ARTIFACT_VIEW_PREFS.statusFilter);
  const [readinessFilter, setReadinessFilter] = useState(DEFAULT_ARTIFACT_VIEW_PREFS.readinessFilter);
  const [sortBy, setSortBy] = useState(DEFAULT_ARTIFACT_VIEW_PREFS.sortBy);
  const [sortOrder, setSortOrder] = useState(DEFAULT_ARTIFACT_VIEW_PREFS.sortOrder);
  const [keepLatest, setKeepLatest] = useState(DEFAULT_ARTIFACT_VIEW_PREFS.keepLatest);
  const [pageSize, setPageSize] = useState(DEFAULT_ARTIFACT_VIEW_PREFS.pageSize);
  const [currentPage, setCurrentPage] = useState(DEFAULT_ARTIFACT_VIEW_PREFS.currentPage);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [deletingArtifactId, setDeletingArtifactId] = useState('');
  const [viewPrefsHydrated, setViewPrefsHydrated] = useState(false);
  const [pageInput, setPageInput] = useState(String(DEFAULT_ARTIFACT_VIEW_PREFS.currentPage));
  const [expandedTeachItems, setExpandedTeachItems] = useState({});
  const [teachNotice, setTeachNotice] = useState('');

  const isArtifactActionInFlight = artifactLoading || cleanupLoading || Boolean(deletingArtifactId);
  const artifactOffset = (currentPage - 1) * pageSize;
  const totalPages = Math.max(1, Math.ceil((artifactTotal || 0) / pageSize));
  const canGoPreviousPage = currentPage > 1;
  const canGoNextPage = currentPage < totalPages;
  const currentRangeStart = artifactTotal === 0 ? 0 : artifactOffset + 1;
  const currentRangeEnd = Math.min(artifactOffset + artifacts.length, artifactTotal);
  const artifactViewPrefsStorageKey = currentUser?.user_id
    ? `${ARTIFACT_VIEW_PREFS_STORAGE_PREFIX}:${currentUser.user_id}`
    : null;

  const getScoreColor = (score) => {
    if (score >= 8) return 'text-cyan-400';
    if (score >= 6) return 'text-teal-300';
    return 'text-red-400';
  };

  const getReadinessColor = () => {
    const readiness = (safeSummary.readiness || '').toLowerCase();
    if (readiness.includes('ready') || readiness.includes('excellent')) return 'text-cyan-300';
    if (readiness.includes('practice') || readiness.includes('improve')) return 'text-teal-300';
    return 'text-slate-300';
  };

  const competencyPlaybook = {
    'Cloud Architecture': {
      keyPhrases: ['RTO/RPO targets', 'failure-domain isolation', 'global traffic routing', 'consistency trade-off', 'cost-aware scaling'],
      followUps: [
        'How would you fail over a region with minimal user impact?',
        'What consistency model would you choose for critical writes and why?',
        'How would you prove resilience before production launch?',
      ],
    },
    'Kubernetes Operations': {
      keyPhrases: ['evidence-first triage', 'events/logs correlation', 'probe and resource validation', 'safe rollback'],
      followUps: [
        'What is your first 5-minute triage checklist?',
        'How do you distinguish app bugs from platform issues?',
        'What safeguards prevent recurrence?',
      ],
    },
    'Observability and Monitoring': {
      keyPhrases: ['SLO-driven alerts', 'golden signals', 'trace correlation', 'noise reduction'],
      followUps: [
        'How do you tune alerts to reduce false positives?',
        'Which SLI would you prioritize for customer impact?',
        'How do logs and traces complement metrics during incidents?',
      ],
    },
    'CI/CD and Automation': {
      keyPhrases: ['progressive delivery', 'quality gates', 'rollback strategy', 'change risk control'],
      followUps: [
        'How would you handle a bad deployment in peak traffic?',
        'What checks must pass before promotion?',
        'How do you balance speed and reliability?',
      ],
    },
    'Security and Governance': {
      keyPhrases: ['least privilege', 'secrets lifecycle', 'policy-as-code', 'audit evidence'],
      followUps: [
        'How do you enforce least privilege at scale?',
        'How do you handle secret rotation safely?',
        'How do you make compliance evidence continuous?',
      ],
    },
    'Incident Response': {
      keyPhrases: ['incident command', 'clear stakeholder comms', 'service restoration', 'blameless postmortem'],
      followUps: [
        'How do you structure communication during Sev-1?',
        'How do you decide rollback vs mitigation?',
        'How do you ensure postmortem actions are completed?',
      ],
    },
  };

  const buildTeachPlan = (review) => {
    const competency = review?.competency || 'General';
    const modelAnswer = String(review?.model_answer || '').trim();
    const firstSentence = modelAnswer.split('. ').slice(0, 1).join('. ').trim();
    const openingLine = firstSentence ? `${firstSentence}${firstSentence.endsWith('.') ? '' : '.'}` : 'I would answer this by stating context, approach, trade-offs, and validation.';
    const profile = competencyPlaybook[competency] || {
      keyPhrases: ['structured approach', 'trade-offs', 'risk mitigation', 'validation in production'],
      followUps: [
        'What constraints matter most for this design?',
        'Which trade-off would you prioritize and why?',
        'How would you validate success after implementation?',
      ],
    };

    return {
      openingLine,
      talkTrack: [
        'State the business goal and technical constraints first.',
        'Present a concrete architecture or execution approach step-by-step.',
        'Call out trade-offs, risks, and fallback options explicitly.',
        'Close with how you monitor outcomes and improve over time.',
      ],
      keyPhrases: profile.keyPhrases,
      followUps: profile.followUps,
    };
  };

  const buildPracticeScript = (review) => {
    const plan = buildTeachPlan(review);
    return [
      `Question: ${review?.question || 'N/A'}`,
      '',
      'Suggested Opening:',
      plan.openingLine,
      '',
      'Talk Track:',
      ...plan.talkTrack.map((step, index) => `${index + 1}. ${step}`),
      '',
      `Key Phrases: ${plan.keyPhrases.join(', ')}`,
      '',
      'Likely Follow-up Questions:',
      ...plan.followUps.map((question, index) => `${index + 1}. ${question}`),
    ].join('\n');
  };

  const handleCopyPracticeScript = async (review) => {
    const script = buildPracticeScript(review);
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(script);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = script;
        textarea.setAttribute('readonly', '');
        textarea.style.position = 'absolute';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
      setTeachNotice('Practice script copied to clipboard.');
    } catch (error) {
      setTeachNotice('Could not copy script automatically. Please copy manually.');
    }
  };

  useEffect(() => {
    if (!teachNotice) return;
    const timeoutId = window.setTimeout(() => setTeachNotice(''), 3500);
    return () => window.clearTimeout(timeoutId);
  }, [teachNotice]);

  useEffect(() => {
    if (!Array.isArray(safeSummary.turn_reviews) || safeSummary.turn_reviews.length === 0) {
      setExpandedTeachItems({});
      return;
    }

    setExpandedTeachItems({ 0: true });
  }, [safeSummary.session_id, safeSummary.turn_reviews]);

  const loadArtifacts = useCallback(async () => {
    if (!currentUser) return;
    setArtifactLoading(true);
    setArtifactError('');
    try {
      const data = await apiService.listInterviewerV2Artifacts({
        limit: pageSize,
        offset: artifactOffset,
        status: statusFilter || undefined,
        readiness_band: readinessFilter || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setArtifacts(Array.isArray(data?.items) ? data.items : []);
      setArtifactTotal(Number(data?.total || 0));
    } catch (err) {
      setArtifactError(err?.response?.data?.detail || 'Failed to load interviewer-v2 artifacts.');
    } finally {
      setArtifactLoading(false);
    }
  }, [artifactOffset, currentUser, pageSize, readinessFilter, sortBy, sortOrder, statusFilter]);

  useEffect(() => {
    if (!currentUser || !artifactViewPrefsStorageKey) {
      setViewPrefsHydrated(false);
      return;
    }

    try {
      const raw = window.localStorage.getItem(artifactViewPrefsStorageKey);
      if (!raw) {
        setStatusFilter(DEFAULT_ARTIFACT_VIEW_PREFS.statusFilter);
        setReadinessFilter(DEFAULT_ARTIFACT_VIEW_PREFS.readinessFilter);
        setSortBy(DEFAULT_ARTIFACT_VIEW_PREFS.sortBy);
        setSortOrder(DEFAULT_ARTIFACT_VIEW_PREFS.sortOrder);
        setKeepLatest(DEFAULT_ARTIFACT_VIEW_PREFS.keepLatest);
        setPageSize(DEFAULT_ARTIFACT_VIEW_PREFS.pageSize);
        setCurrentPage(DEFAULT_ARTIFACT_VIEW_PREFS.currentPage);
        setViewPrefsHydrated(true);
        return;
      }

      const parsed = JSON.parse(raw);
      const safePrefs = sanitizeArtifactViewPrefs(parsed);
      setStatusFilter(safePrefs.statusFilter);
      setReadinessFilter(safePrefs.readinessFilter);
      setSortBy(safePrefs.sortBy);
      setSortOrder(safePrefs.sortOrder);
      setKeepLatest(safePrefs.keepLatest);
      setPageSize(safePrefs.pageSize);
      setCurrentPage(safePrefs.currentPage);
    } catch (error) {
      setStatusFilter(DEFAULT_ARTIFACT_VIEW_PREFS.statusFilter);
      setReadinessFilter(DEFAULT_ARTIFACT_VIEW_PREFS.readinessFilter);
      setSortBy(DEFAULT_ARTIFACT_VIEW_PREFS.sortBy);
      setSortOrder(DEFAULT_ARTIFACT_VIEW_PREFS.sortOrder);
      setKeepLatest(DEFAULT_ARTIFACT_VIEW_PREFS.keepLatest);
      setPageSize(DEFAULT_ARTIFACT_VIEW_PREFS.pageSize);
      setCurrentPage(DEFAULT_ARTIFACT_VIEW_PREFS.currentPage);
    } finally {
      setViewPrefsHydrated(true);
    }
  }, [artifactViewPrefsStorageKey, currentUser]);

  useEffect(() => {
    if (!currentUser || !artifactViewPrefsStorageKey || !viewPrefsHydrated) return;

    const payload = sanitizeArtifactViewPrefs({
      statusFilter,
      readinessFilter,
      sortBy,
      sortOrder,
      keepLatest,
      pageSize,
      currentPage,
    });

    const timeoutId = window.setTimeout(() => {
      window.localStorage.setItem(artifactViewPrefsStorageKey, JSON.stringify(payload));
    }, 200);

    return () => window.clearTimeout(timeoutId);
  }, [
    artifactViewPrefsStorageKey,
    currentUser,
    keepLatest,
    currentPage,
    pageSize,
    readinessFilter,
    sortBy,
    sortOrder,
    statusFilter,
    viewPrefsHydrated,
  ]);

  useEffect(() => {
    if (artifactLoading) return;
    if (artifactTotal > 0 && artifacts.length === 0 && currentPage > 1) {
      setCurrentPage((previous) => Math.max(1, previous - 1));
    }
  }, [artifactLoading, artifactTotal, artifacts.length, currentPage]);

  useEffect(() => {
    if (!currentUser || !viewPrefsHydrated) return;
    loadArtifacts();
  }, [currentUser, loadArtifacts, viewPrefsHydrated]);

  useEffect(() => {
    if (!artifactNotice) return;
    const timeoutId = window.setTimeout(() => {
      setArtifactNotice('');
    }, 4000);
    return () => window.clearTimeout(timeoutId);
  }, [artifactNotice]);

  useEffect(() => {
    setPageInput(String(currentPage));
  }, [currentPage]);

  useEffect(() => {
    if (!artifactError) return;
    const timeoutId = window.setTimeout(() => {
      setArtifactError('');
    }, 6000);
    return () => window.clearTimeout(timeoutId);
  }, [artifactError]);

  const handleDeleteArtifact = async (artifactId) => {
    if (!artifactId) return;
    if (!window.confirm('Delete this artifact permanently?')) return;
    setArtifactNotice('');
    setArtifactError('');
    setDeletingArtifactId(artifactId);
    try {
      await apiService.deleteInterviewerV2ArtifactById(artifactId);
      setArtifactNotice('Artifact deleted.');
      await loadArtifacts();
    } catch (err) {
      setArtifactError(err?.response?.data?.detail || 'Failed to delete artifact.');
    } finally {
      setDeletingArtifactId('');
    }
  };

  const handleCleanupArtifacts = async (dryRun) => {
    if (!dryRun && !window.confirm('Apply retention cleanup now? Older artifacts beyond keep_latest will be deleted.')) {
      return;
    }
    setArtifactNotice('');
    setArtifactError('');
    const safeKeepLatest = Number.isFinite(Number(keepLatest)) ? Number(keepLatest) : 10;
    setCleanupLoading(true);
    try {
      const result = await apiService.cleanupInterviewerV2Artifacts({
        keep_latest: Math.max(0, Math.min(1000, safeKeepLatest)),
        dry_run: dryRun,
      });
      if (dryRun) {
        setArtifactNotice(`Dry run: ${result.removed_count || 0} artifacts would be removed.`);
      } else {
        setArtifactNotice(`Cleanup complete: removed ${result.removed_count || 0} artifact(s).`);
        await loadArtifacts();
      }
    } catch (err) {
      setArtifactError(err?.response?.data?.detail || 'Failed to cleanup artifacts.');
    } finally {
      setCleanupLoading(false);
    }
  };

  const handleResetArtifactView = () => {
    setStatusFilter(DEFAULT_ARTIFACT_VIEW_PREFS.statusFilter);
    setReadinessFilter(DEFAULT_ARTIFACT_VIEW_PREFS.readinessFilter);
    setSortBy(DEFAULT_ARTIFACT_VIEW_PREFS.sortBy);
    setSortOrder(DEFAULT_ARTIFACT_VIEW_PREFS.sortOrder);
    setKeepLatest(DEFAULT_ARTIFACT_VIEW_PREFS.keepLatest);
    setPageSize(DEFAULT_ARTIFACT_VIEW_PREFS.pageSize);
    setCurrentPage(DEFAULT_ARTIFACT_VIEW_PREFS.currentPage);
    if (artifactViewPrefsStorageKey) {
      window.localStorage.removeItem(artifactViewPrefsStorageKey);
    }
    setArtifactNotice('Artifact view reset to defaults.');
    setArtifactError('');
  };

  const handleStatusFilterChange = (event) => {
    setStatusFilter(event.target.value);
    setCurrentPage(1);
  };

  const handleReadinessFilterChange = (event) => {
    setReadinessFilter(event.target.value);
    setCurrentPage(1);
  };

  const handleSortByChange = (event) => {
    setSortBy(event.target.value);
    setCurrentPage(1);
  };

  const handleSortOrderChange = (event) => {
    setSortOrder(event.target.value);
    setCurrentPage(1);
  };

  const handlePageSizeChange = (event) => {
    const next = Number(event.target.value);
    if (!ALLOWED_PAGE_SIZES.has(next)) return;
    setPageSize(next);
    setCurrentPage(1);
  };

  const goToPage = () => {
    const parsed = Number(pageInput);
    if (!Number.isFinite(parsed)) {
      setArtifactError('Enter a valid page number.');
      return;
    }

    const targetPage = Math.round(parsed);
    if (targetPage < 1 || targetPage > totalPages) {
      setArtifactError(`Page must be between 1 and ${totalPages}.`);
      return;
    }

    setArtifactError('');
    setCurrentPage(targetPage);
  };

  const handlePageInputKeyDown = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      goToPage();
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-8">
      <div className="text-center mb-6 sm:mb-8">
        <FaTrophy className="text-5xl sm:text-6xl mx-auto mb-4 text-cyan-400" />
        <h1 className="text-2xl sm:text-3xl font-bold mb-2">Interview Complete!</h1>
        <p className="text-sm sm:text-base text-gray-400">Here's your performance summary</p>
      </div>

      <div className="glass-dark rounded-3xl p-5 sm:p-8 mb-6 border border-white/10">
        {/* Overall Score */}
        <div className="text-center mb-8 pb-8 border-b border-white/10">
          <h2 className="text-lg sm:text-xl font-semibold mb-4">Overall Score</h2>
          <div className={`text-5xl sm:text-6xl font-bold ${getScoreColor(safeSummary.overall_score)}`}>
            {Number(safeSummary.overall_score).toFixed(1)}/10
          </div>
          <p className="text-gray-400 mt-4">
            {String(safeSummary.platform).toUpperCase()} - {safeSummary.difficulty} Level
          </p>
          <p className="text-sm text-gray-500">
            {safeSummary.total_questions} questions answered
          </p>
        </div>

        {/* Readiness Assessment */}
        <div className="mb-8 pb-8 border-b border-white/10">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <FaCheckCircle className="text-cyan-400" />
            Readiness Assessment
          </h3>
          <p className={`text-xl ${getReadinessColor()}`}>{safeSummary.readiness || 'Summary pending'}</p>
          <p className="text-gray-300 mt-4">{safeSummary.summary || 'No summary text available yet.'}</p>
        </div>

        {/* Strengths */}
        {safeSummary.strengths && safeSummary.strengths.length > 0 && (
          <div className="mb-8 pb-8 border-b border-white/10">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FaCheckCircle className="text-teal-300" />
              Your Strengths
            </h3>
            <ul className="space-y-2">
              {safeSummary.strengths.map((strength, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="text-cyan-300 mt-1">✓</span>
                  <span className="text-gray-300">{strength}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Areas for Improvement */}
        {safeSummary.improvements && safeSummary.improvements.length > 0 && (
          <div className="mb-8 pb-8 border-b border-white/10">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FaExclamationCircle className="text-cyan-300" />
              Areas for Improvement
            </h3>
            <ul className="space-y-2">
              {safeSummary.improvements.map((improvement, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="text-teal-300 mt-1">→</span>
                  <span className="text-gray-300">{improvement}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Study Topics */}
        {safeSummary.study_topics && safeSummary.study_topics.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FaBook className="text-cyan-300" />
              Recommended Study Topics
            </h3>
            <div className="flex flex-wrap gap-2">
              {safeSummary.study_topics.map((topic, index) => (
                <span
                  key={index}
                  className="px-4 py-2 bg-cyan-900/40 border border-cyan-500 rounded-full text-sm"
                >
                  {topic}
                </span>
              ))}
            </div>
          </div>
        )}

        {Array.isArray(safeSummary.turn_reviews) && safeSummary.turn_reviews.length > 0 && (
          <div className="mb-8 pb-8 border-b border-white/10">
            <h3 className="text-lg font-semibold mb-4">Detailed Answer Coaching</h3>
            {teachNotice && (
              <p className="text-sm text-cyan-300 mb-3" role="status" aria-live="polite">
                {teachNotice}
              </p>
            )}
            <div className="space-y-4">
              {safeSummary.turn_reviews.map((review, index) => (
                <div key={`${review.turn_number || index}-${index}`} className="panel-soft p-4">
                  <p className="text-xs text-slate-400 mb-2">
                    Question {review.turn_number || index + 1} • {review.competency || 'General'} • Score {Number(review.score || 0).toFixed(1)}/10
                  </p>
                  <p className="text-sm text-white mb-3">{review.question || 'Question unavailable.'}</p>

                  <div className="mb-3">
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Your Answer</p>
                    <p className="text-sm text-slate-300 whitespace-pre-wrap">{review.user_response || 'No answer recorded.'}</p>
                  </div>

                  <div className="mb-3">
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Feedback</p>
                    <p className="text-sm text-slate-300 whitespace-pre-wrap">{review.feedback || 'No feedback available.'}</p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">How You Could Answer Better</p>
                    <p className="text-sm text-cyan-200 whitespace-pre-wrap">{review.model_answer || 'Model answer unavailable.'}</p>
                  </div>

                  <div className="mt-4">
                    <button
                      type="button"
                      onClick={() => setExpandedTeachItems((previous) => ({
                        ...previous,
                        [index]: !previous[index],
                      }))}
                      className="btn btn-secondary px-3 py-1.5 text-xs"
                    >
                      {expandedTeachItems[index] ? 'Hide teach mode' : 'Teach me this answer'}
                    </button>
                  </div>

                  {expandedTeachItems[index] && (
                    <div className="mt-4 rounded-2xl border border-cyan-500/30 bg-cyan-500/10 p-4 space-y-3">
                      <div className="flex justify-end">
                        <button
                          type="button"
                          onClick={() => handleCopyPracticeScript(review)}
                          className="btn btn-info px-3 py-1.5 text-xs"
                        >
                          Copy practice script
                        </button>
                      </div>

                      <div>
                        <p className="text-xs uppercase tracking-wide text-cyan-200 mb-1">Sample Opening</p>
                        <p className="text-sm text-cyan-100">{buildTeachPlan(review).openingLine}</p>
                      </div>

                      <div>
                        <p className="text-xs uppercase tracking-wide text-cyan-200 mb-1">Talk Track</p>
                        <ol className="list-decimal list-inside text-sm text-slate-200 space-y-1">
                          {buildTeachPlan(review).talkTrack.map((step, stepIndex) => (
                            <li key={`${index}-talk-${stepIndex}`}>{step}</li>
                          ))}
                        </ol>
                      </div>

                      <div>
                        <p className="text-xs uppercase tracking-wide text-cyan-200 mb-1">Key Phrases to Use</p>
                        <div className="flex flex-wrap gap-2">
                          {buildTeachPlan(review).keyPhrases.map((phrase, phraseIndex) => (
                            <span key={`${index}-phrase-${phraseIndex}`} className="chip text-xs">
                              {phrase}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div>
                        <p className="text-xs uppercase tracking-wide text-cyan-200 mb-1">Likely Follow-up Questions</p>
                        <ul className="list-disc list-inside text-sm text-slate-200 space-y-1">
                          {buildTeachPlan(review).followUps.map((question, qIndex) => (
                            <li key={`${index}-followup-${qIndex}`}>{question}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {currentUser && (
          <div
            className="mb-8 pb-8 border-b border-white/10"
            role="region"
            aria-labelledby="iv2-artifacts-heading"
            aria-busy={artifactLoading}
          >
            <h3 id="iv2-artifacts-heading" className="text-lg font-semibold mb-4">Interviewer-v2 Artifacts</h3>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-4">
              <select
                value={statusFilter}
                onChange={handleStatusFilterChange}
                className="bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm"
                aria-label="Filter artifacts by status"
                disabled={isArtifactActionInFlight}
              >
                <option value="">All Statuses</option>
                <option value="completed">completed</option>
              </select>

              <select
                value={readinessFilter}
                onChange={handleReadinessFilterChange}
                className="bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm"
                aria-label="Filter artifacts by readiness band"
                disabled={isArtifactActionInFlight}
              >
                <option value="">All Readiness Bands</option>
                <option value="emerging">emerging</option>
                <option value="progressing">progressing</option>
                <option value="interview_ready">interview_ready</option>
              </select>

              <select
                value={sortBy}
                onChange={handleSortByChange}
                className="bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm"
                aria-label="Sort artifacts by field"
                disabled={isArtifactActionInFlight}
              >
                <option value="created_at">created_at</option>
                <option value="average_score">average_score</option>
                <option value="interview_readiness_score">interview_readiness_score</option>
              </select>

              <select
                value={sortOrder}
                onChange={handleSortOrderChange}
                className="bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm"
                aria-label="Sort artifacts order"
                disabled={isArtifactActionInFlight}
              >
                <option value="desc">desc</option>
                <option value="asc">asc</option>
              </select>

              <select
                value={pageSize}
                onChange={handlePageSizeChange}
                className="bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm"
                aria-label="Artifacts per page"
                disabled={isArtifactActionInFlight}
              >
                <option value={10}>10 / page</option>
                <option value={20}>20 / page</option>
                <option value={50}>50 / page</option>
                <option value={100}>100 / page</option>
              </select>
            </div>

            <div className="flex flex-wrap gap-3 mb-4">
              <button
                onClick={loadArtifacts}
                className="btn btn-info px-4 py-2 text-sm"
                aria-label="Refresh artifact list"
                disabled={isArtifactActionInFlight}
              >
                {artifactLoading ? 'Refreshing...' : 'Refresh Artifacts'}
              </button>

              <button
                onClick={handleResetArtifactView}
                className="btn btn-secondary px-4 py-2 text-sm"
                aria-label="Reset artifact view filters sorting and pagination"
                disabled={isArtifactActionInFlight}
              >
                Reset View
              </button>

              <input
                type="number"
                min={0}
                max={1000}
                value={keepLatest}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  if (!Number.isFinite(next)) {
                    setKeepLatest(DEFAULT_ARTIFACT_VIEW_PREFS.keepLatest);
                    return;
                  }
                  setKeepLatest(Math.max(0, Math.min(1000, Math.round(next))));
                }}
                className="bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm w-28"
                aria-label="Keep latest count"
                disabled={isArtifactActionInFlight}
              />

              <button
                onClick={() => handleCleanupArtifacts(true)}
                className="btn btn-secondary px-4 py-2 text-sm"
                aria-label="Run cleanup dry run for artifacts"
                disabled={isArtifactActionInFlight}
              >
                {cleanupLoading ? 'Working...' : 'Cleanup Dry Run'}
              </button>

              <button
                onClick={() => handleCleanupArtifacts(false)}
                className="btn btn-warning px-4 py-2 text-sm"
                aria-label="Apply artifact cleanup retention policy"
                disabled={isArtifactActionInFlight}
              >
                {cleanupLoading ? 'Working...' : 'Cleanup Apply'}
              </button>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
              <p className="text-sm text-gray-400">
                Total artifacts: {artifactTotal} {artifactTotal > 0 ? `(showing ${currentRangeStart}-${currentRangeEnd})` : ''}
              </p>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage((previous) => Math.max(1, previous - 1))}
                  className="btn btn-secondary px-3 py-1.5 text-xs"
                  aria-label="Go to previous artifact page"
                  disabled={isArtifactActionInFlight || !canGoPreviousPage}
                >
                  Previous
                </button>
                <span className="text-xs text-gray-400">Page {currentPage} / {totalPages}</span>
                <button
                  onClick={() => setCurrentPage((previous) => Math.min(totalPages, previous + 1))}
                  className="btn btn-secondary px-3 py-1.5 text-xs"
                  aria-label="Go to next artifact page"
                  disabled={isArtifactActionInFlight || !canGoNextPage}
                >
                  Next
                </button>

                <input
                  type="number"
                  min={1}
                  max={totalPages}
                  value={pageInput}
                  onChange={(event) => setPageInput(event.target.value)}
                  onKeyDown={handlePageInputKeyDown}
                  className="bg-slate-800 border border-white/10 rounded-xl px-2 py-1 text-xs w-20"
                  aria-label="Go to page"
                  disabled={isArtifactActionInFlight}
                />

                <button
                  onClick={goToPage}
                  className="btn btn-secondary px-3 py-1.5 text-xs"
                  aria-label="Go to selected artifact page"
                  disabled={isArtifactActionInFlight}
                >
                  Go
                </button>
              </div>
            </div>

            {artifactError && (
              <p className="text-sm text-red-300 mb-3" role="alert" aria-live="assertive">
                {artifactError}
              </p>
            )}
            {artifactNotice && (
              <p className="text-sm text-cyan-300 mb-3" role="status" aria-live="polite">
                {artifactNotice}
              </p>
            )}

            <div className="space-y-2">
              {artifactLoading ? (
                <p className="text-sm text-gray-500">Loading artifacts...</p>
              ) : artifacts.length === 0 ? (
                <p className="text-sm text-gray-500">
                  {statusFilter || readinessFilter
                    ? 'No artifacts match the current filters. Adjust filters and try refresh.'
                    : 'No interviewer-v2 artifacts yet. Complete an interviewer-v2 session to create one.'}
                </p>
              ) : (
                artifacts.map((item) => (
                  <div key={item.session_artifact_id} className="border border-white/10 rounded-xl p-3 bg-slate-900/40">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                      <div>
                        <p className="text-sm text-white font-medium">{item.session_artifact_id}</p>
                        <p className="text-xs text-gray-400">
                          score: {Number(item.average_score || 0).toFixed(1)} | readiness: {item.readiness_band || 'n/a'}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteArtifact(item.session_artifact_id)}
                        className="btn btn-danger px-3 py-1.5 text-xs"
                        aria-label={`Delete artifact ${item.session_artifact_id}`}
                        disabled={isArtifactActionInFlight}
                      >
                        {deletingArtifactId === item.session_artifact_id ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Action Button */}
        <button
          onClick={onRestart}
          className="btn btn-info w-full py-3 sm:py-4 text-base sm:text-lg"
        >
          Start New Interview
        </button>
      </div>
    </div>
  );
}
