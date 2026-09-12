import React, { useState, useEffect } from 'react';
import { Brain, Sparkles, Trophy, RotateCcw, Volume2, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

export default function ActivitiesPage({ currentPatient }) {
  // DDA Game State
  const [gameConfig, setGameConfig] = useState(null);
  const [gameState, setGameState] = useState('idle'); // idle, showing, playing, finished
  const [userInput, setUserInput] = useState([]);
  const [startTime, setStartTime] = useState(0);
  const [gameResult, setGameResult] = useState(null);
  const [loadingGame, setLoadingGame] = useState(false);

  // GK State
  const [gkQuestion, setGkQuestion] = useState(null);
  const [gkFeedback, setGkFeedback] = useState('');

  // Attention State
  const [attentionQuestion, setAttentionQuestion] = useState(null);
  const [attentionFeedback, setAttentionFeedback] = useState('');

  // Task Animation State
  const [taskStep, setTaskStep] = useState(1);

  useEffect(() => {
    loadNextGame();
    loadGk();
    loadAttention();
  }, [currentPatient]);

  const loadNextGame = async () => {
    setLoadingGame(true);
    try {
      const config = await api.getNextGame(currentPatient?.id || 1);
      setGameConfig(config);
      setGameState('idle');
      setUserInput([]);
      setGameResult(null);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingGame(false);
    }
  };

  const loadGk = async () => {
    try {
      const q = await api.getGkQuestion();
      setGkQuestion(q);
      setGkFeedback('');
    } catch (e) {
      console.error(e);
    }
  };

  const loadAttention = async () => {
    try {
      const q = await api.getAttentionQuestion();
      setAttentionQuestion(q);
      setAttentionFeedback('');
    } catch (e) {
      console.error(e);
    }
  };

  const startMemoryGame = () => {
    if (!gameConfig) return;
    setGameState('showing');
    setUserInput([]);
    setGameResult(null);

    // After display duration, switch to playing mode and start latency timer
    setTimeout(() => {
      setGameState('playing');
      setStartTime(Date.now());
    }, gameConfig.display_duration_ms || 3000);
  };

  const handleSelectSymbol = async (symbol) => {
    if (gameState !== 'playing') return;

    const nextInput = [...userInput, symbol];
    setUserInput(nextInput);

    // If user selected full sequence length
    if (nextInput.length === gameConfig.sequence.length) {
      const latency = Date.now() - startTime;
      let mistakes = 0;
      for (let i = 0; i < gameConfig.sequence.length; i++) {
        if (nextInput[i] !== gameConfig.sequence[i]) mistakes++;
      }

      const isSuccess = mistakes === 0;
      const accuracy = isSuccess ? 1.0 : Math.max(0, 1 - mistakes / gameConfig.sequence.length);

      setGameResult({
        success: isSuccess,
        latencyMs: latency,
        accuracy: accuracy,
      });
      setGameState('finished');

      // Vocal congratulation
      if ('speechSynthesis' in window) {
        const msg = isSuccess ? 'Excellent memory! Well done.' : 'Good try! Practice makes us stronger.';
        const utt = new SpeechSynthesisUtterance(msg);
        utt.rate = 0.85;
        window.speechSynthesis.speak(utt);
      }

      // Log session telemetry to FastAPI -> DDA Engine
      try {
        await api.logCognitiveSession({
          patient_id: currentPatient?.id || 1,
          game_type: 'sequence_memory',
          difficulty_level: gameConfig.difficulty_level,
          score: isSuccess ? 100 : Math.round(accuracy * 100),
          accuracy: accuracy,
          reaction_time_ms: latency,
          mistake_count: mistakes,
        });
      } catch (e) {
        console.error('Failed to log telemetry', e);
      }
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold font-serif text-[#273047]">AI Cognitive Activities</h1>
        <p className="text-sm text-[#68738a] mt-1">
          Gentle exercises with <b>AI-Powered Dynamic Difficulty Adjustment (DDA)</b>.
        </p>
      </div>

      {/* 1. Dynamic Difficulty Memory Game */}
      <div className="bg-[#fffefb] p-8 rounded-3xl border border-[#e5dfd4] shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-[#4943a5]" />
            <h2 className="text-2xl font-bold font-serif text-[#273047]">Memory Sequence Game</h2>
          </div>
          {gameConfig && (
            <span className="text-xs font-bold uppercase tracking-wider bg-indigo-50 text-[#4943a5] px-3 py-1.5 rounded-xl border border-indigo-100">
              AI Difficulty Level: {gameConfig.difficulty_level}
            </span>
          )}
        </div>

        <p className="text-sm text-[#68738a] mb-6">
          {gameConfig?.guidance_cue || 'Watch the symbols carefully, then pick them in the same order.'}
        </p>

        {/* Display Area */}
        <div className="min-h-[120px] bg-[#faf8f2] rounded-2xl border border-[#e8e2d5] flex items-center justify-center p-6 mb-6">
          {gameState === 'idle' && (
            <button
              onClick={startMemoryGame}
              className="bg-[#4943a5] text-white px-6 py-3 rounded-2xl font-bold hover:bg-[#3d378f] shadow-md transition"
            >
              Start Game →
            </button>
          )}

          {gameState === 'showing' && (
            <div className="flex gap-4 text-5xl animate-pulse">
              {gameConfig?.sequence?.map((sym, idx) => (
                <span key={idx} className="p-2 bg-white rounded-2xl shadow-sm border border-gray-100">
                  {sym}
                </span>
              ))}
            </div>
          )}

          {gameState === 'playing' && (
            <div className="text-center">
              <div className="text-sm font-semibold text-[#4943a5] mb-2">
                Selected {userInput.length} of {gameConfig?.sequence?.length}:
              </div>
              <div className="flex gap-2 justify-center text-3xl min-h-[48px]">
                {userInput.map((sym, idx) => (
                  <span key={idx}>{sym}</span>
                ))}
              </div>
            </div>
          )}

          {gameState === 'finished' && gameResult && (
            <div className="text-center space-y-3">
              <div className={`text-xl font-bold ${gameResult.success ? 'text-emerald-600' : 'text-amber-600'}`}>
                {gameResult.success ? '✓ Wonderful! Perfect Sequence!' : 'Good attempt! Keep enjoying.'}
              </div>
              <div className="text-xs text-[#68738a]">
                Reaction Time: {(gameResult.latencyMs / 1000).toFixed(1)}s • AI is tuning next level...
              </div>
              <button
                onClick={loadNextGame}
                className="bg-[#4943a5] text-white px-5 py-2 rounded-xl text-sm font-semibold hover:bg-[#3d378f]"
              >
                Next AI Round →
              </button>
            </div>
          )}
        </div>

        {/* Options Grid */}
        {gameState === 'playing' && (
          <div className="grid grid-cols-4 gap-4 max-w-md mx-auto">
            {gameConfig?.options?.map((opt, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectSymbol(opt)}
                className="h-20 text-3xl bg-white hover:bg-indigo-50 border border-gray-200 rounded-2xl shadow-sm hover:shadow transition active:scale-95 flex items-center justify-center"
              >
                {opt}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 2. General Knowledge & Attention Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* GK */}
        <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
          <div className="text-xs uppercase tracking-wider font-bold text-[#68738a] mb-2">Memory Recall</div>
          <h3 className="text-xl font-bold font-serif text-[#273047] mb-3">General Knowledge</h3>
          <p className="text-sm font-medium text-[#273047] mb-4">{gkQuestion?.question || 'Loading question...'}</p>

          <div className="grid grid-cols-3 gap-2 mb-4">
            {gkQuestion?.options?.map((opt, i) => (
              <button
                key={i}
                onClick={() => setGkFeedback(opt === gkQuestion.answer ? '✓ Correct! Excellent recall.' : 'Try again.')}
                className="py-3 px-2 bg-[#faf8f2] hover:bg-indigo-50 text-sm font-semibold rounded-xl border border-[#e8e2d5] transition"
              >
                {opt}
              </button>
            ))}
          </div>

          {gkFeedback && <div className="text-sm font-bold text-emerald-700 bg-emerald-50 p-3 rounded-xl">{gkFeedback}</div>}
        </div>

        {/* Attention Odd-One-Out */}
        <div className="bg-[#fffefb] p-6 rounded-3xl border border-[#e5dfd4] shadow-sm">
          <div className="text-xs uppercase tracking-wider font-bold text-[#68738a] mb-2">Visual Focus</div>
          <h3 className="text-xl font-bold font-serif text-[#273047] mb-3">Odd One Out</h3>
          <p className="text-sm font-medium text-[#273047] mb-4">{attentionQuestion?.question || 'Spot the difference:'}</p>

          <div className="grid grid-cols-3 gap-2 mb-4">
            {attentionQuestion?.options?.map((opt, i) => (
              <button
                key={i}
                onClick={() =>
                  setAttentionFeedback(
                    opt === attentionQuestion.answer ? `✓ Exactly right! ${attentionQuestion.explanation}` : 'Try once more.'
                  )
                }
                className="py-3 px-2 bg-[#faf8f2] hover:bg-indigo-50 text-sm font-semibold rounded-xl border border-[#e8e2d5] transition"
              >
                {opt}
              </button>
            ))}
          </div>

          {attentionFeedback && (
            <div className="text-xs font-bold text-emerald-700 bg-emerald-50 p-3 rounded-xl">{attentionFeedback}</div>
          )}
        </div>
      </div>
    </div>
  );
}
