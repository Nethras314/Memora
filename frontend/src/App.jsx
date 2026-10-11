import React, { useEffect, useState } from 'react';
import Sidebar from './components/Sidebar';
import PinModal from './components/PinModal';
import VoiceAssistantModal from './components/VoiceAssistantModal';
import TodayDashboard from './pages/TodayDashboard';
import MemoriesPage from './pages/MemoriesPage';
import RoutinePage from './pages/RoutinePage';
import RemindersPage from './pages/RemindersPage';
import ActivitiesPage from './pages/ActivitiesPage';
import ExercisePage from './pages/ExercisePage';
import SleepPage from './pages/SleepPage';
import CaregiverDashboard from './pages/CaregiverDashboard';
import DoctorDashboard from './pages/DoctorDashboard';
import AuthPage from './pages/AuthPage';
import AdminPage from './pages/AdminPage';
import { AuthProvider, useAuth } from './context/AuthContext';
import { api } from './services/api';
import { SUPPORTED_LANGUAGES, t } from './i18n';
import { Globe, Volume2, LogOut, Menu } from 'lucide-react';

const LANG_CACHE_PREFIX = 'memora_lang_';

function getCachedLanguage(patientId) {
  if (!patientId) return '';
  try {
    return localStorage.getItem(`${LANG_CACHE_PREFIX}${patientId}`) || '';
  } catch {
    return '';
  }
}

function setCachedLanguage(patientId, code) {
  if (!patientId) return;
  try {
    localStorage.setItem(`${LANG_CACHE_PREFIX}${patientId}`, code);
  } catch {
    /* ignore storage errors (private mode, etc.) */
  }
}

function normalizeRole(role) {
  const r = (role || 'caregiver').toLowerCase();
  return r === 'caretaker' ? 'caregiver' : r;
}

