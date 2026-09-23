import React, { useState, useEffect } from 'react';
import { CheckCircle2, Circle, Clock, Bell, Plus } from 'lucide-react';
import { api } from '../services/api';

export default function RoutinePage({ currentPatient }) {
  const [tasks, setTasks] = useState([]);
  const [reminders, setReminders] = useState([]);

  useEffect(() => {
    loadData();
  }, [currentPatient]);

  const loadData = async () => {
    try {
      const [t, r] = await Promise.all([
        api.getTasks(currentPatient?.id || 1),
        api.getReminders(currentPatient?.id || 1),
      ]);
      setTasks(t);
      setReminders(r);
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleTask = async (taskId) => {
    try {
      const updated = await api.toggleTask(taskId, currentPatient?.id || 1);
      setTasks(tasks.map((t) => (t.id === taskId ? updated : t)));
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleReminder = async (reminderId) => {
    try {
      const updated = await api.toggleReminder(reminderId, currentPatient?.id || 1);
      setReminders(reminders.map((r) => (r.id === reminderId ? updated : r)));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold font-serif text-[#273047]">My Daily Routine</h1>
        <p className="text-sm text-[#68738a] mt-1">Calm, structured steps for each part of the day.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Tasks Section */}
        <div className="md:col-span-7 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
          <h2 className="text-xl font-bold font-serif text-[#273047] mb-6">Today's Schedule</h2>
          <div className="space-y-3">
            {tasks.map((task) => (
              <div
                key={task.id}
                onClick={() => handleToggleTask(task.id)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                  task.done
                    ? 'bg-emerald-50/50 border-emerald-200 opacity-75'
                    : 'bg-[#faf8f2] border-[#e8e2d5] hover:border-[#4943a5]'
                }`}
              >
                <div className="flex items-center gap-3">
                  {task.done ? (
                    <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                  ) : (
                    <Circle className="w-6 h-6 text-gray-400" />
                  )}
                  <div>
                    <span className={`font-semibold text-base block ${task.done ? 'line-through text-gray-500' : 'text-[#273047]'}`}>
                      {task.title}
                    </span>
                    <span className="text-xs text-[#68738a]">{task.category}</span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 text-sm font-mono text-[#546077] bg-white px-3 py-1.5 rounded-xl border border-gray-200">
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span>{task.task_time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Reminders Section */}
        <div className="md:col-span-5 bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
          <h2 className="text-xl font-bold font-serif text-[#273047] mb-6">Gentle Alerts</h2>
          <div className="space-y-3">
            {reminders.map((rem) => (
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
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
