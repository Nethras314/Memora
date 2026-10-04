import React, { useState } from 'react';
import { api } from '../services/api';

const MOODS = ['Calm', 'Happy', 'Anxious', 'Agitated', 'Confused', 'Sad', 'Irritable'];
const FLAGS = ['sundowning', 'wandering', 'aggression', 'restless', 'tearful'];

export default function MoodLog({ patientId, onSaved }) {
  const [mood, setMood] = useState('Calm');
  const [flags, setFlags] = useState([]);
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  const toggleFlag = (f) =>
    setFlags((prev) => (prev.includes(f) ? prev.filter((x) => x !== f) : [...prev, f]));

  const submit = async () => {
    setBusy(true);
    setMsg('');
    try {
      await api.createMoodLog({ patient_id: patientId, mood, behavior_flags: flags, note: note || null });
      setNote('');
      setFlags([]);
      setMsg('Logged ✓');
      if (onSaved) onSaved();
    } catch (e) {
      setMsg('Could not save.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {MOODS.map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMood(m)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
              mood === m
                ? 'bg-[#4943a5] text-white border-[#4943a5]'
                : 'bg-white text-[#546077] border-[#e5dfd4]'
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        {FLAGS.map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => toggleFlag(f)}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition ${
              flags.includes(f)
                ? 'bg-amber-100 text-amber-800 border-amber-300'
                : 'bg-white text-gray-500 border-[#e5dfd4]'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Optional note…"
        rows={2}
        className="w-full px-3 py-2 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
      />

      <button
        onClick={submit}
        disabled={busy}
        className="px-4 py-2 rounded-2xl bg-[#4943a5] text-white text-sm font-bold disabled:opacity-50 hover:bg-[#3d378f]"
      >
        {busy ? 'Saving…' : 'Log mood'}
      </button>
      {msg && <div className="text-xs text-[#68738a]">{msg}</div>}
    </div>
  );
}
