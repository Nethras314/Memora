import React, { useEffect, useState } from 'react';
import { Sparkles, ArrowRight, CheckCircle2, Circle, Clock, Heart, Brain, Activity, Moon } from 'lucide-react';
import { api } from '../services/api';

export default function TodayDashboard({ currentPatient, onOpenVoiceModal, setActiveTab }) {
  const [tasks, setTasks] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [taskList, reminderList] = await Promise.all([
          api.getTasks(currentPatient?.id || 1),
          api.getReminders(currentPatient?.id || 1),
        ]);
        setTasks(taskList);
        setReminders(reminderList);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [currentPatient]);

  const completedTasks = tasks.filter((t) => t.done).length;
  const progressPercent = tasks.length ? Math.round((completedTasks / tasks.length) * 100) : 0;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Hero Welcome Banner */}
      <div className="bg-gradient-to-r from-[#4943a5] via-[#534cb3] to-[#6058c7] rounded-3xl p-8 md:p-10 text-white shadow-xl flex flex-col md:flex-row items-center justify-between gap-8">
        <div className="space-y-3">
          <div className="text-xs uppercase tracking-widest text-indigo-200 font-bold">
            TODAY • {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
          </div>
          <h1 className="text-3xl md:text-4xl font-bold font-serif">
            Good morning, {currentPatient?.name || 'Meenakshi'}.
          </h1>
          <p className="text-indigo-100 max-w-xl text-base leading-relaxed">
            You can ask me about family members, your next reminder, or an enjoyable activity.
          </p>
          <div className="flex gap-3 pt-2">
            <button
              onClick={onOpenVoiceModal}
              className="bg-white text-[#4943a5] px-5 py-3 rounded-2xl font-bold flex items-center gap-2 shadow-md hover:bg-indigo-50 transition"
            >
              <span>🎙 Talk to MEMORA</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveTab('routine')}
              className="bg-white/15 hover:bg-white/20 text-white px-5 py-3 rounded-2xl font-semibold backdrop-blur-sm transition"
            >
              View today's routine
            </button>
          </div>
        </div>

        {/* Progress Circular Badge */}
        <div className="bg-white/10 backdrop-blur-md rounded-3xl p-6 text-center border border-white/20 min-w-[200px]">
          <div className="text-5xl font-extrabold mb-1">{progressPercent}%</div>
          <div className="text-sm font-medium text-indigo-200">Daily routine completed</div>
        </div>
      </div>

      {/* Grid: Quick Actions + Today's Reminders */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Quick Actions */}
        <div className="md:col-span-7 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
          <div className="text-xs uppercase tracking-wider font-bold text-[#68738a] mb-2">Quick Actions</div>
          <h2 className="text-2xl font-bold font-serif text-[#273047] mb-6">Easy to reach</h2>

          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={onOpenVoiceModal}
              className="bg-[#dceee9] hover:bg-[#cee5df] p-5 rounded-2xl text-left border border-[#cbe2dc] transition flex flex-col justify-between h-28"
            >
              <span className="text-2xl">💬</span>
              <strong className="text-[#204a43] text-sm flex items-center justify-between">
                Ask a question <span>→</span>
              </strong>
            </button>

            <button
              onClick={() => setActiveTab('memories')}
              className="bg-[#eeece7] hover:bg-[#e4e1da] p-5 rounded-2xl text-left border border-[#dedad1] transition flex flex-col justify-between h-28"
            >
              <span className="text-2xl">▣</span>
              <strong className="text-[#3b4353] text-sm flex items-center justify-between">
                Open memories <span>→</span>
              </strong>
            </button>

            <button
              onClick={() => setActiveTab('activities')}
              className="bg-[#f9e7c5] hover:bg-[#f1dcaf] p-5 rounded-2xl text-left border border-[#ebd6a9] transition flex flex-col justify-between h-28"
            >
              <span className="text-2xl">🧠</span>
              <strong className="text-[#654e20] text-sm flex items-center justify-between">
                Try an activity <span>→</span>
              </strong>
            </button>

            <button
              onClick={() => setActiveTab('routine')}
              className="bg-[#f3f0ea] hover:bg-[#eae5dc] p-5 rounded-2xl text-left border border-[#dfd9ce] transition flex flex-col justify-between h-28"
            >
              <span className="text-2xl">♧</span>
              <strong className="text-[#3b4353] text-sm flex items-center justify-between">
                See reminders <span>→</span>
              </strong>
            </button>
          </div>
        </div>

        {/* Reminders Mini Card */}
        <div className="md:col-span-5 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm flex flex-col justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider font-bold text-[#68738a] mb-2">Gentle Prompts</div>
            <h2 className="text-2xl font-bold font-serif text-[#273047] mb-4">Today's Reminders</h2>

            <div className="divide-y divide-[#e5dfd4]">
              {reminders.slice(0, 3).map((r) => (
                <div key={r.id} className="py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`w-3 h-3 rounded-full ${r.done ? 'bg-emerald-500' : 'bg-amber-400'}`} />
                    <span className={`text-sm font-medium ${r.done ? 'line-through text-gray-400' : 'text-[#273047]'}`}>
                      {r.title}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-[#68738a] bg-gray-100 px-2 py-1 rounded-md">
                    {r.reminder_time}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => setActiveTab('routine')}
            className="w-full mt-4 py-3 rounded-2xl font-bold text-sm text-[#4943a5] bg-indigo-50 hover:bg-indigo-100 transition"
          >
            Manage all reminders →
          </button>
        </div>
      </div>
    </div>
  );
}
