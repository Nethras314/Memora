import React from 'react';

const DOMAIN_LABELS = {
  memory: 'Memory',
  attention: 'Attention / Executive',
  semantic: 'Semantic / Orientation',
  speed: 'Processing Speed',
  adl: 'Daily Function (ADL)',
  medication: 'Medication Adherence',
  mood: 'Mood / Behaviour',
};

export default function DomainBreakdown({ data }) {
  const rows = (data || []).filter((d) => d.score != null);
  if (!rows.length) {
    return <div className="text-sm text-gray-400 py-6 text-center">No domain data yet.</div>;
  }

  return (
    <div className="space-y-3">
      {rows.map((d) => (
        <div key={d.domain}>
          <div className="flex justify-between items-baseline text-xs mb-1">
            <span className="font-semibold text-[#273047]">{DOMAIN_LABELS[d.domain] || d.domain}</span>
            <span className="text-[#68738a]">
              {d.score}/100 · {Math.round((d.weight || 0) * 100)}% weight
            </span>
          </div>
          <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
            <div
              className="h-2 rounded-full bg-[#4943a5] transition-all"
              style={{ width: `${Math.max(0, Math.min(100, d.score))}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
