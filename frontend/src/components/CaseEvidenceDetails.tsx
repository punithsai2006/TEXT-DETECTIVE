import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useCase } from '../context/CaseContext';
import { SourceCitation } from './SourceCitation';
import { API_BASE } from '../services/api';

type Claim = { claim_id: string; subject: string; predicate: string; object: string; speaker: string | null;
  polarity: string; attribution: string; source_span_ids: string[]; uncertainty: string[] };
type Run = { run_id: string; status: string; stale: boolean; is_mock: boolean; model: string;
  claims: Claim[]; failures: string[]; actions: Record<string, unknown>[]; review_history: Record<string, unknown>[] };

export const CaseEvidenceDetails: React.FC<{ section: 'status' | 'claims' | 'actions'; fallback?: React.ReactNode }> = ({ section, fallback }) => {
  const { activeCaseId } = useCase();
  return <Details key={`${activeCaseId}-${section}`} section={section} fallback={fallback} />;
};

const Details: React.FC<{ section: 'status' | 'claims' | 'actions'; fallback?: React.ReactNode }> = ({ section, fallback }) => {
  const { activeCaseId, activeCase, refreshCases } = useCase();
  const location = useLocation();
  const [run, setRun] = useState<Run | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState('');
  const [correction, setCorrection] = useState<{ id: string; text: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const base = `${API_BASE}/cases/${activeCaseId}/evidence-review`;
  useEffect(() => {
    let current = true;
    if (!activeCaseId) { setLoaded(true); return; }
    fetch(base).then(async response => {
      if (!response.ok) throw new Error('Unable to load evidence analysis');
      const data = await response.json();
      if (current) { setRun(data.run); setError(''); }
    }).catch(e => { if (current) setError(e.message); }).finally(() => { if (current) setLoaded(true); });
    return () => { current = false; };
  }, [activeCaseId, activeCase?.updated_at, location.pathname]);
  if (!loaded) return section === 'status' ? null : <p className="text-sm text-slate-500">Loading evidence records…</p>;
  if (!run) return error ? <p role="alert" className="text-red-700 text-sm">{error}</p> : <>{fallback}</>;
  if (section === 'status') return <div className="mb-4 rounded-xl border border-slate-200 bg-white p-3 text-xs space-y-1">
    <p className="font-semibold">{run.is_mock ? 'FIXTURE/MOCK — scripted outputs' : run.model} · {run.status}{run.stale ? ' · STALE' : ''}</p>
    {run.failures.map((failure, i) => <p key={i} className="text-red-700">{failure}</p>)}
    {run.stale && <p className="text-amber-800">Sources or corrections changed. Previous findings and approvals are stale. <Link to="/new" className="underline">Rerun the investigation.</Link></p>}
    <p className="text-slate-600">Source claims and accepted leads require human review; processing completion does not establish actual events.</p>
  </div>;
  if (section === 'actions') return <section className="case-card p-5 rounded-xl space-y-4">
    <h1 className="text-xl font-bold">Agent Activity & Review History</h1>
    <p className="text-sm text-slate-600">Evidence retrieval, contradiction, hypothesis investigation, and verification/reporting roles. Recorded tool actions and evidence references; no private reasoning or automatic verdict.</p>
    {run.actions.map((action, i) => <article key={i} className="border rounded-lg p-3 text-xs space-y-2">
      <p className="font-semibold">{String(action.role)} · {String(action.tool)} · {String(action.status || action.action || 'executed')}</p>
      {action.query != null && <p>Search: {String(action.query)}</p>}
      {action.reason != null && <p>{String(action.reason)}</p>}
      {((action.source_span_ids || []) as string[]).map(id => <div key={id}><SourceCitation spanId={id} /></div>)}
    </article>)}
    <details><summary className="cursor-pointer font-semibold">Append-only review history</summary><pre className="text-xs whitespace-pre-wrap break-all">{JSON.stringify(run.review_history, null, 2)}</pre></details>
  </section>;
  const save = async () => {
    if (!correction) return;
    setSaving(true); setError('');
    try {
      const response = await fetch(`${base}/runs/${run.run_id}/reviews/${correction.id}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'correct_claim', reviewer: 'local_reviewer', notes: 'Versioned correction from Documents', correction: JSON.parse(correction.text) }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Correction failed');
      setRun({ ...run, stale: true }); setCorrection(null); await refreshCases();
    } catch (e) { setError(e instanceof Error ? e.message : 'Correction failed'); }
    finally { setSaving(false); }
  };
  return <section className="case-card p-5 rounded-xl space-y-3">
    <h2 className="text-base font-bold">Attributed claims & source provenance</h2>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {run.claims.map(claim => <article key={claim.claim_id} className="border-t pt-3 text-sm space-y-1">
      <p><strong>{claim.speaker || 'Source'} reports:</strong> {claim.subject} / {claim.predicate} / {claim.object}</p>
      <p className="text-xs text-slate-500">{claim.polarity} · {claim.attribution} · {claim.uncertainty.join('; ') || 'Human review required'}</p>
      {claim.source_span_ids.map(id => <div key={id}><SourceCitation spanId={id} /></div>)}
      <button disabled={run.stale} className="text-xs underline disabled:opacity-40" onClick={() => setCorrection({ id: claim.claim_id, text: JSON.stringify(claim, null, 2) })}>Correct extracted information</button>
    </article>)}
    {correction && <div className="space-y-2"><label className="block">Versioned claim correction<textarea className="w-full h-64 border p-3 font-mono text-xs" value={correction.text} onChange={e => setCorrection({ ...correction, text: e.target.value })} /></label>
      <button disabled={saving || run.stale} onClick={save} className="bg-slate-900 text-white px-3 py-2 rounded-lg">Save correction</button>
    </div>}
  </section>;
};
