import React, { useState, useEffect } from 'react';
import { HeartHandshake, User, TrendingUp, TrendingDown, Minus, CheckCircle } from 'lucide-react';
import { api } from '../services/api';
import { tCaregiver } from '../i18n';
import StatusBadge from '../components/StatusBadge';
import MoodLog from '../components/MoodLog';

const STATUS_LABEL = { green: 'stable', amber: 'watch', red: 'needsAttention' };

function DeltaArrow({ value }) {
  if (value == null) return <Minus className="w-5 h-5 text-gray-400" />;
  if (value > 0) return <TrendingUp className="w-5 h-5 text-emerald-600" />;
  if (value < 0) return <TrendingDown className="w-5 h-5 text-red-500" />;
  return <Minus className="w-5 h-5 text-gray-400" />;
}

export default function CaregiverDashboard({ patients, currentPatient, onSelectPatient, language = 'en-IN' }) {
  const [glance, setGlance] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      setGlance(await api.getCaregiverGlance(currentPatient?.id || 1));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [currentPatient]);

  const status = glance?.status || 'amber';
  const flagKey = status === 'red' ? 'flagRed' : status === 'amber' ? 'flagAmber' : 'flagGreen';
  const actionKey = status === 'red' ? 'actionRed' : status === 'amber' ? 'actionAmber' : 'actionGreen';

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-serif text-[#273047] flex items-center gap-3">
            <HeartHandshake className="w-8 h-8 text-[#4943a5]" /> {tCaregiver(language, 'caregiverToday')}
          </h1>
          <p className="text-sm text-[#68738a] mt-1">{tCaregiver(language, 'caregiverSub')}</p>
        </div>

        <div className="flex items-center gap-2 bg-white p-2 rounded-2xl border border-[#e5dfd4] shadow-sm">
          <User className="w-5 h-5 text-[#4943a5] ml-2" />
          <span className="text-xs font-bold text-gray-400 uppercase">Patient:</span>
          {(patients || []).length > 0 ? (
            <select
              value={currentPatient?.id}
              onChange={(e) => onSelectPatient(Number(e.target.value))}
              className="bg-transparent font-bold text-sm text-[#273047] outline-none cursor-pointer pr-4"
            >
              {patients.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          ) : (
            <span className="text-xs font-semibold text-gray-500 pr-2">No patients assigned</span>
          )}
        </div>
      </div>

      {loading ? (
        <div className="text-sm text-gray-500">Loading…</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Stability Index card */}
          <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#68738a]">
                {tCaregiver(language, 'stabilityIndex')}
              </span>
              <StatusBadge status={status} label={tCaregiver(language, STATUS_LABEL[status])} />
            </div>
            <div className="flex items-end gap-3 mt-4 mb-1">
              <div className="text-5xl font-extrabold text-[#4943a5]">{glance?.index ?? '—'}</div>
              <div className="text-sm text-gray-400 mb-2">/100</div>
              <div className="ml-auto flex items-center gap-1 text-xs font-semibold text-[#68738a] mb-2">
                <DeltaArrow value={glance?.index_delta} />
                {glance?.index_delta != null ? `${glance.index_delta > 0 ? '+' : ''}${glance.index_delta}` : '—'}
              </div>
            </div>
            <p className="text-xs text-[#68738a] mt-4 leading-relaxed">{tCaregiver(language, flagKey)}</p>
          </div>

          {/* Routine adherence card */}
          <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#68738a]">
                {tCaregiver(language, 'routineAdherence')}
              </span>
              <CheckCircle className="w-5 h-5 text-emerald-600" />
            </div>
            <div className="text-5xl font-extrabold text-[#273047] mt-4 mb-2">{glance?.routine_pct ?? 0}%</div>
            <div className="w-full bg-gray-200 h-2.5 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-2.5 rounded-full transition-all" style={{ width: `${glance?.routine_pct || 0}%` }} />
            </div>
            <p className="text-xs text-[#68738a] mt-4 leading-relaxed">{tCaregiver(language, actionKey)}</p>
          </div>

          {/* 7-day sparkline */}
          <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm flex flex-col justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#68738a]">7 days</span>
            <div className="flex items-end gap-2 h-28 mt-3">
              {(glance?.trend || []).map((p, i) => (
                <div key={i} className="flex-1 flex flex-col items-center justify-end h-full">
                  <div
                    className="w-full rounded-t-md bg-[#4943a5]/80"
                    style={{ height: `${Math.max(4, Math.min(100, p.index ?? 40))}%` }}
                    title={`${p.date}: ${p.index ?? '—'}`}
                  />
                  <span className="text-[10px] text-[#68738a] mt-1">{p.date?.slice(5)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Mood quick-log */}
      <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
        <h2 className="text-lg font-bold font-serif text-[#273047] mb-1">How are they today?</h2>
        <p className="text-xs text-[#68738a] mb-4">A 5-second check-in helps spot changes early.</p>
        <MoodLog patientId={currentPatient?.id || 1} onSaved={load} />
      </div>
    </div>
  );
}
