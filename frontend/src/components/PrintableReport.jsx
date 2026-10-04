import React from 'react';

const DOMAIN_LABELS = {
  memory: 'Memory', attention: 'Attention', semantic: 'Semantic', speed: 'Processing speed',
  adl: 'Daily function', medication: 'Medication', mood: 'Mood',
};

export default function PrintableReport({ patient, analytics, notes }) {
  const esc = (v) => String(v ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  const print = () => {
    const w = window.open('', '_blank', 'width=820,height=1100');
    if (!w) return;
    const status = analytics?.status || 'amber';
    const breakdown = (analytics?.domain_breakdown || [])
      .filter((d) => d.score != null)
      .map((d) => `<tr><td>${esc(DOMAIN_LABELS[d.domain] || d.domain)}</td><td>${d.score}/100</td><td>${Math.round((d.weight || 0) * 100)}%</td></tr>`)
      .join('');

    const sessions = (analytics?.cognitive_trend || [])
      .map((r) => `<tr><td>${esc(r.date)}</td><td>${esc(r.level)}</td><td>${esc(r.latency_sec)}s</td><td>${esc(r.score)}%</td></tr>`)
      .join('');

    const notesHtml = (notes || [])
      .map((n) => `<li>${esc(n.body)} <span style="color:#888">(${esc(n.note_type)})</span></li>`)
      .join('');

    w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>MEMORA Cognitive Report</title>
      <style>
        body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; color: #273047; margin: 40px; }
        h1 { font-size: 24px; } h2 { font-size: 16px; margin-top: 28px; border-bottom: 1px solid #e5dfd4; padding-bottom: 6px; }
        .muted { color: #68738a; font-size: 13px; }
        .badge { display:inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 700; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
        th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #f0ebe0; }
        th { color: #68738a; text-transform: uppercase; font-size: 11px; }
        ul { font-size: 13px; }
        .note { font-size: 11px; color: #888; margin-top: 40px; }
      </style></head><body>
      <h1>MEMORA Cognitive Report</h1>
      <p class="muted">Patient: <strong>${esc(analytics?.patient_name || patient?.name)}</strong> · Generated ${esc(new Date().toLocaleString())}</p>
      <p><span class="badge" style="background:${status === 'red' ? '#fee2e2' : status === 'amber' ? '#fef3c7' : '#dcfce7'};color:${status === 'red' ? '#b91c1c' : status === 'amber' ? '#b45309' : '#047857'}">${status.toUpperCase()}</span></p>
      <p>Cognitive Stability Index: <strong>${esc(analytics?.index ?? '—')}/100</strong> · Routine adherence: <strong>${esc(analytics?.routine_completion_pct ?? 0)}%</strong> · Medication adherence: <strong>${esc(analytics?.medication_adherence_pct ?? '—')}%</strong></p>
      <h2>Domain breakdown</h2>
      <table><tr><th>Domain</th><th>Score</th><th>Weight</th></tr>${breakdown || '<tr><td colspan="3">No data</td></tr>'}</table>
      <h2>Recent sessions</h2>
      <table><tr><th>Date</th><th>Level</th><th>Latency</th><th>Score</th></tr>${sessions || '<tr><td colspan="4">No sessions</td></tr>'}</table>
      <h2>Clinical notes</h2>
      ${notesHtml ? `<ul>${notesHtml}</ul>` : '<p class="muted">No notes.</p>'}
      <p class="note">MEMORA v2.0 · Longitudinal supportive data — not a medical diagnosis. Review by a qualified clinician recommended.</p>
      </body></html>`);
    w.document.close();
    w.focus();
    setTimeout(() => w.print(), 300);
  };

  return (
    <button
      onClick={print}
      className="px-4 py-2 rounded-2xl bg-white border border-[#e5dfd4] text-sm font-bold text-[#273047] hover:bg-[#f3f0e8]"
    >
      Print / Save PDF
    </button>
  );
}
