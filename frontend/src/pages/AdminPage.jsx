import React, { useEffect, useState } from 'react';
import { ShieldCheck, Users, UserPlus, Activity } from 'lucide-react';
import { api } from '../services/api';

export default function AdminPage() {
  const [users, setUsers] = useState([]);
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'caregiver' });
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const [u, o] = await Promise.all([api.adminListUsers(), api.adminOverview()]);
      setUsers(u);
      setOverview(o);
    } catch (e) {
      setErr(e?.response?.data?.detail || 'Failed to load admin data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const createUser = async (e) => {
    e.preventDefault();
    setMsg('');
    setErr('');
    try {
      await api.adminCreateUser(form);
      setMsg(`Account created for ${form.email} (${form.role}).`);
      setForm({ email: '', password: '', full_name: '', role: 'caregiver' });
      load();
    } catch (ex) {
      setErr(ex?.response?.data?.detail || 'Could not create user.');
    }
  };

  if (loading) return <div className="text-sm text-gray-500">Loading admin portal…</div>;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold font-serif text-[#273047] flex items-center gap-3">
          <ShieldCheck className="w-8 h-8 text-[#4943a5]" /> Admin Portal
        </h1>
        <p className="text-sm text-[#68738a] mt-1">Manage patients, caregivers, doctors and platform usage.</p>
      </div>

      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { label: 'Total Patients', value: overview.total_patients },
            { label: 'Total Users', value: overview.total_users },
            { label: 'Cognitive Sessions', value: overview.total_sessions },
          ].map((k) => (
            <div key={k.label} className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
              <div className="text-xs font-bold uppercase tracking-wider text-[#68738a]">{k.label}</div>
              <div className="text-4xl font-extrabold text-[#4943a5] mt-2">{k.value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="md:col-span-5 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
          <h2 className="text-xl font-bold font-serif mb-4 flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-[#4943a5]" /> Create user
          </h2>
          <form onSubmit={createUser} className="space-y-3">
            <input
              required
              placeholder="Full name"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
            />
            <input
              required
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
            />
            <input
              required
              type="password"
              minLength={6}
              placeholder="Password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
            />
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
            >
              <option value="patient">Patient</option>
              <option value="caregiver">Caregiver / Caretaker</option>
              <option value="doctor">Doctor</option>
              <option value="admin">Admin</option>
            </select>
            <button className="w-full py-3 bg-[#4943a5] text-white rounded-2xl font-bold text-sm hover:bg-[#3d378f]">
              Create account
            </button>
          </form>
          {msg && <div className="text-xs text-emerald-700 bg-emerald-50 p-3 rounded-xl mt-3">{msg}</div>}
          {err && <div className="text-xs text-red-700 bg-red-50 p-3 rounded-xl mt-3">{err}</div>}
        </div>

        <div className="md:col-span-7 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
          <h2 className="text-xl font-bold font-serif mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-[#4943a5]" /> All users ({users.length})
          </h2>
          <div className="divide-y divide-[#f0ebe0] max-h-[420px] overflow-auto">
            {users.map((u) => (
              <div key={u.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="font-semibold text-sm text-[#273047]">{u.full_name || u.email}</div>
                  <div className="text-xs text-gray-500">{u.email}</div>
                </div>
                <span className="text-[11px] font-bold uppercase tracking-wide bg-indigo-50 text-[#4943a5] px-2.5 py-1 rounded-lg">
                  {u.role}
                </span>
              </div>
            ))}
          </div>
          <div className="text-[11px] text-gray-400 mt-4 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5" /> Roles: patient sees own data · caregiver manages assigned patients ·
            doctor read-only analytics · admin full access.
          </div>
        </div>
      </div>
    </div>
  );
}
