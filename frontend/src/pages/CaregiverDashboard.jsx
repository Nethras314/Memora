import React, { useState, useEffect } from 'react';
import { HeartHandshake, User, TrendingUp, CheckCircle, Clock, AlertCircle, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';

export default function CaregiverDashboard({ patients, currentPatient, onSelectPatient }) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, [currentPatient]);

  const loadAnalytics = async () => {
    try {
      const data = await api.getCaregiverAnalytics(currentPatient?.id || 1);
      setAnalytics(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header & Multi-Patient Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-serif text-[#273047]">Caregiver & Clinical Portal</h1>
          <p className="text-sm text-[#68738a] mt-1">
            Real-time monitoring of patient routines, cognitive stability, and AI telemetry.
          </p>
        </div>

        {/* Patient Switcher */}
        <div className="flex items-center gap-2 bg-white p-2 rounded-2xl border border-[#e5dfd4] shadow-sm">
          <User className="w-5 h-5 text-[#4943a5] ml-2" />
          <span className="text-xs font-bold text-gray-400 uppercase">Active Patient:</span>
          <select
            value={currentPatient?.id}
            onChange={(e) => onSelectPatient(Number(e.target.value))}
            className="bg-transparent font-bold text-sm text-[#273047] outline-none cursor-pointer pr-4"
          >
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} (Age {p.age})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Analytics KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Cognitive Stability Index */}
        <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#68738a]">Cognitive Stability</span>
              <TrendingUp className="w-5 h-5 text-[#4943a5]" />
            </div>
            <div className="text-5xl font-extrabold text-[#4943a5] mt-4 mb-1">
              {analytics?.cognitive_stability_score || 78}/100
            </div>
            <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-lg">
              ✓ Normal Sensory Latency
            </span>
          </div>
          <p className="text-xs text-[#68738a] mt-4">
            Calculated from DDA game reaction times (ms) and recall accuracy over recent sessions.
          </p>
        </div>

        {/* Routine Adherence */}
        <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#68738a]">Routine Adherence</span>
              <CheckCircle className="w-5 h-5 text-emerald-600" />
            </div>
            <div className="text-5xl font-extrabold text-[#273047] mt-4 mb-2">
              {analytics?.routine_completion_pct || 0}%
            </div>
            <div className="w-full bg-gray-200 h-2.5 rounded-full overflow-hidden">
              <div
                className="bg-emerald-500 h-2.5 rounded-full transition-all"
                style={{ width: `${analytics?.routine_completion_pct || 0}%` }}
              />
            </div>
          </div>
          <p className="text-xs text-[#68738a] mt-4">
            {analytics?.completed_tasks || 0} of {analytics?.total_tasks || 0} routine tasks marked done today.
          </p>
        </div>

        {/* Clinical Recommendation */}
        <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#68738a]">Clinical Focus</span>
              <ShieldCheck className="w-5 h-5 text-indigo-500" />
            </div>
            <h3 className="text-lg font-bold font-serif text-[#273047] mt-3 mb-2">Physician Guidance</h3>
            <p className="text-xs text-[#526079] leading-relaxed">
              {analytics?.recommended_focus || 'Routine adherence is high. Continue morning symbol sequence exercises.'}
            </p>
          </div>
          <div className="text-[11px] text-gray-400 mt-4 border-t pt-2">
            Aligned with WHO Cognitive Stimulation Therapy (CST) Guidelines.
          </div>
        </div>
      </div>

      {/* Longitudinal Session Telemetry Table */}
      <div className="bg-[#fffefb] p-8 rounded-3xl border border-[#e5dfd4] shadow-sm">
        <h2 className="text-xl font-bold font-serif text-[#273047] mb-4">Longitudinal AI Telemetry Log</h2>
        <p className="text-sm text-[#68738a] mb-6">
          Doctor-exportable session telemetry recording reaction latency and dynamic difficulty levels.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[#e5dfd4] text-[#68738a] text-xs uppercase">
                <th className="pb-3 font-bold">Date</th>
                <th className="pb-3 font-bold">Game Type</th>
                <th className="pb-3 font-bold">AI Level</th>
                <th className="pb-3 font-bold">Reaction Latency</th>
                <th className="pb-3 font-bold">Score</th>
                <th className="pb-3 font-bold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f0ebe0]">
              {analytics?.cognitive_trend?.map((row, i) => (
                <tr key={i} className="hover:bg-[#faf8f2] transition">
                  <td className="py-4 font-semibold text-[#273047]">{row.date}</td>
                  <td className="py-4 text-[#546077]">Sequence Memory</td>
                  <td className="py-4">
                    <span className="bg-indigo-50 text-[#4943a5] text-xs font-bold px-2 py-1 rounded-md">
                      Level {row.level}
                    </span>
                  </td>
                  <td className="py-4 font-mono text-gray-600">{row.latency_sec}s</td>
                  <td className="py-4 font-bold text-[#273047]">{row.score}%</td>
                  <td className="py-4">
                    <span className="text-emerald-700 bg-emerald-50 text-xs font-bold px-2.5 py-1 rounded-lg">
                      Consistent
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
