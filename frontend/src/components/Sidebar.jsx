import React from 'react';
import {
  Home,
  Mic,
  Image,
  Calendar,
  Bell,
  Brain,
  Activity,
  Moon,
  HeartHandshake,
  ShieldCheck,
  X,
} from 'lucide-react';
import { t } from '../i18n';

export default function Sidebar({
  activeTab,
  setActiveTab,
  currentPatient,
  onOpenPinModal,
  onOpenVoiceModal,
  user,
  role,
  language = 'en-IN',
  showCaregiver = true,
  showAdmin = false,
  open = false,
  onClose,
}) {
  const baseItems = [
    { id: 'today', label: t(language, 'navToday'), icon: Home },
    { id: 'memories', label: t(language, 'navMemories'), icon: Image, requiresPin: true },
    { id: 'routine', label: t(language, 'navRoutine'), icon: Calendar },
    { id: 'reminders', label: t(language, 'navReminders'), icon: Bell },
    { id: 'activities', label: t(language, 'navActivities'), icon: Brain },
    { id: 'exercise', label: t(language, 'navExercise'), icon: Activity },
    { id: 'sleep', label: t(language, 'navSleep'), icon: Moon },
  ];
  const navItems = [
    ...baseItems,
    ...(showCaregiver
      ? [
          {
            id: 'caregiver',
            label:
              role === 'patient'
                ? t(language, 'navProgress')
                : role === 'doctor' || role === 'admin'
                  ? t(language, 'navClinical')
                  : t(language, 'navCaregiver'),
            icon: HeartHandshake,
          },
        ]
      : []),
    ...(showAdmin ? [{ id: 'admin', label: t(language, 'navAdmin'), icon: ShieldCheck }] : []),
  ];

  const handleNavClick = (item) => {
    if (item.requiresPin) {
      onOpenPinModal();
    } else {
      setActiveTab(item.id);
    }
  };

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-line bg-paper p-5 shadow-soft transition-transform duration-200 lg:translate-x-0 ${
        open ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      <div className="flex items-start justify-between">
        <div
          className="flex cursor-pointer items-center gap-3"
          onClick={() => setActiveTab('today')}
          role="button"
          tabIndex={0}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-2xl text-white shadow-soft">
            🌼
          </div>
          <div>
            <h1 className="font-serif text-2xl font-bold tracking-tight text-ink">MEMORA</h1>
            <p className="text-[10px] font-semibold uppercase tracking-[3px] text-muted">Together, Each Day</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="icon-btn lg:hidden"
          aria-label="Close navigation"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      <div className="mt-6 flex flex-1 flex-col overflow-y-auto">
        <div className="mb-4 flex items-center gap-3 rounded-2xl border border-line-soft bg-mint p-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-saffron text-xl font-bold text-ink shadow-soft">
            {currentPatient?.name?.[0]?.toUpperCase() || 'M'}
          </div>
          <div className="min-w-0">
            <strong className="block truncate text-base text-ink">{currentPatient?.name || 'No patient yet'}</strong>
            <span className="text-xs text-muted">Your gentle space</span>
          </div>
        </div>

        {user && (
          <div className="mb-4 truncate rounded-2xl border border-line-soft bg-primary-50 px-4 py-2.5 text-xs font-semibold text-primary">
            {(user.full_name || user.email)} · <span className="uppercase">{role}</span>
          </div>
        )}

        <button
          onClick={() => {
            onOpenVoiceModal();
            if (onClose) onClose();
          }}
          className="mb-4 flex w-full items-center justify-center gap-3 rounded-2xl bg-primary py-3 font-semibold text-white shadow-soft transition-colors hover:bg-primary-dark"
        >
          <Mic className="h-5 w-5 text-saffron" aria-hidden="true" />
          <span>{t(language, 'talkToMemora')}</span>
        </button>

        <nav className="space-y-1" aria-label="Primary navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => handleNavClick(item)}
                aria-current={isActive ? 'page' : undefined}
                className={`flex w-full items-center gap-3.5 rounded-xl px-4 py-3 font-medium transition-colors ${
                  isActive
                    ? 'bg-primary font-semibold text-white shadow-soft'
                    : 'text-muted hover:bg-cream hover:text-ink'
                }`}
              >
                <Icon className={`h-5 w-5 ${isActive ? 'text-white' : 'text-faint'}`} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="border-t border-line pt-4">
        <div className="text-center text-xs text-faint">MEMORA v2.0 · SIH 2026</div>
      </div>
    </aside>
  );
}
