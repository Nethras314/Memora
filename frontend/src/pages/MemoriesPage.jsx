import React, { useState, useEffect } from 'react';
import { Image, Plus, Volume2, Sparkles, Heart } from 'lucide-react';
import { api } from '../services/api';

export default function MemoriesPage({ currentPatient }) {
  const [memories, setMemories] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(true);

  // Form state
  const [category, setCategory] = useState('Person');
  const [title, setTitle] = useState('');
  const [details, setDetails] = useState('');
  const [photoFile, setPhotoFile] = useState(null);

  useEffect(() => {
    loadMemories();
  }, [currentPatient]);

  const loadMemories = async () => {
    try {
      const data = await api.getMemories(currentPatient?.id || 1);
      setMemories(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const speakMemory = (m) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const text = `${m.title}. ${m.details}`;
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.85;
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleSaveMemory = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('patient_id', currentPatient?.id || 1);
    formData.append('category', category);
    formData.append('title', title);
    formData.append('details', details);
    if (photoFile) {
      formData.append('photo', photoFile);
    }

    try {
      await api.createMemory(formData);
      setShowAddModal(false);
      setTitle('');
      setDetails('');
      setPhotoFile(null);
      loadMemories();
    } catch (err) {
      alert('Error saving memory.');
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-serif text-[#273047]">Personal Memory Bank</h1>
          <p className="text-sm text-[#68738a] mt-1">Familiar moments, loved ones, and favorite memories.</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-[#4943a5] text-white px-5 py-3 rounded-2xl font-semibold flex items-center gap-2 shadow-md hover:bg-[#3d378f] transition"
        >
          <Plus className="w-5 h-5" />
          <span>Save New Memory</span>
        </button>
      </div>

      {/* Memory Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {memories.map((m) => (
          <div
            key={m.id}
            className="bg-[#fffefb] rounded-3xl overflow-hidden border border-[#e5dfd4] shadow-sm hover:shadow-md transition flex flex-col justify-between"
          >
            {m.photo_url ? (
              <img src={m.photo_url} alt={m.title} className="w-full h-48 object-cover" />
            ) : (
              <div className="w-full h-48 bg-[#eeece7] flex items-center justify-center text-4xl">
                🖼️
              </div>
            )}

            <div className="p-6 flex-1 flex flex-col justify-between">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-[#4943a5] bg-indigo-50 px-3 py-1 rounded-full">
                  {m.category}
                </span>
                <h3 className="text-xl font-bold font-serif text-[#273047] mt-3 mb-2">{m.title}</h3>
                <p className="text-sm text-[#5d687e] leading-relaxed">{m.details}</p>
              </div>

              <div className="pt-4 mt-4 border-t border-[#f0ebe0] flex items-center justify-between">
                <button
                  onClick={() => speakMemory(m)}
                  className="text-xs font-bold text-[#4943a5] flex items-center gap-1.5 hover:underline"
                >
                  <Volume2 className="w-4 h-4" />
                  <span>Listen to memory</span>
                </button>
                <Heart className="w-4 h-4 text-red-400 fill-red-400" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Memory Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl border border-[#e5dfd4]">
            <h2 className="text-2xl font-bold font-serif text-[#273047] mb-2">Save a Familiar Moment</h2>
            <p className="text-sm text-[#68738a] mb-6">Helps stimulate long-term recognition.</p>

            <form onSubmit={handleSaveMemory} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#273047] uppercase mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
                >
                  <option>Person</option>
                  <option>Place</option>
                  <option>Food</option>
                  <option>Activity</option>
                  <option>Important Memory</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#273047] uppercase mb-1">Title</label>
                <input
                  type="text"
                  required
                  placeholder="E.g., Eldest Daughter"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#273047] uppercase mb-1">Details</label>
                <textarea
                  required
                  rows={3}
                  placeholder="E.g., Anitha loves cooking and calls every evening."
                  value={details}
                  onChange={(e) => setDetails(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm resize-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#273047] uppercase mb-1">Upload Photo</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setPhotoFile(e.target.files[0])}
                  className="w-full text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-[#4943a5]"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-3 border border-gray-300 rounded-2xl font-bold text-sm text-gray-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 bg-[#4943a5] text-white rounded-2xl font-bold text-sm hover:bg-[#3d378f]"
                >
                  Save Memory
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
