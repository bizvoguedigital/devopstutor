import React, { useEffect, useState } from 'react';
import { FaCog, FaDatabase, FaSave, FaSyncAlt, FaTrash, FaVolumeMute } from 'react-icons/fa';
import { apiService } from '../services/api';

export default function AdminConsole({ currentUser, onBack }) {
  const [overview, setOverview] = useState(null);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncingJourneyContent, setSyncingJourneyContent] = useState(false);
  const [syncForm, setSyncForm] = useState({
    cloud_provider: '',
    experience_level: '',
    force_refresh: false,
  });
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncResult, setSyncResult] = useState(null);
  const [ttsProviderStatus, setTtsProviderStatus] = useState(null);
  const [testingTts, setTestingTts] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [overviewData, configData] = await Promise.all([
        apiService.getAdminOverview(),
        apiService.getAdminConfig(),
      ]);
      setOverview(overviewData);
      setConfig(configData);
      const providerStatus = await apiService.getAdminTtsProviderStatus(true);
      setTtsProviderStatus(providerStatus);
      const status = await apiService.getJourneyContentSyncStatus();
      setSyncStatus(status);
      if (!status?.is_running) {
        setSyncResult(status);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load admin console data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (!syncStatus?.is_running) return undefined;

    const timer = setInterval(async () => {
      try {
        const status = await apiService.getJourneyContentSyncStatus();
        setSyncStatus(status);
        if (!status?.is_running) {
          setSyncResult(status);
          setMessage(`Journey content sync ${status?.status || 'completed'}.`);
        }
      } catch {
      }
    }, 5000);

    return () => clearInterval(timer);
  }, [syncStatus?.is_running]);

  const updateField = (field, value) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  const saveConfig = async () => {
    if (!config) return;
    setSaving(true);
    setError('');
    setMessage('');

    try {
      const payload = {
        tts_default_voice_id: config.tts_default_voice_id,
        tts_model_id: config.tts_model_id,
        tts_stability: Number(config.tts_stability),
        tts_similarity: Number(config.tts_similarity),
        tts_cache_enabled: Boolean(config.tts_cache_enabled),
        tts_cache_ttl_seconds: Number(config.tts_cache_ttl_seconds),
        tts_cache_max_files: Number(config.tts_cache_max_files),
        max_question_count: Number(config.max_question_count),
        session_timeout: Number(config.session_timeout),
      };

      const updated = await apiService.updateAdminConfig(payload);
      setConfig(updated);
      setMessage('Configuration saved successfully.');
      await loadData();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to save config.');
    } finally {
      setSaving(false);
    }
  };

  const clearCache = async () => {
    setError('');
    setMessage('');
    try {
      const result = await apiService.clearTtsCache();
      setMessage(`Cleared ${result?.removed_files ?? 0} cached audio file(s).`);
      await loadData();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to clear TTS cache.');
    }
  };

  const refreshTtsProviderStatus = async () => {
    setError('');
    setMessage('');
    try {
      const status = await apiService.getAdminTtsProviderStatus(true);
      setTtsProviderStatus(status);
      if (status?.available) {
        setMessage('ElevenLabs provider is ready.');
      } else {
        setMessage(`ElevenLabs not ready: ${status?.availability_reason || 'unknown_reason'}`);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to refresh TTS provider status.');
    }
  };

  const runTtsTest = async () => {
    setTestingTts(true);
    setError('');
    setMessage('');
    try {
      const result = await apiService.runAdminTtsTest({});
      if (result?.success) {
        setMessage(`TTS test succeeded. Generated ${result.generated_bytes} bytes.`);
      } else {
        setError(result?.message || 'TTS test failed.');
      }
      await refreshTtsProviderStatus();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to run TTS test.');
    } finally {
      setTestingTts(false);
    }
  };

  const syncJourneyContent = async () => {
    setSyncingJourneyContent(true);
    setError('');
    setMessage('');
    setSyncResult(null);

    try {
      const payload = {
        cloud_provider: syncForm.cloud_provider || null,
        experience_level: syncForm.experience_level || null,
        force_refresh: Boolean(syncForm.force_refresh),
      };
      const started = await apiService.startJourneyContentSync(payload);
      setSyncStatus({ ...started, is_running: true });
      setMessage('Journey content sync started in background.');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to sync journey content.');
    } finally {
      setSyncingJourneyContent(false);
    }
  };

  if (!currentUser?.is_admin) {
    return (
      <div className="mx-auto max-w-4xl px-4 sm:px-6">
        <div className="glass-dark rounded-3xl p-8 border border-red-500/30">
          <h2 className="text-2xl font-bold text-white mb-2">Admin access required</h2>
          <p className="text-slate-300">Your account does not have admin permissions.</p>
          {onBack && (
            <button className="btn btn-secondary mt-6" onClick={onBack}>Back</button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 space-y-6">
      <div className="glass-dark rounded-3xl p-6 sm:p-8 border border-white/10">
        <div className="flex items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-r from-cyan-500 to-teal-600 flex items-center justify-center">
              <FaCog className="text-white" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-white">Admin Console</h1>
              <p className="text-slate-400">Runtime configuration and operational controls</p>
            </div>
          </div>
          <button onClick={loadData} className="btn btn-secondary px-3 py-2">
            <FaSyncAlt className="mr-2" /> Refresh
          </button>
        </div>

        {error && <div className="rounded-xl border border-red-500/40 bg-red-950/40 px-4 py-3 text-red-200 mb-4">{error}</div>}
        {message && <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/40 px-4 py-3 text-emerald-200 mb-4">{message}</div>}

        {loading || !overview || !config ? (
          <p className="text-slate-400">Loading admin data...</p>
        ) : (
          <>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
              <div className="rounded-2xl bg-slate-900/60 border border-white/10 p-4">
                <p className="text-slate-400 text-xs">Users</p>
                <p className="text-2xl font-bold text-white">{overview.total_users}</p>
              </div>
              <div className="rounded-2xl bg-slate-900/60 border border-white/10 p-4">
                <p className="text-slate-400 text-xs">Active Sessions</p>
                <p className="text-2xl font-bold text-white">{overview.active_sessions}</p>
              </div>
              <div className="rounded-2xl bg-slate-900/60 border border-white/10 p-4">
                <p className="text-slate-400 text-xs">Completed Sessions</p>
                <p className="text-2xl font-bold text-white">{overview.completed_sessions}</p>
              </div>
              <div className="rounded-2xl bg-slate-900/60 border border-white/10 p-4">
                <p className="text-slate-400 text-xs">TTS Cache Hit Rate</p>
                <p className="text-2xl font-bold text-white">{(overview.tts_cache.hit_rate * 100).toFixed(1)}%</p>
              </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              <div className="rounded-2xl bg-slate-900/60 border border-white/10 p-5 space-y-4">
                <h2 className="text-lg font-semibold text-white">Interview Engine</h2>
                <label className="block">
                  <span className="text-sm text-slate-300">Max Question Count</span>
                  <input
                    type="number"
                    className="input-base mt-1 px-3 py-2"
                    value={config.max_question_count}
                    onChange={(e) => updateField('max_question_count', e.target.value)}
                  />
                </label>
                <label className="block">
                  <span className="text-sm text-slate-300">Session Timeout (seconds)</span>
                  <input
                    type="number"
                    className="input-base mt-1 px-3 py-2"
                    value={config.session_timeout}
                    onChange={(e) => updateField('session_timeout', e.target.value)}
                  />
                </label>
              </div>

              <div className="rounded-2xl bg-slate-900/60 border border-white/10 p-5 space-y-4">
                <h2 className="text-lg font-semibold text-white">TTS Runtime Settings</h2>
                {ttsProviderStatus && (
                  <div className={`rounded-xl border px-3 py-2 text-sm ${ttsProviderStatus.available ? 'border-emerald-500/40 bg-emerald-950/30 text-emerald-200' : 'border-amber-500/40 bg-amber-950/30 text-amber-200'}`}>
                    <div>
                      Provider status: <span className="font-semibold">{ttsProviderStatus.available ? 'Ready' : 'Unavailable'}</span>
                    </div>
                    {!ttsProviderStatus.available && (
                      <div className="mt-1">Reason: {ttsProviderStatus.availability_reason || 'unknown_reason'}</div>
                    )}
                  </div>
                )}
                <label className="block">
                  <span className="text-sm text-slate-300">Default Voice ID</span>
                  <input
                    className="input-base mt-1 px-3 py-2"
                    value={config.tts_default_voice_id}
                    onChange={(e) => updateField('tts_default_voice_id', e.target.value)}
                  />
                </label>
                <label className="block">
                  <span className="text-sm text-slate-300">Model ID</span>
                  <input
                    className="input-base mt-1 px-3 py-2"
                    value={config.tts_model_id}
                    onChange={(e) => updateField('tts_model_id', e.target.value)}
                  />
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <label className="block">
                    <span className="text-sm text-slate-300">Stability</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      className="input-base mt-1 px-3 py-2"
                      value={config.tts_stability}
                      onChange={(e) => updateField('tts_stability', e.target.value)}
                    />
                  </label>
                  <label className="block">
                    <span className="text-sm text-slate-300">Similarity</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      className="input-base mt-1 px-3 py-2"
                      value={config.tts_similarity}
                      onChange={(e) => updateField('tts_similarity', e.target.value)}
                    />
                  </label>
                </div>

                <div className="flex flex-wrap gap-3">
                  <button onClick={refreshTtsProviderStatus} className="btn btn-secondary px-4 py-2">
                    <FaSyncAlt className="mr-2" /> Check Provider
                  </button>
                  <button onClick={runTtsTest} disabled={testingTts} className="btn btn-secondary px-4 py-2">
                    <FaVolumeMute className="mr-2" /> {testingTts ? 'Testing...' : 'Test TTS'}
                  </button>
                </div>
              </div>

              <div className="rounded-2xl bg-slate-900/60 border border-white/10 p-5 space-y-4 lg:col-span-2">
                <div className="flex items-center gap-2">
                  <FaDatabase className="text-cyan-300" />
                  <h2 className="text-lg font-semibold text-white">TTS Cache Control</h2>
                </div>

                <div className="grid sm:grid-cols-3 gap-3">
                  <label className="block">
                    <span className="text-sm text-slate-300">TTL (seconds)</span>
                    <input
                      type="number"
                      className="input-base mt-1 px-3 py-2"
                      value={config.tts_cache_ttl_seconds}
                      onChange={(e) => updateField('tts_cache_ttl_seconds', e.target.value)}
                    />
                  </label>
                  <label className="block">
                    <span className="text-sm text-slate-300">Max Files</span>
                    <input
                      type="number"
                      className="input-base mt-1 px-3 py-2"
                      value={config.tts_cache_max_files}
                      onChange={(e) => updateField('tts_cache_max_files', e.target.value)}
                    />
                  </label>
                  <label className="flex items-center gap-2 mt-7">
                    <input
                      type="checkbox"
                      checked={Boolean(config.tts_cache_enabled)}
                      onChange={(e) => updateField('tts_cache_enabled', e.target.checked)}
                    />
                    <span className="text-sm text-slate-300">Cache Enabled</span>
                  </label>
                </div>

                <div className="grid sm:grid-cols-4 gap-3 text-sm">
                  <div className="rounded-xl bg-slate-800/60 border border-white/10 px-3 py-2 text-slate-300">Files: <span className="text-white font-semibold">{overview.tts_cache.file_count}</span></div>
                  <div className="rounded-xl bg-slate-800/60 border border-white/10 px-3 py-2 text-slate-300">Size: <span className="text-white font-semibold">{Math.round((overview.tts_cache.size_bytes || 0) / 1024)} KB</span></div>
                  <div className="rounded-xl bg-slate-800/60 border border-white/10 px-3 py-2 text-slate-300">Hits/Misses: <span className="text-white font-semibold">{overview.tts_cache.hits}/{overview.tts_cache.misses}</span></div>
                  <div className="rounded-xl bg-slate-800/60 border border-white/10 px-3 py-2 text-slate-300">Evictions: <span className="text-white font-semibold">{overview.tts_cache.evictions}</span></div>
                </div>

                <button onClick={clearCache} className="btn btn-danger px-4 py-2">
                  <FaTrash className="mr-2" /> Clear TTS Cache
                </button>
              </div>

              <div className="rounded-2xl bg-slate-900/60 border border-white/10 p-5 space-y-4 lg:col-span-2">
                <div className="flex items-center gap-2">
                  <FaDatabase className="text-cyan-300" />
                  <h2 className="text-lg font-semibold text-white">Journey Content Sync</h2>
                </div>
                <p className="text-sm text-slate-300">Preload or refresh in-app cloud lesson content cache.</p>

                <div className="grid sm:grid-cols-3 gap-3">
                  <label className="block">
                    <span className="text-sm text-slate-300">Cloud Provider</span>
                    <select
                      className="select-base mt-1 px-3 py-2"
                      value={syncForm.cloud_provider}
                      onChange={(e) => setSyncForm((prev) => ({ ...prev, cloud_provider: e.target.value }))}
                    >
                      <option value="">All providers</option>
                      <option value="aws">AWS</option>
                      <option value="azure">Azure</option>
                      <option value="gcp">GCP</option>
                    </select>
                  </label>

                  <label className="block">
                    <span className="text-sm text-slate-300">Experience Level</span>
                    <select
                      className="select-base mt-1 px-3 py-2"
                      value={syncForm.experience_level}
                      onChange={(e) => setSyncForm((prev) => ({ ...prev, experience_level: e.target.value }))}
                    >
                      <option value="">All levels</option>
                      <option value="junior">Junior</option>
                      <option value="mid">Mid</option>
                      <option value="senior">Senior</option>
                      <option value="expert">Expert</option>
                    </select>
                  </label>

                  <label className="flex items-center gap-2 mt-7">
                    <input
                      type="checkbox"
                      checked={Boolean(syncForm.force_refresh)}
                      onChange={(e) => setSyncForm((prev) => ({ ...prev, force_refresh: e.target.checked }))}
                    />
                    <span className="text-sm text-slate-300">Force refresh</span>
                  </label>
                </div>

                <button onClick={syncJourneyContent} disabled={syncingJourneyContent} className="btn btn-secondary px-4 py-2">
                  <FaSyncAlt className="mr-2" /> {syncingJourneyContent ? 'Starting...' : 'Start Background Sync'}
                </button>

                {syncStatus && (
                  <div className="rounded-xl bg-slate-800/60 border border-white/10 p-4 space-y-2 text-sm">
                    <div className="text-slate-300">Status: <span className="text-white font-semibold uppercase">{syncStatus.status || 'idle'}</span></div>
                    <div className="text-slate-300">Running: <span className="text-white font-semibold">{syncStatus.is_running ? 'Yes' : 'No'}</span></div>
                    {!!syncStatus?.run_id && <div className="text-slate-300">Run ID: <span className="text-white font-semibold">{syncStatus.run_id}</span></div>}
                    {!!syncStatus?.duration_seconds && <div className="text-slate-300">Duration: <span className="text-white font-semibold">{syncStatus.duration_seconds}s</span></div>}
                  </div>
                )}

                {syncResult && (
                  <div className="rounded-xl bg-slate-800/60 border border-white/10 p-4 space-y-2 text-sm">
                    <div className="text-slate-300">Synced: <span className="text-white font-semibold">{syncResult.synced_modules}</span></div>
                    <div className="text-slate-300">Reused: <span className="text-white font-semibold">{syncResult.reused_modules}</span></div>
                    <div className="text-slate-300">Failed: <span className="text-white font-semibold">{syncResult.failed_modules}</span></div>
                    {!!syncResult?.errors?.length && (
                      <div className="text-red-300">Errors: {syncResult.errors.slice(0, 3).join(' | ')}</div>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button onClick={saveConfig} disabled={saving} className="btn btn-primary px-4 py-2">
                <FaSave className="mr-2" /> {saving ? 'Saving...' : 'Save Config'}
              </button>
              {onBack && <button onClick={onBack} className="btn btn-secondary px-4 py-2">Back</button>}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
