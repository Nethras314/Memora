import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export default function TrendChart({ data }) {
  const chartData = (data || []).map((p) => ({
    date: p.date ? p.date.slice(5) : p.date,
    index: p.index,
    score: p.score,
    latencySec: p.latency_ms != null ? +(p.latency_ms / 1000).toFixed(1) : null,
  }));

  if (!chartData.length) {
    return <div className="text-sm text-gray-400 py-8 text-center">No session data yet.</div>;
  }

  return (
    <div style={{ width: '100%', height: 280 }}>
      <ResponsiveContainer>
        <LineChart data={chartData} margin={{ top: 8, right: 4, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5dfd4" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#68738a' }} />
          <YAxis yAxisId="left" domain={[0, 100]} tick={{ fontSize: 11, fill: '#68738a' }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11, fill: '#68738a' }} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line yAxisId="left" type="monotone" dataKey="index" name="Stability Index" stroke="#4943a5" strokeWidth={2} dot={false} />
          <Line yAxisId="left" type="monotone" dataKey="score" name="Session Score" stroke="#08b77b" strokeWidth={1.5} dot={false} />
          <Line yAxisId="right" type="monotone" dataKey="latencySec" name="Latency (s)" stroke="#f3b642" strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
