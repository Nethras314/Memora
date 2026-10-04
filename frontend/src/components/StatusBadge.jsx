import React from 'react';

const MAP = {
  green: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', label: 'Stable' },
  amber: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-400', label: 'Watch' },
  red: { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500', label: 'Needs attention' },
};

export default function StatusBadge({ status, label }) {
  const s = MAP[status] || MAP.amber;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold ${s.bg} ${s.text}`}>
      <span className={`w-2 h-2 rounded-full ${s.dot}`} />
      {label || s.label}
    </span>
  );
}