function Shell() {
  const { user, loading, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('today');
  const [patients, setPatients] = useState([]);
  const [currentPatient, setCurrentPatient] = useState(null);
  const [isPinModalOpen, setIsPinModalOpen] = useState(false);
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);
  const [pinVerified, setPinVerified] = useState(false);
  const [loadError, setLoadError] = useState('');
  const [language, setLanguage] = useState('en-IN');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const role = normalizeRole(user?.role);
  const isClinician = ['doctor', 'admin'].includes(role);

  useEffect(() => {
    if (!user) return;
    async function loadPatients() {
      try {
        const list = await api.getPatients();
        setPatients(list || []);
        setCurrentPatient((prev) => {
          if (prev && list.some((p) => p.id === prev.id)) return prev;
          if (normalizeRole(user?.role) === 'patient' && user?.linked_patient_id) {
            return list.find((p) => p.id === user.linked_patient_id) || list[0] || null;
          }
          return list[0] || null;
        });
        setLoadError('');
        setPinVerified(false);
      } catch (e) {
        setLoadError(e?.response?.data?.detail || 'Could not load patients. Ask your admin to assign one.');
      }
    }
    loadPatients();
  }, [user]);

  useEffect(() => {
    const pid = currentPatient?.id;
    if (!pid) {
      setLanguage('en-IN');
      return;
    }
    setLanguage(getCachedLanguage(pid) || currentPatient?.primary_language || 'en-IN');
  }, [currentPatient?.id, currentPatient?.primary_language]);

  const handleLanguageChange = async (code) => {
    setLanguage(code);
    const pid = currentPatient?.id;
    if (!pid) return;
    setCachedLanguage(pid, code);
    try {
      await api.updatePatientLanguage(pid, code);
    } catch {
      /* keep the local value; the backend write is best-effort */
    }
  };

  useEffect(() => {
    if (role === 'admin') setActiveTab('admin');
    else setActiveTab('today');
  }, [role]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-muted">
        <span className="animate-pulse">Loading MEMORA…</span>
      </div>
    );
  }
  if (!user) return <AuthPage />;

  const handleOpenPin = () => {
    setSidebarOpen(false);
    if (pinVerified) setActiveTab('memories');
    else setIsPinModalOpen(true);
  };

  const handlePinSuccess = () => {
    setPinVerified(true);
    setIsPinModalOpen(false);
    setActiveTab('memories');
  };

  const handleSelectPatient = (patientId) => {
    const selected = patients.find((p) => p.id === patientId);
    if (selected) {
      setCurrentPatient(selected);
      setPinVerified(false);
    }
  };

  const handleNav = (tab) => {
    setActiveTab(tab);
    setSidebarOpen(false);
  };

  const canSeeCaregiver = ['caregiver', 'doctor', 'admin', 'patient'].includes(role);
  const canSeeAdmin = role === 'admin';

  return (
    <div className="min-h-screen bg-cream">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={handleNav}
        currentPatient={currentPatient}
        onOpenPinModal={handleOpenPin}
        onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
        user={user}
        role={role}
        language={language}
        showCaregiver={canSeeCaregiver}
        showAdmin={canSeeAdmin}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {sidebarOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
        />
      )}

      <div className="flex min-h-screen flex-col lg:pl-72">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b border-line bg-paper px-4 md:px-8">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="icon-btn lg:hidden"
              aria-label="Open navigation"
            >
              <Menu className="h-6 w-6" />
            </button>
            <div className="flex items-center gap-2 text-xs font-semibold text-muted">
              <span className="h-2.5 w-2.5 rounded-full bg-success" aria-hidden="true" />
              <span className="hidden sm:inline">
                {user?.full_name || user?.email} · <span className="uppercase">{role}</span>
              </span>
              <span className="sm:hidden uppercase">{role}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <div className="flex items-center gap-1.5 rounded-full bg-mint px-2 py-1 text-sage">
              <Globe className="h-3.5 w-3.5" aria-hidden="true" />
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="cursor-pointer bg-transparent text-xs font-semibold text-sage"
                aria-label="Choose language"
              >
                {SUPPORTED_LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>{l.label}</option>
                ))}
              </select>
            </div>

            <button
              onClick={() => setIsVoiceModalOpen(true)}
              className="flex items-center gap-1 text-xs font-bold text-primary hover:underline"
            >
              <Volume2 className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">{t(language, 'voiceReady')}</span>
            </button>

            <button
              onClick={logout}
              className="flex items-center gap-1 text-xs font-bold text-muted hover:text-danger"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">{t(language, 'signOut')}</span>
            </button>
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl flex-1 p-4 md:p-8 lg:p-10">
          {loadError && (
            <div className="mb-6 rounded-2xl border border-warning-bg bg-warning-bg p-4 text-sm text-warning">
              {loadError}
            </div>
          )}
          {activeTab === 'today' && (
            <TodayDashboard
              currentPatient={currentPatient}
              language={language}
              onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
              onOpenPinModal={() => setIsPinModalOpen(true)}
              pinVerified={pinVerified}
              setActiveTab={setActiveTab}
            />
          )}
          {activeTab === 'memories' && <MemoriesPage currentPatient={currentPatient} language={language} />}
          {activeTab === 'routine' && <RoutinePage currentPatient={currentPatient} language={language} />}
          {activeTab === 'reminders' && <RemindersPage currentPatient={currentPatient} language={language} />}
          {activeTab === 'activities' && <ActivitiesPage currentPatient={currentPatient} language={language} />}
          {activeTab === 'exercise' && <ExercisePage language={language} />}
          {activeTab === 'sleep' && <SleepPage language={language} />}
          {activeTab === 'caregiver' && canSeeCaregiver && (
            isClinician ? (
              <DoctorDashboard
                patients={patients}
                currentPatient={currentPatient}
                onSelectPatient={handleSelectPatient}
                role={role}
              />
            ) : (
              <CaregiverDashboard
                patients={patients}
                currentPatient={currentPatient}
                onSelectPatient={handleSelectPatient}
                language={language}
              />
            )
          )}
          {activeTab === 'admin' && canSeeAdmin && <AdminPage />}
        </main>

        <footer className="border-t border-line py-6 text-center text-xs text-faint">
          MEMORA © 2026 · Cognitive & Daily-Life Companion · SIH26003 (Team VERTEX)
        </footer>
      </div>

      <PinModal
        isOpen={isPinModalOpen}
        onClose={() => setIsPinModalOpen(false)}
        onSuccess={handlePinSuccess}
        patientId={currentPatient?.id || 1}
      />

      <VoiceAssistantModal
        isOpen={isVoiceModalOpen}
        onClose={() => setIsVoiceModalOpen(false)}
        currentPatient={currentPatient}
        language={language}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
