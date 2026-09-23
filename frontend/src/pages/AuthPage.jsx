import React, { useState } from 'react';
import { HeartHandshake, LogIn, UserPlus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function AuthPage() {
  const { login, signup } = useAuth();
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('caregiver');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    setNotice('');
    try {
      if (mode === 'login') {
        await login(email.trim(), password);
      } else {
        await signup({ email: email.trim(), password, full_name: fullName.trim(), role });
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Authentication failed. Please try again.';
      if (err?.response?.status === 202) setNotice(msg);
      else setError(typeof msg === 'string' ? msg : 'Authentication failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#f5f2ff] to-[#f8f4e9] p-4">
      <div className="w-full max-w-md bg-white rounded-3xl border border-[#e5dfd4] shadow-xl p-8">
        <div className="text-center mb-6">
          <div className="w-14 h-14 rounded-2xl bg-[#4943a5] text-white flex items-center justify-center text-2xl mx-auto shadow-md">
            ♡
          </div>
          <h1 className="text-3xl font-bold font-serif mt-3">MEMORA</h1>
          <p className="text-xs tracking-[3px] text-[#68738a] font-semibold">TOGETHER, EACH DAY</p>
        </div>

        <div className="grid grid-cols-2 gap-2 bg-[#faf8f2] p-1.5 rounded-2xl border border-[#e8e2d5] mb-6">
          {['login', 'signup'].map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`py-2.5 rounded-xl text-sm font-bold transition ${
                mode === m ? 'bg-[#4943a5] text-white shadow' : 'text-[#68738a]'
              }`}
            >
              {m === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="space-y-4">
          {mode === 'signup' && (
            <div>
              <label className="block text-xs font-bold uppercase text-[#273047] mb-1">Full name</label>
              <input
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="E.g., Anitha"
                className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm outline-none focus:border-[#4943a5]"
              />
            </div>
          )}
          <div>
            <label className="block text-xs font-bold uppercase text-[#273047] mb-1">Email</label>
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm outline-none focus:border-[#4943a5]"
            />
          </div>
          <div>
            <label className="block text-xs font-bold uppercase text-[#273047] mb-1">Password</label>
            <input
              required
              type="password"
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 6 characters"
              className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm outline-none focus:border-[#4943a5]"
            />
          </div>
          {mode === 'signup' && (
            <div>
              <label className="block text-xs font-bold uppercase text-[#273047] mb-1">I am a</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm outline-none focus:border-[#4943a5]"
              >
                <option value="caregiver">Caregiver / Caretaker</option>
                <option value="patient">Patient</option>
              </select>
              <p className="text-[11px] text-gray-500 mt-1">Doctor and admin accounts are created by an admin.</p>
            </div>
          )}

          {error && <div className="text-sm text-red-700 bg-red-50 p-3 rounded-xl font-medium">{error}</div>}
          {notice && <div className="text-sm text-emerald-800 bg-emerald-50 p-3 rounded-xl font-medium">{notice}</div>}

          <button
            type="submit"
            disabled={busy}
            className="w-full py-3.5 bg-[#4943a5] text-white rounded-2xl font-bold hover:bg-[#3d378f] transition disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {mode === 'login' ? <LogIn className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
            <span>{busy ? 'Please wait…' : mode === 'login' ? 'Sign In to MEMORA' : 'Create Account'}</span>
          </button>
        </form>

        <div className="mt-6 text-xs text-gray-500 bg-[#faf8f2] border border-[#e8e2d5] rounded-2xl p-4 flex gap-2">
          <HeartHandshake className="w-4 h-4 text-[#4943a5] shrink-0 mt-0.5" />
          <span>
            Demo admin: <b>admin@memora.local</b> / <b>admin123</b> (local demo mode). In Supabase mode, create users in
            Supabase Auth — profiles and roles sync automatically.
          </span>
        </div>
      </div>
    </div>
  );
}
