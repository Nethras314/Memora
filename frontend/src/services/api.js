import axios from 'axios';

const API_BASE = '/api';

export const api = {
  // Health
  checkHealth: async () => {
    const res = await axios.get(`${API_BASE}/health`);
    return res.data;
  },

  // Auth / PIN
  verifyPin: async (pin) => {
    const res = await axios.post(`${API_BASE}/auth/verify-pin`, { pin });
    return res.data;
  },

  // Patients
  getPatients: async () => {
    const res = await axios.get(`${API_BASE}/patients`);
    return res.data;
  },
  getPatient: async (id) => {
    const res = await axios.get(`${API_BASE}/patients/${id}`);
    return res.data;
  },

  // Memories
  getMemories: async (patientId = 1) => {
    const res = await axios.get(`${API_BASE}/memories?patient_id=${patientId}`);
    return res.data;
  },
  createMemory: async (formData) => {
    const res = await axios.post(`${API_BASE}/memories`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  // Routines & Reminders
  getTasks: async (patientId = 1) => {
    const res = await axios.get(`${API_BASE}/routines/tasks?patient_id=${patientId}`);
    return res.data;
  },
  toggleTask: async (taskId) => {
    const res = await axios.post(`${API_BASE}/routines/tasks/${taskId}/toggle`);
    return res.data;
  },
  getReminders: async (patientId = 1) => {
    const res = await axios.get(`${API_BASE}/routines/reminders?patient_id=${patientId}`);
    return res.data;
  },
  toggleReminder: async (reminderId) => {
    const res = await axios.post(`${API_BASE}/routines/reminders/${reminderId}/toggle`);
    return res.data;
  },

  // Cognitive Engine & DDA
  getNextGame: async (patientId = 1, gameType = 'sequence_memory') => {
    const res = await axios.get(`${API_BASE}/cognitive/next-game?patient_id=${patientId}&game_type=${gameType}`);
    return res.data;
  },
  logCognitiveSession: async (payload) => {
    const res = await axios.post(`${API_BASE}/cognitive/log-session`, payload);
    return res.data;
  },
  getGkQuestion: async () => {
    const res = await axios.get(`${API_BASE}/cognitive/questions/gk`);
    return res.data;
  },
  getAttentionQuestion: async () => {
    const res = await axios.get(`${API_BASE}/cognitive/questions/attention`);
    return res.data;
  },

  // Sarvam AI Voice
  voiceInteract: async (payload) => {
    const res = await axios.post(`${API_BASE}/voice/interact`, payload);
    return res.data;
  },

  // Caregiver Analytics
  getCaregiverAnalytics: async (patientId = 1) => {
    const res = await axios.get(`${API_BASE}/caregiver/analytics?patient_id=${patientId}`);
    return res.data;
  }
};
