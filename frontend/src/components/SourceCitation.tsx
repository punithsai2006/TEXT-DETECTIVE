import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { useCase } from '../context/CaseContext';

type Span = { filename: string; quote: string; page_number: number | null; paragraph: number;
  char_start: number; char_end: number; raw_text: string; extraction_version: string; original_url: string };

export const SourceCitation: React.FC<{ spanId?: string; label?: string }> = ({ spanId, label = 'Inspect exact source' }) => {
  const { activeCaseId } = useCase();
  const [open, setOpen] = useState(false);
  const [span, setSpan] = useState<Span | null>(null);
  const [error, setError] = useState('');
  if (!spanId?.startsWith('sp_') || !activeCaseId) return null;
  const load = async (event: React.MouseEvent) => {
    event.stopPropagation(); setOpen(true); setSpan(null); setError('');
    try {
      const response = await fetch(`/api/cases/${activeCaseId}/evidence-review/sources/${encodeURIComponent(spanId)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Source unavailable');
      setSpan(data);
    } catch (e) { setError(e instanceof Error ? e.message : 'Source unavailable'); }
  };
  return <>
    <button type="button" onClick={load} className="text-blue-600 underline text-xs font-medium">{label}</button>
    {open && createPortal(<div role="dialog" aria-modal="true" aria-label="Exact source passage" className="fixed inset-0 z-[100] bg-slate-950/50 flex items-center justify-center p-5" onClick={event => event.stopPropagation()}>
      <section className="bg-white text-slate-900 rounded-xl p-5 max-w-3xl w-full max-h-[85vh] overflow-auto space-y-3 shadow-xl">
        <div className="flex justify-between gap-4"><h2 className="text-lg font-bold">Exact source passage</h2><button onClick={() => setOpen(false)} className="underline">Close source</button></div>
        {error && <p role="alert" className="text-red-700">{error}</p>}
        {!span && !error && <p>Loading source…</p>}
        {span && <>
          <p className="font-semibold">{span.filename}{span.page_number ? ` · PDF page ${span.page_number}` : ''} · extracted paragraph {span.paragraph}</p>
          <blockquote className="whitespace-pre-wrap border-l-4 border-blue-600 pl-3">{span.quote}</blockquote>
          <p className="text-xs text-slate-600">Extracted-text characters [{span.char_start}, {span.char_end}); version {span.extraction_version}. Locator and quotation checked; semantic support requires review.</p>
          <a href={span.original_url} className="text-blue-700 underline">Download original evidence</a>
          <details><summary className="cursor-pointer">Surrounding extracted text</summary><pre className="whitespace-pre-wrap text-xs bg-slate-50 p-3 max-h-72 overflow-auto">
            {Array.from(span.raw_text).slice(0, span.char_start).join('')}<mark>{span.quote}</mark>{Array.from(span.raw_text).slice(span.char_end).join('')}
          </pre></details>
        </>}
      </section>
    </div>, document.body)}
  </>;
};
