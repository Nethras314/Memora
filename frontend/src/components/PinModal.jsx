import React, { useState } from 'react';
import { Lock, X, Check } from 'lucide-react';
import { api } from '../services/api';

export default function PinModal({ isOpen, onClose, onSuccess }) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleDigit = (digit) => {
    if (pin.length < 4) {
      const nextPin = pin + digit;
      setPin(nextPin);
      setError('');
      if (nextPin.length === 4) {
        verify(nextPin);
      }
    }
  };

  const handleClear = () => {
    setPin('');
    setError('');
  };

  const verify = async (pinToVerify) => {
    setLoading(true);
    setError('');
    try {
      await api.verifyPin(pinToVerify);
      setLoading(false);
      setPin('');
      onSuccess();
    } catch (err) {
      setLoading(false);
      setError('Incorrect PIN. Please try again or ask family.');
      setPin('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl p-8 max-w-sm w-full shadow-2xl border border-[#e5dfd4] relative text-center">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 p-2 rounded-full"
        >
          <X className="w-6 h-6" />
        </button>

        <div className="w-16 h-16 bg-[#eef0fc] text-[#4943a5] rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl shadow-inner">
          <Lock className="w-8 h-8" />
        </div>

        <h2 className="text-2xl font-bold font-serif text-[#273047] mb-1">Private Memory Bank</h2>
        <p className="text-sm text-[#68738a] mb-6">Enter your 4-digit PIN to open familiar moments.</p>

        {/* PIN Dots */}
        <div className="flex justify-center gap-4 mb-6">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className={`w-4 h-4 rounded-full border-2 transition-all ${
                pin.length > i ? 'bg-[#4943a5] border-[#4943a5] scale-110' : 'border-gray-300'
              }`}
            />
          ))}
        </div>

        {error && <div className="text-sm text-red-600 font-medium mb-4 bg-red-50 py-2 px-3 rounded-xl">{error}</div>}

        {/* Number Dial */}
        <div className="grid grid-cols-3 gap-3 max-w-[260px] mx-auto mb-4">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
            <button
              key={n}
              onClick={() => handleDigit(n.toString())}
              className="h-16 text-2xl font-semibold bg-[#faf8f2] hover:bg-[#ece8dc] text-[#273047] rounded-2xl border border-[#e8e2d5] transition active:scale-95 flex items-center justify-center"
            >
              {n}
            </button>
          ))}
          <button
            onClick={handleClear}
            className="h-16 text-sm font-semibold bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-2xl transition"
          >
            Clear
          </button>
          <button
            onClick={() => handleDigit('0')}
            className="h-16 text-2xl font-semibold bg-[#faf8f2] hover:bg-[#ece8dc] text-[#273047] rounded-2xl border border-[#e8e2d5] transition active:scale-95 flex items-center justify-center"
          >
            0
          </button>
          <div className="h-16 flex items-center justify-center text-xs text-gray-400">
            PIN: 1234
          </div>
        </div>
      </div>
    </div>
  );
}
