import React, { useEffect, useState } from 'react';
import Sidebar from './components/Sidebar';
import PinModal from './components/PinModal';
import VoiceAssistantModal from './components/VoiceAssistantModal';
import TodayDashboard from './pages/TodayDashboard';
import MemoriesPage from './pages/MemoriesPage';
import RoutinePage from './pages/RoutinePage';
import ActivitiesPage from './pages/ActivitiesPage';
import ExercisePage from './pages/ExercisePage';
import SleepPage from './pages/SleepPage';
import CaregiverDashboard from './pages/CaregiverDashboard';
import AuthPage from './pages/AuthPage';
import AdminPage from './pages/AdminPage';
import { AuthProvider, useAuth } from './context/AuthContext';
import { api } from './services/api';
import { Globe, Volume2, LogOut } from 'lucide-react';

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

  const role = normalizeRole(user?.role);

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

  // Default landing tab per role
  useEffect(() => {
    if (role === 'admin') setActiveTab('admin');
    else if (role === 'patient') setActiveTab('today');
    else setActiveTab('today');
  }, [role]);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-sm text-gray-500">Loading MEMORA…</div>;
  }
  if (!user) return <AuthPage />;

  const handleOpenPin = () => {
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

  // Role-based tabs: patients get a focused view; doctors read analytics; admins manage users.
  const canSeeCaregiver = ['caregiver', 'doctor', 'admin', 'patient'].includes(role);
  const canSeeAdmin = role === 'admin';

  return (
    <div className="flex min-h-screen bg-[#faf8f2]">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentPatient={currentPatient}
        onOpenPinModal={handleOpenPin}
        onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
        user={user}
        role={role}
        showCaregiver={canSeeCaregiver}
        showAdmin={canSeeAdmin}
      />

      <div className="ml-72 flex-1 flex flex-col min-h-screen">
        <header className="h-16 bg-[#fffdfa] border-b border-[#e5dfd4] px-8 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-2 text-xs font-bold text-[#5c687f]">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>
              {user?.full_name || user?.email} · <span className="uppercase">{role}</span>
            </span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-xs font-semibold bg-[#e8f3ef] text-[#22574c] px-3 py-1.5 rounded-full flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5" />
              <span>{currentPatient?.primary_language === 'ta-IN' ? 'தமிழ் • Tamil' : 'English'}</span>
            </span>

            <button
              onClick={() => setIsVoiceModalOpen(true)}
              className="text-xs font-bold text-[#4943a5] hover:underline flex items-center gap-1"
            >
              <Volume2 className="w-4 h-4" />
              <span>Voice Ready</span>
            </button>

            <button
              onClick={logout}
              className="text-xs font-bold text-gray-500 hover:text-red-600 flex items-center gap-1"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign out</span>
            </button>
          </div>
        </header>

        <main className="flex-1 p-8 md:p-10 max-w-7xl mx-auto w-full">
          {loadError && (
            <div className="mb-6 text-sm text-amber-800 bg-amber-50 border border-amber-200 p-4 rounded-2xl">
              {loadError}
            </div>
          )}
          {activeTab === 'today' && (
            <TodayDashboard
              currentPatient={currentPatient}
              onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'memories' && <MemoriesPage currentPatient={currentPatient} />}

          {activeTab === 'routine' && <RoutinePage currentPatient={currentPatient} />}

          {activeTab === 'activities' && <ActivitiesPage currentPatient={currentPatient} />}

          {activeTab === 'exercise' && <ExercisePage />}

          {activeTab === 'sleep' && <SleepPage />}

          {activeTab === 'caregiver' && canSeeCaregiver && (
            <CaregiverDashboard
              patients={patients}
              currentPatient={currentPatient}
              onSelectPatient={handleSelectPatient}
            />
          )}

          {activeTab === 'admin' && canSeeAdmin && <AdminPage />}
        </main>

        <footer className="py-6 text-center text-xs text-[#7d879c] border-t border-[#e5dfd4]">
          MEMORA © 2026 • AI-Based Cognitive & Daily-Life Assistance Platform • SIH26003 (Team VERTEX)
        </footer>
      </div>

      <PinModal
        isOpen={isPinModalOpen}
        onClose={() => setIsPinModalOpen(false)}
        onSuccess={handlePinSuccess}
        patientId={currentPatient?.id}
      />

      <VoiceAssistantModal
        isOpen={isVoiceModalOpen}
        onClose={() => setIsVoiceModalOpen(false)}
        currentPatient={currentPatient}
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
