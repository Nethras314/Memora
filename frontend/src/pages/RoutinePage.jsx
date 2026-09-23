import React, { useState, useEffect } from 'react';
import { CheckCircle2, Circle, Clock, Plus, RotateCcw, Trash2, X, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function RoutinePage({ currentPatient }) {
  const [tasks, setTasks] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [showAddTaskModal, setShowAddTaskModal] = useState(false);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskTime, setTaskTime] = useState('09:00');
  const [taskCategory, setTaskCategory] = useState('Routine');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    loadData();
  }, [currentPatient]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [t, r] = await Promise.all([
        api.getTasks(currentPatient?.id || 1),
        api.getReminders(currentPatient?.id || 1),
      ]);
      setTasks(t || []);
      setReminders(r || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleTask = async (taskId) => {
    try {
      const updated = await api.toggleTask(taskId);
      setTasks(tasks.map((t) => (t.id === taskId ? updated : t)));
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteTask = async (e, taskId) => {
    e.stopPropagation();
    try {
      await api.deleteTask(taskId);
      setTasks(tasks.filter((t) => t.id !== taskId));
    } catch (e) {
      console.error(e);
      alert('Failed to delete task.');
    }
  };

  const handleResetTasks = async () => {
    try {
      await api.resetTasks(currentPatient?.id || 1);
      const refreshed = await api.getTasks(currentPatient?.id || 1);
      setTasks(refreshed || tasks.map((t) => ({ ...t, done: false })));
    } catch (e) {
      console.error(e);
      alert('Failed to reset tasks.');
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErrorMsg('');

    try {
      const newTask = await api.createTask({
        patient_id: currentPatient?.id || 1,
        title: taskTitle,
        task_time: taskTime,
        category: taskCategory,
      });
      const refreshed = await api.getTasks(currentPatient?.id || 1);
      setTasks(refreshed || [...tasks, newTask]);
      setShowAddTaskModal(false);
      setTaskTitle('');
      setTaskTime('09:00');
      setTaskCategory('Routine');
    } catch (err) {
      console.error(err);
      setErrorMsg('Error creating routine task. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleReminder = async (reminderId) => {
    try {
      const updated = await api.toggleReminder(reminderId);
      setReminders(reminders.map((r) => (r.id === reminderId ? updated : r)));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-serif text-[#273047]">My Daily Routine</h1>
          <p className="text-sm text-[#68738a] mt-1">Calm, structured steps for each part of the day.</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleResetTasks}
            title="Reset routine completion for today"
            className="px-4 py-2.5 bg-white hover:bg-gray-50 text-[#68738a] border border-[#e5dfd4] rounded-2xl text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset Today</span>
          </button>
          <button
            onClick={() => setShowAddTaskModal(true)}
            className="px-4 py-2.5 bg-[#4943a5] hover:bg-[#3d378f] text-white rounded-2xl text-xs font-semibold flex items-center gap-1.5 shadow-md transition"
          >
            <Plus className="w-4 h-4" />
            <span>Add Routine</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Tasks Section */}
        <div className="md:col-span-7 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold font-serif text-[#273047]">Today's Schedule</h2>
            <span className="text-xs font-bold text-[#4943a5] bg-indigo-50 px-3 py-1 rounded-full">
              {tasks.filter((t) => t.done).length} / {tasks.length} Completed
            </span>
          </div>

          {loading ? (
            <div className="text-center py-12 text-[#68738a]">
              <div className="animate-spin w-6 h-6 border-2 border-[#4943a5] border-t-transparent rounded-full mx-auto mb-2"></div>
              <p className="text-xs font-medium">Loading schedule...</p>
            </div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-12 text-[#68738a]">
              <p className="text-sm">No routine tasks scheduled for today.</p>
              <button
                onClick={() => setShowAddTaskModal(true)}
                className="mt-3 text-xs font-bold text-[#4943a5] hover:underline"
              >
                + Add a routine step
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  onClick={() => handleToggleTask(task.id)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between group ${
                    task.done
                      ? 'bg-emerald-50/50 border-emerald-200 opacity-75'
                      : 'bg-[#faf8f2] border-[#e8e2d5] hover:border-[#4943a5]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {task.done ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />
                    ) : (
                      <Circle className="w-6 h-6 text-gray-400 shrink-0" />
                    )}
                    <div>
                      <span className={`font-semibold text-base block ${task.done ? 'line-through text-gray-500' : 'text-[#273047]'}`}>
                        {task.title}
                      </span>
                      <span className="text-xs text-[#68738a]">{task.category}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5 text-sm font-mono text-[#546077] bg-white px-3 py-1.5 rounded-xl border border-gray-200">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span>{task.task_time}</span>
                    </div>
                    <button
                      onClick={(e) => handleDeleteTask(e, task.id)}
                      title="Delete routine step"
                      className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg opacity-0 group-hover:opacity-100 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Reminders Section */}
        <div className="md:col-span-5 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
          <h2 className="text-xl font-bold font-serif text-[#273047] mb-6">Gentle Alerts</h2>
          <div className="space-y-3">
            {reminders.length === 0 ? (
              <p className="text-sm text-[#68738a] py-6 text-center">No gentle alerts for today.</p>
            ) : (
              reminders.map((rem) => (
              <div
                key={rem.id}
                onClick={() => handleToggleReminder(rem.id)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                  rem.done
                    ? 'bg-emerald-50/50 border-emerald-200 opacity-75'
                    : 'bg-[#faf8f2] border-[#e8e2d5] hover:border-amber-400'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className={`w-3 h-3 rounded-full ${rem.done ? 'bg-emerald-500' : 'bg-amber-400'}`} />
                  <span className={`text-sm font-medium ${rem.done ? 'line-through text-gray-400' : 'text-[#273047]'}`}>
                    {rem.title}
                  </span>
                </div>
                <span className="text-xs font-mono text-[#68738a]">{rem.reminder_time}</span>
              </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Add Task Modal */}
      {showAddTaskModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl border border-[#e5dfd4] relative">
            <button
              onClick={() => setShowAddTaskModal(false)}
              className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 p-2 rounded-full"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-2xl font-bold font-serif text-[#273047] mb-1">Add Routine Step</h2>
            <p className="text-sm text-[#68738a] mb-6">Create a gentle step for today's daily flow.</p>

            {errorMsg && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2 rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleAddTask} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#273047] uppercase mb-1">Routine Title</label>
                <input
                  type="text"
                  required
                  placeholder="E.g., Morning Walk in Courtyard"
                  value={taskTitle}
                  onChange={(e) => setTaskTitle(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-[#273047] uppercase mb-1">Time</label>
                  <input
                    type="time"
                    required
                    value={taskTime}
                    onChange={(e) => setTaskTime(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#273047] uppercase mb-1">Category</label>
                  <select
                    value={taskCategory}
                    onChange={(e) => setTaskCategory(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
                  >
                    <option value="Routine">Routine</option>
                    <option value="Daily">Daily</option>
                    <option value="Exercise">Exercise</option>
                    <option value="Cognitive">Cognitive</option>
                    <option value="Appointment">Appointment</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddTaskModal(false)}
                  className="flex-1 py-3 border border-gray-300 rounded-2xl font-bold text-sm text-gray-600 hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 py-3 bg-[#4943a5] text-white rounded-2xl font-bold text-sm hover:bg-[#3d378f] disabled:opacity-50 transition"
                >
                  {saving ? 'Saving...' : 'Add Step'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

