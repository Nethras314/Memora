import React, { useState, useRef } from 'react';
import { Mic, MicOff, Volume2, X, Send, Globe } from 'lucide-react';
import { api } from '../services/api';

export default function VoiceAssistantModal({ isOpen, onClose, currentPatient }) {
  const [language, setLanguage] = useState(currentPatient?.primary_language || 'ta-IN');
  const [isRecording, setIsRecording] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [reply, setReply] = useState('MEMORA is ready to listen. Ask about family, reminders, or foods.');
  const [loading, setLoading] = useState(false);
  const [typedInput, setTypedInput] = useState('');
  const audioRef = useRef(null);

  if (!isOpen) return null;

  const languages = [
    { code: 'ta-IN', label: 'தமிழ் (Tamil)' },
    { code: 'hi-IN', label: 'हिन्दी (Hindi)' },
    { code: 'kn-IN', label: 'ಕನ್ನಡ (Kannada)' },
    { code: 'en-IN', label: 'English' },
  ];

  const handleSendQuestion = async (text) => {
    if (!text.trim()) return;
    setLoading(true);
    setTranscription(text);
    setTypedInput('');

    try {
      const res = await api.voiceInteract({
        patient_id: currentPatient?.id || 1,
        question_text: text,
        language_code: language,
      });

      setReply(res.reply_text);

      // Playback audio if Sarvam AI base64 is returned
      if (res.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${res.audio_base64}`);
        audio.play();
      } else if ('speechSynthesis' in window) {
        // Fallback to client synthesis
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(res.reply_text);
        utterance.lang = language;
        utterance.rate = 0.85;
        window.speechSynthesis.speak(utterance);
      }
    } catch (err) {
      setReply("I'm here with you. Please try asking again.");
    } finally {
      setLoading(false);
    }
  };

  const handleStartListening = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert("Browser speech recognition isn't available. Please type your question below.");
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = language;
    recognition.continuous = false;
    recognition.interimResults = false;

    setIsRecording(true);
    setReply('Listening gently...');

    recognition.onresult = (e) => {
      setIsRecording(false);
      const spokenText = e.results[0][0].transcript;
      handleSendQuestion(spokenText);
    };

    recognition.onerror = () => {
      setIsRecording(false);
      setReply('I could not hear clearly. Feel free to try again.');
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognition.start();
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl p-8 max-w-lg w-full shadow-2xl border border-[#e5dfd4] relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 p-2 rounded-full"
        >
          <X className="w-6 h-6" />
        </button>

        {/* Header */}
        <div className="flex items-center justify-between mb-6 pr-8">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-[#4943a5] text-white flex items-center justify-center">
              <Mic className="w-6 h-6 text-amber-300" />
            </div>
            <div>
              <h2 className="text-xl font-bold font-serif text-[#273047]">Talk to MEMORA</h2>
              <p className="text-xs text-[#68738a]">Powered by Sarvam AI Indian Regional Voice</p>
            </div>
          </div>
        </div>

        {/* Language Selector */}
        <div className="flex items-center gap-2 mb-6 bg-[#faf8f2] p-2 rounded-2xl border border-[#e8e2d5]">
          <Globe className="w-5 h-5 text-[#4943a5] ml-2" />
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full bg-transparent font-medium text-sm text-[#273047] outline-none"
          >
            {languages.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </div>

        {/* Dynamic Speech Display */}
        <div className="space-y-4 mb-6">
          {transcription && (
            <div className="p-4 rounded-2xl bg-[#f5f3ff] text-sm text-[#4943a5] border border-indigo-100">
              <span className="font-bold block text-xs uppercase mb-1">You Asked:</span>
              "{transcription}"
            </div>
          )}

          <div className="p-5 rounded-2xl bg-[#dceee9] text-[#1c473f] text-lg font-medium shadow-sm border border-[#c1e2d9] min-h-[90px] flex items-center">
            {loading ? (
              <div className="flex items-center gap-3">
                <span className="animate-spin text-2xl">⏳</span>
                <span>Thinking gently...</span>
              </div>
            ) : (
              reply
            )}
          </div>
        </div>

        {/* Push to Talk Button */}
        <div className="flex justify-center mb-6">
          <button
            onClick={handleStartListening}
            className={`w-24 h-24 rounded-full flex flex-col items-center justify-center gap-1 shadow-lg transition-all active:scale-95 ${
              isRecording
                ? 'bg-red-500 text-white animate-pulse'
                : 'bg-[#4943a5] hover:bg-[#3d378f] text-white'
            }`}
          >
            {isRecording ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
            <span className="text-xs font-semibold">{isRecording ? 'Listening' : 'Tap & Speak'}</span>
          </button>
        </div>

        {/* Text Input Fallback */}
        <div className="flex gap-2">
          <input
            type="text"
            value={typedInput}
            onChange={(e) => setTypedInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendQuestion(typedInput)}
            placeholder="Or type: Who is my daughter? / என் மகள் யார்?"
            className="flex-1 px-4 py-3 rounded-2xl border border-[#dcd6cc] bg-[#faf8f2] text-sm outline-none focus:border-[#4943a5]"
          />
          <button
            onClick={() => handleSendQuestion(typedInput)}
            className="px-5 bg-[#4943a5] text-white rounded-2xl font-semibold hover:bg-[#3d378f] transition"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
