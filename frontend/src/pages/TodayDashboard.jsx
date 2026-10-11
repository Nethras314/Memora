import React, { useEffect, useState } from 'react';
import { Sparkles, ArrowRight, CheckCircle2, Circle, Clock, Heart, Brain, Activity, Moon } from 'lucide-react';
import { api } from '../services/api';
import { t } from '../i18n';

export default function TodayDashboard({ currentPatient, language = 'en-IN', onOpenVoiceModal, onOpenPinModal, pinVerified, setActiveTab }) {
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
      <div className="flex flex-col items-center justify-between gap-8 rounded-3xl bg-primary p-8 text-white shadow-lift md:flex-row md:p-10">
        <div className="space-y-3">
          <div className="text-xs uppercase tracking-widest text-indigo-200 font-bold">
            TODAY • {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
          </div>
          <h1 className="text-3xl md:text-4xl font-bold font-serif">
            {t(language, 'greeting')} {currentPatient?.name || 'Meenakshi'}.
          </h1>
          <p className="text-indigo-100 max-w-xl text-base leading-relaxed">
            {t(language, 'heroSub')}
          </p>
          <div className="flex gap-3 pt-2">
            <button
              onClick={onOpenVoiceModal}
              className="bg-white text-[#b04a28] px-5 py-3 rounded-2xl font-bold flex items-center gap-2 shadow-md hover:bg-indigo-50 transition"
            >
              <span>🎙 {t(language, 'talkToMemoraBtn')}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveTab('routine')}
              className="bg-white/15 hover:bg-white/20 text-white px-5 py-3 rounded-2xl font-semibold backdrop-blur-sm transition"
            >
              {t(language, 'viewRoutine')}
            </button>
          </div>
        </div>

        {/* Progress Circular Badge */}
        <div className="bg-white/10 backdrop-blur-md rounded-3xl p-6 text-center border border-white/20 min-w-[200px]">
          <div className="text-5xl font-extrabold mb-1">{progressPercent}%</div>
          <div className="text-sm font-medium text-indigo-200">{t(language, 'dailyRoutineDone')}</div>
        </div>
      </div>

      {/* Grid: Quick Actions + Today's Reminders */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Quick Actions */}
        <div className="md:col-span-7 bg-[#fffdf9] p-6 rounded-3xl border border-[#e8ddcf] shadow-sm">
          <div className="text-xs uppercase tracking-wider font-bold text-[#6e6055] mb-2">{t(language, 'quickActions')}</div>
          <h2 className="text-2xl font-bold font-serif text-[#2a211b] mb-6">{t(language, 'easyToReach')}</h2>

          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={onOpenVoiceModal}
              className="bg-[#e7efe9] hover:bg-[#cee5df] p-5 rounded-2xl text-left border border-[#d4e4da] transition flex flex-col justify-between h-28"
            >
              <span className="text-2xl">💬</span>
              <strong className="text-[#3f6b52] text-sm flex items-center justify-between">
                {t(language, 'askQuestion')} <span>→</span>
              </strong>
            </button>

            <button
              onClick={() => {
                if (pinVerified) {
                  setActiveTab('memories');
                } else if (onOpenPinModal) {
                  onOpenPinModal();
                } else {
                  setActiveTab('memories');
                }
              }}
              className="bg-[#efe8dd] hover:bg-[#e8ddcf] p-5 rounded-2xl text-left border border-[#e8ddcf] transition flex flex-col justify-between h-28"
            >
              <span className="text-2xl">▣</span>
              <strong className="text-[#3b4353] text-sm flex items-center justify-between">
                {t(language, 'openMemories')} <span>→</span>
              </strong>
            </button>

            <button
              onClick={() => setActiveTab('activities')}
              className="bg-[#f7e3c8] hover:bg-[#f3d9ae] p-5 rounded-2xl text-left border border-[#eed3a5] transition flex flex-col justify-between h-28"
            >
              <span className="text-2xl">🧠</span>
              <strong className="text-[#654e20] text-sm flex items-center justify-between">
                {t(language, 'tryActivity')} <span>→</span>
              </strong>
            </button>

            <button
              onClick={() => setActiveTab('reminders')}
              className="bg-[#f0e8dc] hover:bg-[#e8ddcf] p-5 rounded-2xl text-left border border-[#e8ddcf] transition flex flex-col justify-between h-28"
            >
              <span className="text-2xl">♧</span>
              <strong className="text-[#3b4353] text-sm flex items-center justify-between">
                {t(language, 'seeReminders')} <span>→</span>
              </strong>
            </button>
          </div>
        </div>

        {/* Reminders Mini Card */}
        <div className="md:col-span-5 bg-[#fffdf9] p-6 rounded-3xl border border-[#e8ddcf] shadow-sm flex flex-col justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider font-bold text-[#6e6055] mb-2">{t(language, 'gentlePrompts')}</div>
            <h2 className="text-2xl font-bold font-serif text-[#2a211b] mb-4">{t(language, 'todaysReminders')}</h2>

            <div className="divide-y divide-[#e8ddcf]">
              {reminders.filter((r) => r.enabled !== false).slice(0, 3).map((r) => (
                <div key={r.id} className="py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`w-3 h-3 rounded-full ${r.done ? 'bg-emerald-500' : 'bg-amber-400'}`} />
                    <span className={`text-sm font-medium ${r.done ? 'line-through text-gray-400' : 'text-[#2a211b]'}`}>
                      {r.title}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-[#6e6055] bg-gray-100 px-2 py-1 rounded-md">
                    {r.reminder_time}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => setActiveTab('reminders')}
            className="w-full mt-4 py-3 rounded-2xl font-bold text-sm text-[#b04a28] bg-indigo-50 hover:bg-indigo-100 transition"
          >
            {t(language, 'manageReminders')}
          </button>
        </div>
      </div>
    </div>
  );
}
