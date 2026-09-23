import React, { useEffect, useState } from 'react';
import { Bell, Clock, Plus, Pencil, Trash2, X, AlertCircle, Power } from 'lucide-react';
import { api } from '../services/api';

const CATEGORIES = [
  'Medicine',
  'Water/Hydration',
  'Food/Meal',
  'Exercise',
  'Medical Appointment',
  'Custom',
];

const FREQUENCIES = ['Daily', 'Once', 'Hourly', 'Weekly'];

export default function RemindersPage({ currentPatient }) {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const [title, setTitle] = useState('');
  const [reminderTime, setReminderTime] = useState('09:00');
  const [category, setCategory] = useState('Custom');
  const [frequency, setFrequency] = useState('Daily');

  useEffect(() => {
    loadReminders();
  }, [currentPatient]);

  const loadReminders = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const data = await api.getReminders(currentPatient?.id || 1);
      setReminders(data || []);
    } catch (e) {
      console.error(e);
      setErrorMsg('Could not load reminders. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setTitle('');
    setReminderTime('09:00');
    setCategory('Custom');
    setFrequency('Daily');
    setEditing(null);
    setErrorMsg('');
  };

  const handleOpenAdd = () => {
    resetForm();
    setShowModal(true);
  };

  const handleOpenEdit = (reminder) => {
    setEditing(reminder);
    setTitle(reminder.title || '');
    setReminderTime((reminder.reminder_time || '09:00').slice(0, 5));
    setCategory(reminder.category || 'Custom');
    setFrequency(reminder.frequency || 'Daily');
    setErrorMsg('');
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErrorMsg('');

    const payload = {
      patient_id: currentPatient?.id || 1,
      title,
      reminder_time: reminderTime,
      category,
      frequency,
    };

    try {
      if (editing) {
        await api.updateReminder(editing.id, payload, currentPatient?.id || 1);
      } else {
        await api.createReminder(payload);
      }
      setShowModal(false);
      resetForm();
      await loadReminders();
    } catch (err) {
      console.error(err);
      setErrorMsg('Could not save reminder. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleEnabled = async (reminderId) => {
    try {
      await api.toggleReminderEnabled(reminderId, currentPatient?.id || 1);
      await loadReminders();
    } catch (e) {
      console.error(e);
      setErrorMsg('Could not update reminder status.');
    }
  };

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await api.deleteReminder(deletingId, currentPatient?.id || 1);
      setDeletingId(null);
      await loadReminders();
    } catch (e) {
      console.error(e);
      setErrorMsg('Could not delete reminder.');
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-serif text-[#273047]">Reminders</h1>
          <p className="text-sm text-[#68738a] mt-1">Gentle prompts for medicine, meals, water, and appointments.</p>
        </div>
        <button
          onClick={handleOpenAdd}
          className="px-4 py-2.5 bg-[#4943a5] hover:bg-[#3d378f] text-white rounded-2xl text-xs font-semibold flex items-center gap-1.5 shadow-md transition"
        >
          <Plus className="w-4 h-4" />
          <span>Add Reminder</span>
        </button>
      </div>

      {errorMsg && !showModal && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-2xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
        {loading ? (
          <div className="text-center py-12 text-[#68738a]">
            <div className="animate-spin w-6 h-6 border-2 border-[#4943a5] border-t-transparent rounded-full mx-auto mb-2"></div>
            <p className="text-xs font-medium">Loading reminders...</p>
          </div>
        ) : reminders.length === 0 ? (
          <div className="text-center py-14 text-[#68738a]">
            <Bell className="w-10 h-10 mx-auto mb-3 text-[#c5c0b6]" />
            <p className="text-sm font-medium">No reminders yet.</p>
            <p className="text-xs mt-1">Add a gentle prompt for medicine, water, or a meal.</p>
            <button
              onClick={handleOpenAdd}
              className="mt-4 text-xs font-bold text-[#4943a5] hover:underline"
            >
              + Add a reminder
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {reminders.map((reminder) => (
              <div
                key={reminder.id}
                className={`p-4 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  reminder.enabled === false
                    ? 'bg-gray-50 border-gray-200 opacity-75'
                    : 'bg-[#faf8f2] border-[#e8e2d5]'
                }`}
              >
                <div className="min-w-0">
                  <span className="text-[10px] font-bold uppercase tracking-wide text-[#4943a5] bg-indigo-50 px-2 py-0.5 rounded-full">
                    {reminder.category || 'Custom'}
                  </span>
                  <p className={`mt-2 font-semibold text-base ${reminder.enabled === false ? 'text-gray-500' : 'text-[#273047]'}`}>
                    {reminder.title}
                  </p>
                  <p className="text-xs text-[#68738a] mt-1">{reminder.frequency || 'Daily'}</p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <div className="flex items-center gap-1.5 text-sm font-mono text-[#546077] bg-white px-3 py-1.5 rounded-xl border border-gray-200">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span>{reminder.reminder_time}</span>
                  </div>
                  <button
                    onClick={() => handleToggleEnabled(reminder.id)}
                    title={reminder.enabled === false ? 'Enable reminder' : 'Disable reminder'}
                    className={`px-3 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 border transition ${
                      reminder.enabled === false
                        ? 'bg-white text-[#68738a] border-gray-200 hover:bg-gray-50'
                        : 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                    }`}
                  >
                    <Power className="w-3.5 h-3.5" />
                    {reminder.enabled === false ? 'Off' : 'On'}
                  </button>
                  <button
                    onClick={() => handleOpenEdit(reminder)}
                    title="Edit reminder"
                    className="p-2 text-gray-400 hover:text-[#4943a5] hover:bg-indigo-50 rounded-xl transition"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setDeletingId(reminder.id)}
                    title="Delete reminder"
                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl border border-[#e5dfd4] relative">
            <button
              onClick={() => {
                setShowModal(false);
                resetForm();
              }}
              className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 p-2 rounded-full"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-2xl font-bold font-serif text-[#273047] mb-1">
              {editing ? 'Edit Reminder' : 'Add Reminder'}
            </h2>
            <p className="text-sm text-[#68738a] mb-6">A calm prompt for the right time of day.</p>

            {errorMsg && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2 rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#273047] uppercase mb-1">Title</label>
                <input
                  type="text"
                  required
                  placeholder="E.g., Take afternoon tablet"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-[#273047] uppercase mb-1">Time</label>
                  <input
                    type="time"
                    required
                    value={reminderTime}
                    onChange={(e) => setReminderTime(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[#273047] uppercase mb-1">Repeat</label>
                  <select
                    value={frequency}
                    onChange={(e) => setFrequency(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
                  >
                    {FREQUENCIES.map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#273047] uppercase mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
                >
                  {CATEGORIES.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    resetForm();
                  }}
                  className="flex-1 py-3 border border-gray-300 rounded-2xl font-bold text-sm text-gray-600 hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 py-3 bg-[#4943a5] text-white rounded-2xl font-bold text-sm hover:bg-[#3d378f] disabled:opacity-50 transition"
                >
                  {saving ? 'Saving...' : editing ? 'Save Changes' : 'Add Reminder'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {deletingId && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-sm w-full shadow-2xl border border-[#e5dfd4]">
            <h3 className="text-xl font-bold font-serif text-[#273047]">Delete this reminder?</h3>
            <p className="text-sm text-[#68738a] mt-2">This cannot be undone.</p>
            <div className="flex gap-3 pt-6">
              <button
                onClick={() => setDeletingId(null)}
                className="flex-1 py-3 border border-gray-300 rounded-2xl font-bold text-sm text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="flex-1 py-3 bg-red-600 text-white rounded-2xl font-bold text-sm hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
