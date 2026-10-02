import React, { useState, useEffect } from 'react';
import { Moon, Sparkles, Volume2 } from 'lucide-react';
import { t } from '../i18n';

export default function SleepPage({ language = 'en-IN' }) {
  const [sleepScore, setSleepScore] = useState(82);
  const [isPlayingCalm, setIsPlayingCalm] = useState(false);
  const [toneMessage, setToneMessage] = useState(t(language, 'toneReady'));

  useEffect(() => {
    if (!isPlayingCalm) setToneMessage(t(language, 'toneReady'));
  }, [language]);

  const playCalmTone = () => {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(220, ctx.currentTime); // Soft A3 tone

      gain.gain.setValueAtTime(0.03, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 5);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 5);

      setIsPlayingCalm(true);
      setToneMessage('🌙 ' + t(language, 'tonePlaying'));
      setTimeout(() => {
        setIsPlayingCalm(false);
        setToneMessage(t(language, 'toneEnded'));
      }, 5000);
    } catch (e) {
      setToneMessage(t(language, 'toneUnsupported'));
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold font-serif text-[#273047]">{t(language, 'sleepTitle')}</h1>
        <p className="text-sm text-[#68738a] mt-1">{t(language, 'sleepSub')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        {/* Sleep Meter */}
        <div className="bg-[#fffefb] p-8 rounded-3xl border border-[#e5dfd4] shadow-sm text-center flex flex-col items-center">
          <div className="text-xs uppercase tracking-wider font-bold text-[#68738a] mb-2">{t(language, 'sleepScore')}</div>
          <h2 className="text-xl font-bold font-serif text-[#273047] mb-6">{t(language, 'restfulQuality')}</h2>

          <div
            className="w-48 h-48 rounded-full p-4 flex items-center justify-center mb-6 shadow-inner"
            style={{
              background: `conic-gradient(#4943a5 0% ${sleepScore}%, #e9e5dc ${sleepScore}% 100%)`,
            }}
          >
            <div className="w-36 h-36 bg-white rounded-full flex flex-col items-center justify-center shadow-sm">
              <span className="text-4xl font-extrabold text-[#4943a5]">{sleepScore}%</span>
              <span className="text-xs text-[#68738a] font-medium">{t(language, 'restful')}</span>
            </div>
          </div>

          <input
            type="range"
            min="0"
            max="100"
            value={sleepScore}
            onChange={(e) => setSleepScore(e.target.value)}
            className="w-4/5 accent-[#4943a5] cursor-pointer"
          />
          <span className="text-xs text-gray-400 mt-2">{t(language, 'simulatedMeter')}</span>
        </div>

        {/* Wind Down Audio */}
        <div className="bg-[#fffefb] p-8 rounded-3xl border border-[#e5dfd4] shadow-sm space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-[#4943a5] flex items-center justify-center">
            <Moon className="w-6 h-6" />
          </div>
          <h3 className="text-2xl font-bold font-serif text-[#273047]">{t(language, 'eveningCalmMode')}</h3>
          <p className="text-sm text-[#5a657c] leading-relaxed">
            {t(language, 'calmToneDesc')}
          </p>

          <button
            onClick={playCalmTone}
            disabled={isPlayingCalm}
            className="w-full py-4 bg-[#4943a5] text-white rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-[#3d378f] shadow-md transition disabled:opacity-50"
          >
            <Volume2 className="w-5 h-5" />
            <span>{isPlayingCalm ? t(language, 'playingTone') : t(language, 'playCalmTone')}</span>
          </button>

          <div className="text-xs text-[#205147] bg-[#e7f4f0] p-4 rounded-2xl border border-[#d2e8e0]">
            {toneMessage}
          </div>
        </div>
      </div>
    </div>
  );
}
