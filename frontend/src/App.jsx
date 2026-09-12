import React, { useState, useEffect } from 'react';
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
import { api } from './services/api';
import { Sparkles, Globe, Volume2 } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('today');
  const [patients, setPatients] = useState([
    { id: 1, name: 'Meenakshi', age: 70, gender: 'Female', primary_language: 'ta-IN' },
    { id: 2, name: 'Raman', age: 75, gender: 'Male', primary_language: 'en-IN' }
  ]);
  const [currentPatient, setCurrentPatient] = useState(patients[0]);
  const [isPinModalOpen, setIsPinModalOpen] = useState(false);
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);
  const [pinVerified, setPinVerified] = useState(false);

  useEffect(() => {
    async function loadPatients() {
      try {
        const list = await api.getPatients();
        if (list && list.length > 0) {
          setPatients(list);
          setCurrentPatient(list[0]);
        }
      } catch (e) {
        console.error('Using default mock patients', e);
      }
    }
    loadPatients();
  }, []);

  const handleOpenPin = () => {
    if (pinVerified) {
      setActiveTab('memories');
    } else {
      setIsPinModalOpen(true);
    }
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
      setPinVerified(false); // Re-require PIN on patient switch for privacy
    }
  };

  return (
    <div className="flex min-h-screen bg-[#faf8f2]">
      {/* Elder-Friendly Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentPatient={currentPatient}
        onOpenPinModal={handleOpenPin}
        onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
      />

      {/* Main Content Area */}
      <div className="ml-72 flex-1 flex flex-col min-h-screen">
        {/* Sticky Topbar */}
        <header className="h-16 bg-[#fffdfa] border-b border-[#e5dfd4] px-8 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-2 text-xs font-bold text-[#5c687f]">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>A quiet, supportive place for today</span>
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
          </div>
        </header>

        {/* Tab Body Content */}
        <main className="flex-1 p-8 md:p-10 max-w-7xl mx-auto w-full">
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

          {activeTab === 'caregiver' && (
            <CaregiverDashboard
              patients={patients}
              currentPatient={currentPatient}
              onSelectPatient={handleSelectPatient}
            />
          )}
        </main>

        {/* Footer */}
        <footer className="py-6 text-center text-xs text-[#7d879c] border-t border-[#e5dfd4]">
          MEMORA © 2026 • AI-Based Cognitive & Daily-Life Assistance Platform • SIH26003 (Team VERTEX)
        </footer>
      </div>

      {/* Global Modals */}
      <PinModal
        isOpen={isPinModalOpen}
        onClose={() => setIsPinModalOpen(false)}
        onSuccess={handlePinSuccess}
      />

      <VoiceAssistantModal
        isOpen={isVoiceModalOpen}
        onClose={() => setIsVoiceModalOpen(false)}
        currentPatient={currentPatient}
      />
    </div>
  );
}
