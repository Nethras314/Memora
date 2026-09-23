import React, { useState, useEffect } from 'react';
import { Plus, Volume2, Heart, Edit2, Trash2, X, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function MemoriesPage({ currentPatient }) {
  const [memories, setMemories] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingMemory, setEditingMemory] = useState(null);
  const [deletingMemoryId, setDeletingMemoryId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Form state
  const [category, setCategory] = useState('Person');
  const [title, setTitle] = useState('');
  const [details, setDetails] = useState('');
  const [photoFile, setPhotoFile] = useState(null);

  useEffect(() => {
    loadMemories();
  }, [currentPatient]);

  const loadMemories = async () => {
    setLoading(true);
    try {
      const data = await api.getMemories(currentPatient?.id || 1);
      setMemories(data || []);
    } catch (e) {
      console.error(e);
      setErrorMsg('Failed to load memories.');
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

  const handleOpenAdd = () => {
    setEditingMemory(null);
    setCategory('Person');
    setTitle('');
    setDetails('');
    setPhotoFile(null);
    setErrorMsg('');
    setShowAddModal(true);
  };

  const handleOpenEdit = (m) => {
    setEditingMemory(m);
    setCategory(m.category || 'Person');
    setTitle(m.title || '');
    setDetails(m.details || '');
    setPhotoFile(null);
    setErrorMsg('');
    setShowAddModal(true);
  };

  const handleSaveMemory = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErrorMsg('');

    const formData = new FormData();
    formData.append('patient_id', currentPatient?.id || 1);
    formData.append('category', category);
    formData.append('title', title);
    formData.append('details', details);
    if (photoFile) {
      formData.append('photo', photoFile);
    }

    try {
      if (editingMemory) {
        await api.updateMemory(editingMemory.id, formData);
      } else {
        await api.createMemory(formData);
      }
      setShowAddModal(false);
      setEditingMemory(null);
      setTitle('');
      setDetails('');
      setPhotoFile(null);
      await loadMemories();
    } catch (err) {
      console.error(err);
      setErrorMsg('Error saving memory. Please check fields and try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteMemory = async () => {
    if (!deletingMemoryId) return;
    try {
      await api.deleteMemory(deletingMemoryId);
      setDeletingMemoryId(null);
      await loadMemories();
    } catch (err) {
      console.error(err);
      alert('Error deleting memory.');
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
          onClick={handleOpenAdd}
          className="bg-[#4943a5] text-white px-5 py-3 rounded-2xl font-semibold flex items-center gap-2 shadow-md hover:bg-[#3d378f] transition"
        >
          <Plus className="w-5 h-5" />
          <span>Save New Memory</span>
        </button>
      </div>

      {loading ? (
        <div className="text-center py-16 text-[#68738a]">
          <div className="animate-spin w-8 h-8 border-4 border-[#4943a5] border-t-transparent rounded-full mx-auto mb-3"></div>
          <p className="text-sm font-medium">Loading your familiar moments...</p>
        </div>
      ) : memories.length === 0 ? (
        <div className="bg-[#fffefb] rounded-3xl p-12 text-center border border-[#e5dfd4]">
          <span className="text-5xl block mb-3">🖼️</span>
          <h3 className="text-xl font-bold font-serif text-[#273047] mb-1">No memories saved yet</h3>
          <p className="text-sm text-[#68738a] mb-6">Start by adding a favorite photo of a family member, food, or hometown.</p>
          <button
            onClick={handleOpenAdd}
            className="bg-[#4943a5] text-white px-6 py-3 rounded-2xl font-semibold inline-flex items-center gap-2 shadow hover:bg-[#3d378f] transition"
          >
            <Plus className="w-4 h-4" />
            <span>Save your first memory</span>
          </button>
        </div>
      ) : (
        /* Memory Cards Grid */
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {memories.map((m) => (
            <div
              key={m.id}
              className="bg-[#fffefb] rounded-3xl overflow-hidden border border-[#e5dfd4] shadow-sm hover:shadow-md transition flex flex-col justify-between group"
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
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#4943a5] bg-indigo-50 px-3 py-1 rounded-full">
                      {m.category}
                    </span>
                    <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition">
                      <button
                        onClick={() => handleOpenEdit(m)}
                        title="Edit Memory"
                        className="p-1.5 text-gray-400 hover:text-[#4943a5] hover:bg-indigo-50 rounded-lg transition"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setDeletingMemoryId(m.id)}
                        title="Delete Memory"
                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <h3 className="text-xl font-bold font-serif text-[#273047] mt-1 mb-2">{m.title}</h3>
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
      )}

      {/* Add / Edit Memory Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl border border-[#e5dfd4] relative">
            <button
              onClick={() => {
                setShowAddModal(false);
                setEditingMemory(null);
              }}
              className="absolute top-5 right-5 text-gray-400 hover:text-gray-600 p-2 rounded-full"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-2xl font-bold font-serif text-[#273047] mb-1">
              {editingMemory ? 'Edit Familiar Moment' : 'Save a Familiar Moment'}
            </h2>
            <p className="text-sm text-[#68738a] mb-6">Helps stimulate recognition and comfort.</p>

            {errorMsg && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2 rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

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
                  placeholder="E.g., Eldest Daughter Anitha"
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
                  placeholder="E.g., Anitha loves cooking herbal tea and calls every evening."
                  value={details}
                  onChange={(e) => setDetails(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[#dcd6cc] bg-[#faf8f2] text-sm resize-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#273047] uppercase mb-1">
                  {editingMemory ? 'Change Photo (Optional)' : 'Upload Photo (Optional)'}
                </label>
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
                  onClick={() => {
                    setShowAddModal(false);
                    setEditingMemory(null);
                  }}
                  className="flex-1 py-3 border border-gray-300 rounded-2xl font-bold text-sm text-gray-600 hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 py-3 bg-[#4943a5] text-white rounded-2xl font-bold text-sm hover:bg-[#3d378f] disabled:opacity-50 transition"
                >
                  {saving ? 'Saving...' : editingMemory ? 'Update Memory' : 'Save Memory'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingMemoryId && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-sm w-full shadow-2xl border border-[#e5dfd4] text-center">
            <div className="w-12 h-12 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center mx-auto mb-3">
              <Trash2 className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold font-serif text-[#273047] mb-1">Delete this memory?</h3>
            <p className="text-sm text-[#68738a] mb-6">This action cannot be undone.</p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeletingMemoryId(null)}
                className="flex-1 py-2.5 border border-gray-300 rounded-2xl font-bold text-sm text-gray-600 hover:bg-gray-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteMemory}
                className="flex-1 py-2.5 bg-red-600 text-white rounded-2xl font-bold text-sm hover:bg-red-700 transition"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

