import React, { useState, useEffect } from 'react';
import {
  Stethoscope,
  User,
  FileDown,
  ClipboardList,
  ShieldCheck,
  Activity,
  Calendar,
} from 'lucide-react';
import { api } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import TrendChart from '../components/TrendChart';
import DomainBreakdown from '../components/DomainBreakdown';
import PrintableReport from '../components/PrintableReport';

const WINDOWS = [30, 90, 180];

export default function DoctorDashboard({ patients, currentPatient, onSelectPatient, role = 'doctor' }) {
  const [summary, setSummary] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [trend, setTrend] = useState([]);
  const [windowDays, setWindowDays] = useState(30);
  const [notes, setNotes] = useState([]);
  const [moods, setMoods] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [grants, setGrants] = useState([]);
  const [newNote, setNewNote] = useState({ note_type: 'assessment', body: '' });
  const [grantForm, setGrantForm] = useState({ doctor_id: '', reason: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const isAdmin = role === 'admin';

  const loadSummary = async () => {
    try {
      setSummary(await api.getCaregiverSummary());
    } catch (e) {
      setError(e?.response?.data?.detail || 'Could not load patient summary.');
    } finally {
      setLoading(false);
    }
  };

  const loadDetail = async (id) => {
    if (!id) return;
    setError('');
    try {
      const [a, t, n, m] = await Promise.all([
        api.getCaregiverAnalytics(id),
        api.getCaregiverTrend(id, windowDays),
        api.getClinicalNotes(id),
        api.getMoodLogs(id),
      ]);
      setAnalytics(a);
      setTrend(t);
      setNotes(n);
      setMoods(m);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Could not load patient detail.');
    }
  };

  const loadGrants = async (id) => {
    if (!isAdmin) return;
    try {
      const [all, docs] = await Promise.all([api.listGrants(), api.listDoctors()]);
      setGrants(all.filter((g) => g.patient_id === id && g.status === 'active'));
      setDoctors(docs);
    } catch {
      /* non-critical */
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  useEffect(() => {
    if (selectedId) {
      loadDetail(selectedId);
      loadGrants(selectedId);
    }
  }, [selectedId]);

  useEffect(() => {
    if (selectedId) loadDetail(selectedId);
  }, [windowDays]);

  const selectPatient = (id) => {
    setSelectedId(id);
    const p = (patients || []).find((x) => x.id === id);
    if (p && onSelectPatient) onSelectPatient(id);
  };

  const addNote = async () => {
    if (!newNote.body.trim()) return;
    try {
      await api.createClinicalNote({ patient_id: selectedId, note_type: newNote.note_type, body: newNote.body });
      setNewNote({ note_type: 'assessment', body: '' });
      setNotes(await api.getClinicalNotes(selectedId));
    } catch {
      /* handled by UI state */
    }
  };

  const grant = async () => {
    if (!grantForm.doctor_id) return;
    try {
      await api.grantAccess({ patient_id: selectedId, doctor_id: grantForm.doctor_id, reason: grantForm.reason || null });
      setGrantForm({ doctor_id: '', reason: '' });
      loadGrants(selectedId);
    } catch {
      /* handled by UI state */
    }
  };

  const revoke = async (grantId) => {
    try {
      await api.revokeAccess(grantId);
      loadGrants(selectedId);
    } catch {
      /* handled by UI state */
    }
  };

  const sel = summary.find((s) => s.patient_id === selectedId) || null;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-serif text-[#273047] flex items-center gap-3">
            <Stethoscope className="w-8 h-8 text-[#4943a5]" /> Clinical Portal
          </h1>
          <p className="text-sm text-[#68738a] mt-1">
            Longitudinal cognitive tracking across your patients, sorted by decline velocity.
          </p>
        </div>
        {selectedId && (
          <div className="flex gap-2">
            <button
              onClick={() => api.exportAnalyticsCsv(selectedId)}
              className="px-4 py-2 rounded-2xl bg-[#4943a5] text-white text-sm font-bold hover:bg-[#3d378f] flex items-center gap-2"
            >
              <FileDown className="w-4 h-4" /> Export CSV
            </button>
            <PrintableReport patient={analytics || {}} analytics={analytics} notes={notes} />
          </div>
        )}
      </div>

      {error && (
        <div className="text-sm text-amber-800 bg-amber-50 border border-amber-200 p-4 rounded-2xl">{error}</div>
      )}

      {/* Cohort table */}
      <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm overflow-x-auto">
        <h2 className="text-xl font-bold font-serif text-[#273047] mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-[#4943a5]" /> Patients ({summary.length})
        </h2>
        {loading ? (
          <div className="text-sm text-gray-500">Loading…</div>
        ) : summary.length === 0 ? (
          <div className="text-sm text-gray-400 py-6 text-center">
            No patients granted to you yet. Ask a caregiver or admin to grant access.
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[#e5dfd4] text-[#68738a] text-xs uppercase">
                <th className="pb-3 font-bold">Patient</th>
                <th className="pb-3 font-bold">Age</th>
                <th className="pb-3 font-bold">Index</th>
                <th className="pb-3 font-bold">Δ/week</th>
                <th className="pb-3 font-bold">Status</th>
                <th className="pb-3 font-bold">Last visit</th>
                <th className="pb-3 font-bold">Since visit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f0ebe0]">
              {summary.map((s) => (
                <tr
                  key={s.patient_id}
                  onClick={() => selectPatient(s.patient_id)}
                  className={`cursor-pointer hover:bg-[#faf8f2] transition ${selectedId === s.patient_id ? 'bg-indigo-50/50' : ''}`}
                >
                  <td className="py-3 font-semibold text-[#273047]">{s.patient_name}</td>
                  <td className="py-3 text-[#546077]">{s.age ?? '—'}</td>
                  <td className="py-3 font-bold text-[#273047]">{s.index ?? '—'}</td>
                  <td className={`py-3 font-semibold ${s.delta_per_week == null ? 'text-gray-400' : s.delta_per_week < 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                    {s.delta_per_week ?? '—'}
                  </td>
                  <td className="py-3"><StatusBadge status={s.status} /></td>
                  <td className="py-3 text-[#546077]">
                    {s.last_visit ? new Date(s.last_visit).toLocaleDateString() : '—'}
                  </td>
                  <td className="py-3 text-[#546077]">{s.sessions_since_visit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Patient detail */}
      {selectedId && analytics && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              { label: 'Cognitive Stability Index', value: analytics.index ?? '—', sub: '/100' },
              { label: 'Δ vs prior week', value: analytics.index_delta ?? '—', sub: 'pts' },
              { label: 'Routine adherence', value: `${analytics.routine_completion_pct ?? 0}%`, sub: '' },
              { label: 'Medication adherence', value: `${analytics.medication_adherence_pct ?? '—'}%`, sub: '' },
            ].map((k) => (
              <div key={k.label} className="bg-[#fffefb] p-5 rounded-3xl border border-[#e5dfd4] shadow-sm">
                <div className="text-xs font-bold uppercase tracking-wider text-[#68738a]">{k.label}</div>
                <div className="text-3xl font-extrabold text-[#4943a5] mt-2">
                  {k.value} <span className="text-sm text-gray-400 font-semibold">{k.sub}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Trend chart */}
            <div className="md:col-span-8 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold font-serif text-[#273047]">Longitudinal trend</h2>
                <div className="flex gap-1.5">
                  {WINDOWS.map((w) => (
                    <button
                      key={w}
                      onClick={() => setWindowDays(w)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold border ${
                        windowDays === w
                          ? 'bg-[#4943a5] text-white border-[#4943a5]'
                          : 'bg-white text-[#546077] border-[#e5dfd4]'
                      }`}
                    >
                      {w}d
                    </button>
                  ))}
                </div>
              </div>
              <TrendChart data={trend} />
            </div>

            {/* Domain breakdown */}
            <div className="md:col-span-4 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
              <h2 className="text-xl font-bold font-serif text-[#273047] mb-4">Domain breakdown</h2>
              <DomainBreakdown data={analytics.domain_breakdown} />
              <div className="text-[11px] text-gray-400 mt-4 border-t pt-2">
                Composite weights: games 50% · routine 20% · medication 15% · mood 15%.
              </div>
            </div>
          </div>

          {/* Since last visit + session drill-down */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            <div className="md:col-span-4 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
              <h2 className="text-xl font-bold font-serif text-[#273047] mb-3 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-[#4943a5]" /> Since last visit
              </h2>
              <p className="text-sm text-[#546077]">
                {sel?.last_visit ? (
                  <>Last note: <strong>{new Date(sel.last_visit).toLocaleDateString()}</strong></>
                ) : (
                  'No clinical note recorded yet.'
                )}
              </p>
              <p className="text-sm text-[#546077] mt-1">
                Sessions since: <strong>{sel?.sessions_since_visit ?? analytics.recent_sessions_count}</strong>
              </p>
              <p className="text-xs text-[#68738a] mt-3">
                Most recent mood: <strong>{analytics.mood_recent || '—'}</strong>
              </p>
            </div>

            <div className="md:col-span-8 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm overflow-x-auto">
              <h2 className="text-xl font-bold font-serif text-[#273047] mb-4">Recent sessions</h2>
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[#e5dfd4] text-[#68738a] text-xs uppercase">
                    <th className="pb-3 font-bold">Date</th>
                    <th className="pb-3 font-bold">Level</th>
                    <th className="pb-3 font-bold">Latency</th>
                    <th className="pb-3 font-bold">Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f0ebe0]">
                  {analytics.cognitive_trend?.map((r, i) => (
                    <tr key={i}>
                      <td className="py-3 font-semibold text-[#273047]">{r.date}</td>
                      <td className="py-3 text-[#546077]">Level {r.level}</td>
                      <td className="py-3 font-mono text-gray-600">{r.latency_sec}s</td>
                      <td className="py-3 font-bold text-[#273047]">{r.score}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Clinical notes */}
          <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
            <h2 className="text-xl font-bold font-serif text-[#273047] mb-4 flex items-center gap-2">
              <ClipboardList className="w-5 h-5 text-[#4943a5]" /> Clinical notes
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
              <div className="md:col-span-7 space-y-3">
                {notes.length === 0 ? (
                  <div className="text-sm text-gray-400">No notes yet.</div>
                ) : (
                  notes.map((n) => (
                    <div key={n.id} className="border border-[#e5dfd4] rounded-2xl p-4">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] font-bold uppercase tracking-wide text-[#4943a5]">{n.note_type}</span>
                        <span className="text-[11px] text-gray-400">
                          {n.created_at ? new Date(n.created_at).toLocaleString() : ''}
                        </span>
                      </div>
                      <p className="text-sm text-[#273047]">{n.body}</p>
                    </div>
                  ))
                )}
              </div>
              <div className="md:col-span-5 space-y-3">
                <select
                  value={newNote.note_type}
                  onChange={(e) => setNewNote({ ...newNote, note_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
                >
                  <option value="assessment">Assessment</option>
                  <option value="plan">Plan</option>
                  <option value="general">General</option>
                </select>
                <textarea
                  value={newNote.body}
                  onChange={(e) => setNewNote({ ...newNote, body: e.target.value })}
                  placeholder="Write a clinical note…"
                  rows={3}
                  className="w-full px-3 py-2 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
                />
                <button
                  onClick={addNote}
                  disabled={!newNote.body.trim()}
                  className="px-4 py-2 rounded-2xl bg-[#4943a5] text-white text-sm font-bold disabled:opacity-50"
                >
                  Add note
                </button>
              </div>
            </div>
          </div>

          {/* Grants manager (admin only) */}
          {isAdmin && (
            <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
              <h2 className="text-xl font-bold font-serif text-[#273047] mb-4 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-[#4943a5]" /> Doctor access
              </h2>
              <div className="flex flex-wrap gap-4 items-end">
                <select
                  value={grantForm.doctor_id}
                  onChange={(e) => setGrantForm({ ...grantForm, doctor_id: e.target.value })}
                  className="px-3 py-2 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm min-w-[220px]"
                >
                  <option value="">Select doctor…</option>
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>{d.full_name || d.email}</option>
                  ))}
                </select>
                <input
                  value={grantForm.reason}
                  onChange={(e) => setGrantForm({ ...grantForm, reason: e.target.value })}
                  placeholder="Reason (e.g. treating physician)"
                  className="px-3 py-2 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm flex-1 min-w-[200px]"
                />
                <button
                  onClick={grant}
                  disabled={!grantForm.doctor_id}
                  className="px-4 py-2 rounded-2xl bg-[#4943a5] text-white text-sm font-bold disabled:opacity-50"
                >
                  Grant access
                </button>
              </div>
              <div className="mt-4 space-y-2">
                {grants.length === 0 ? (
                  <div className="text-sm text-gray-400">No active doctor grants for this patient.</div>
                ) : (
                  grants.map((g) => (
                    <div key={g.id} className="flex items-center justify-between border border-[#e5dfd4] rounded-2xl px-4 py-2">
                      <span className="text-sm text-[#273047]">
                        Doctor <strong>{g.doctor_id}</strong>{g.reason ? ` · ${g.reason}` : ''}
                      </span>
                      <button onClick={() => revoke(g.id)} className="text-xs font-bold text-red-600 hover:underline">
                        Revoke
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
