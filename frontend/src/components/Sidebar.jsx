import React from 'react';
import { Home, Mic, Image, Calendar, Bell, Brain, Activity, Moon, HeartHandshake, ShieldCheck } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, currentPatient, onOpenPinModal, onOpenVoiceModal, user, role, showCaregiver = true, showAdmin = false }) {
  const baseItems = [
    { id: 'today', label: 'Today', icon: Home },
    { id: 'memories', label: 'Memories', icon: Image, requiresPin: true },
    { id: 'routine', label: 'My Routine', icon: Calendar },
    { id: 'reminders', label: 'Reminders', icon: Bell },
    { id: 'activities', label: 'Activities & AI', icon: Brain },
    { id: 'exercise', label: 'Exercise & Yoga', icon: Activity },
    { id: 'sleep', label: 'Deep Sleep', icon: Moon },
  ];
  // Patients see the essentials; staff see monitoring tools.
  const navItems = [
    ...baseItems,
    ...(showCaregiver ? [{ id: 'caregiver', label: role === 'patient' ? 'My Progress' : 'Caregiver Portal', icon: HeartHandshake }] : []),
    ...(showAdmin ? [{ id: 'admin', label: 'Admin Portal', icon: ShieldCheck }] : []),
  ];

  const handleNavClick = (item) => {
    if (item.requiresPin) {
      onOpenPinModal();
    } else {
      setActiveTab(item.id);
    }
  };

  return (
    <aside className="w-72 bg-[#fffdfa] border-r border-[#e5dfd4] p-6 flex flex-col justify-between fixed top-0 bottom-0 left-0 z-20 shadow-sm">
      <div>
        {/* Brand */}
        <div className="flex items-center gap-3 mb-8 cursor-pointer" onClick={() => setActiveTab('today')}>
          <div className="w-12 h-12 rounded-2xl bg-[#4943a5] text-white flex items-center justify-center text-2xl shadow-md">
            ♡
          </div>
          <div>
            <h1 className="text-2xl font-bold font-serif text-[#273047] tracking-tight">MEMORA</h1>
            <p className="text-[10px] tracking-[3px] font-semibold text-[#68738a] uppercase">Together, Each Day</p>
          </div>
        </div>

        {/* Patient Badge */}
        <div className="bg-[#e7f2ee] rounded-2xl p-4 mb-4 flex items-center gap-3 border border-[#d2e5dd]">
          <div className="w-12 h-12 rounded-xl bg-[#f0b548] text-[#273047] font-bold text-xl flex items-center justify-center shadow-sm">
            {currentPatient?.name?.[0]?.toUpperCase() || 'M'}
          </div>
          <div className="overflow-hidden">
            <strong className="block text-base text-[#273047] truncate">{currentPatient?.name || 'No patient yet'}</strong>
            <span className="text-xs text-[#526079]">Your gentle space</span>
          </div>
        </div>

        {user && (
          <div className="bg-[#eef0fc] rounded-2xl px-4 py-2.5 mb-6 border border-indigo-100 text-xs font-semibold text-[#4943a5] truncate">
            {(user.full_name || user.email)} · <span className="uppercase">{role}</span>
          </div>
        )}

        {/* Voice Quick Action */}
        <button
          onClick={onOpenVoiceModal}
          className="w-full mb-6 bg-gradient-to-r from-[#4943a5] to-[#5b54c2] text-white py-3 px-4 rounded-2xl font-semibold flex items-center justify-center gap-3 shadow-md hover:brightness-105 transition"
        >
          <Mic className="w-5 h-5 text-amber-300" />
          <span>Talk to MEMORA</span>
        </button>

        {/* Navigation Links */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item)}
                className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-2xl font-medium text-sm transition-all ${
                  isActive
                    ? 'bg-[#4943a5] text-white shadow-sm font-semibold'
                    : 'text-[#5a657c] hover:bg-[#f3f0e8] hover:text-[#273047]'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-[#7d879c]'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="pt-4 border-t border-[#e5dfd4]">
        <div className="text-xs text-[#7d879c] text-center">
          MEMORA v2.0 • SIH 2026
        </div>
      </div>
    </aside>
  );
}
