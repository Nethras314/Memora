import React, { useState, useEffect } from 'react';
import { Activity, Play, Pause, Heart } from 'lucide-react';
import { t } from '../i18n';

export default function ExercisePage({ language = 'en-IN' }) {
  const [isActive, setIsActive] = useState(false);
  const [phaseIndex, setPhaseIndex] = useState(0);

  const phases = [
    { text: t(language, 'breatheIn'), instruction: t(language, 'breatheInInstr') },
    { text: t(language, 'holdGently'), instruction: t(language, 'holdGentlyInstr') },
    { text: t(language, 'breatheOut'), instruction: t(language, 'breatheOutInstr') },
    { text: t(language, 'restComfortably'), instruction: t(language, 'restComfortablyInstr') },
  ];

  useEffect(() => {
    let interval = null;
    if (isActive) {
      speakPhase(phases[phaseIndex].text);
      interval = setInterval(() => {
        setPhaseIndex((prev) => {
          const next = (prev + 1) % 4;
          speakPhase(phases[next].text);
          return next;
        });
      }, 3500);
    } else {
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    }
    return () => clearInterval(interval);
  }, [isActive, phaseIndex]);

  const speakPhase = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 0.8;
      window.speechSynthesis.speak(u);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold font-serif text-[#273047]">{t(language, 'exerciseTitle')}</h1>
        <p className="text-sm text-[#68738a] mt-1">
          {t(language, 'exerciseSub')}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        {/* Breathing Animation Card */}
        <div className="bg-[#fffefb] p-8 rounded-3xl border border-[#e5dfd4] shadow-sm text-center flex flex-col items-center">
          <div className="text-xs uppercase tracking-wider font-bold text-[#68738a] mb-4">{t(language, 'breathingCircle')}</div>

          <div
            className={`w-48 h-48 rounded-full bg-[#dceee9] border-4 border-[#bedcd4] flex flex-col items-center justify-center transition-transform duration-1000 my-6 shadow-inner ${
              isActive && (phaseIndex === 0 || phaseIndex === 1) ? 'scale-110' : 'scale-90'
            }`}
          >
            <span className="text-5xl">🌿</span>
          </div>

          <h3 className="text-2xl font-bold font-serif text-[#273047] mb-1">{phases[phaseIndex].text}</h3>
          <p className="text-sm text-[#68738a] mb-6">{phases[phaseIndex].instruction}</p>

          <button
            onClick={() => setIsActive(!isActive)}
            className={`px-8 py-3 rounded-2xl font-bold flex items-center gap-2 shadow-md transition ${
              isActive ? 'bg-amber-600 text-white hover:bg-amber-700' : 'bg-[#4943a5] text-white hover:bg-[#3d378f]'
            }`}
          >
            {isActive ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            <span>{isActive ? t(language, 'pauseBreathing') : t(language, 'startCalmBreathing')}</span>
          </button>
        </div>

        {/* Movement Routines */}
        <div className="bg-[#fffefb] p-8 rounded-3xl border border-[#e5dfd4] shadow-sm space-y-4">
          <h3 className="text-xl font-bold font-serif text-[#273047] mb-4">{t(language, 'dailyGentleMovement')}</h3>

          <div className="p-4 rounded-2xl bg-[#faf8f2] border border-[#e8e2d5] flex items-center justify-between">
            <span className="font-semibold text-sm">🧘 {t(language, 'shoulderRolls')}</span>
            <span className="text-xs font-mono text-gray-500 bg-white px-2 py-1 rounded-lg">1 min</span>
          </div>

          <div className="p-4 rounded-2xl bg-[#faf8f2] border border-[#e8e2d5] flex items-center justify-between">
            <span className="font-semibold text-sm">🚶 {t(language, 'courtyardWalk')}</span>
            <span className="text-xs font-mono text-gray-500 bg-white px-2 py-1 rounded-lg">5 mins</span>
          </div>

          <div className="p-4 rounded-2xl bg-[#faf8f2] border border-[#e8e2d5] flex items-center justify-between">
            <span className="font-semibold text-sm">🙆 {t(language, 'seatedStretch')}</span>
            <span className="text-xs font-mono text-gray-500 bg-white px-2 py-1 rounded-lg">2 mins</span>
          </div>

          <div className="text-xs text-[#68738a] bg-[#e7f2ee] p-4 rounded-2xl border border-[#d3e6df] leading-relaxed">
            <b>{t(language, 'safetyNotice')}</b> {t(language, 'safetyNoticeText')}
          </div>
        </div>
      </div>
    </div>
  );
}
