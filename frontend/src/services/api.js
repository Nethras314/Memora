import axios from 'axios';
import { getSupabaseToken } from './supabase';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

let authToken = localStorage.getItem('memora_token') || '';

export function setAuthToken(token) {
  authToken = token || '';
  if (token) localStorage.setItem('memora_token', token);
  else localStorage.removeItem('memora_token');
}

export function getAuthToken() {
  return authToken;
}

async function authHeaders() {
  let token = authToken;
  if (!token) {
    try {
      token = (await getSupabaseToken()) || '';
      if (token) authToken = token;
    } catch {
      token = '';
    }
  }
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(method, url, data, config = {}) {
  const headers = { ...(config.headers || {}), ...(await authHeaders()) };
  const clientConfig = { ...config, headers };
  if (method === 'get' || method === 'delete') {
    return axios[method](`${API_BASE}${url}`, clientConfig);
  }
  return axios[method](`${API_BASE}${url}`, data, clientConfig);
}

export const api = {
  // Auth / users
  signup: async (payload) => {
    const res = await axios.post(`${API_BASE}/auth/signup`, payload);
    if (res.data?.access_token) setAuthToken(res.data.access_token);
    return res.data;
  },
  login: async (payload) => {
    const res = await axios.post(`${API_BASE}/auth/login`, payload);
    if (res.data?.access_token) setAuthToken(res.data.access_token);
    return res.data;
  },
  logout: () => setAuthToken(''),
  me: async () => {
    const res = await request('get', '/auth/me');
    return res.data;
  },
  linkPatient: async (patient_id) => {
    const res = await request('post', '/auth/link-patient', { patient_id });
    return res.data;
  },
  adminListUsers: async () => {
    const res = await request('get', '/auth/admin/users');
    return res.data;
  },
  adminCreateUser: async (payload) => {
    const res = await request('post', '/auth/admin/users', payload);
    return res.data;
  },
  adminOverview: async () => {
    const res = await request('get', '/caregiver/admin/overview');
    return res.data;
  },

  // Health
  checkHealth: async () => {
    const res = await axios.get(`${API_BASE}/health`);
    return res.data;
  },

  // Auth / PIN
  verifyPin: async (pin, patient_id) => {
    const res = await request('post', '/auth/verify-pin', { pin, patient_id });
    return res.data;
  },

  // Patients
  getPatients: async () => {
    const res = await request('get', '/patients');
    return res.data;
  },
  getPatient: async (id) => {
    const res = await request('get', `/patients/${id}`);
    return res.data;
  },
  createPatient: async (payload) => {
    const res = await request('post', '/patients', payload);
    return res.data;
  },

  // Memories
  getMemories: async (patientId = 1) => {
    const res = await request('get', `/memories?patient_id=${patientId}`);
    return res.data;
  },
  createMemory: async (formData) => {
    const res = await request('post', '/memories', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  updateMemory: async (memoryId, formData, patientId = 1) => {
    const res = await request('put', `/memories/${memoryId}?patient_id=${patientId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  deleteMemory: async (memoryId, patientId = 1) => {
    const res = await request('delete', `/memories/${memoryId}?patient_id=${patientId}`);
    return res.data;
  },

  // Routines & Reminders
  getTasks: async (patientId = 1) => {
    const res = await request('get', `/routines/tasks?patient_id=${patientId}`);
    return res.data;
  },
  createTask: async (taskData) => {
    const res = await request('post', '/routines/tasks', taskData);
    return res.data;
  },
  addTask: async (payload) => {
    const res = await request('post', '/routines/tasks', payload);
    return res.data;
  },
  toggleTask: async (taskId, patientId = 1) => {
    const res = await request('post', `/routines/tasks/${taskId}/toggle?patient_id=${patientId}`);
    return res.data;
  },
  deleteTask: async (taskId, patientId = 1) => {
    const res = await request('delete', `/routines/tasks/${taskId}?patient_id=${patientId}`);
    return res.data;
  },
  resetTasks: async (patientId = 1) => {
    const res = await request('post', `/routines/tasks/reset?patient_id=${patientId}`);
    return res.data;
  },
  getReminders: async (patientId = 1) => {
    const res = await request('get', `/routines/reminders?patient_id=${patientId}`);
    return res.data;
  },
  createReminder: async (reminderData) => {
    const res = await request('post', '/routines/reminders', reminderData);
    return res.data;
  },
  addReminder: async (payload) => {
    const res = await request('post', '/routines/reminders', payload);
    return res.data;
  },
  updateReminder: async (reminderId, reminderData, patientId = 1) => {
    const res = await request('put', `/routines/reminders/${reminderId}?patient_id=${patientId}`, reminderData);
    return res.data;
  },
  deleteReminder: async (reminderId, patientId = 1) => {
    const res = await request('delete', `/routines/reminders/${reminderId}?patient_id=${patientId}`);
    return res.data;
  },
  toggleReminder: async (reminderId, patientId = 1) => {
    const res = await request('post', `/routines/reminders/${reminderId}/toggle?patient_id=${patientId}`);
    return res.data;
  },
  toggleReminderEnabled: async (reminderId, patientId = 1) => {
    const res = await request('post', `/routines/reminders/${reminderId}/toggle-enabled?patient_id=${patientId}`);
    return res.data;
  },

  // Cognitive Engine & DDA
  getNextGame: async (patientId = 1, gameType = 'sequence_memory') => {
    const res = await request('get', `/cognitive/next-game?patient_id=${patientId}&game_type=${gameType}`);
    return res.data;
  },
  logCognitiveSession: async (payload) => {
    const res = await request('post', '/cognitive/log-session', payload);
    return res.data;
  },
  getGkQuestion: async () => {
    const res = await request('get', '/cognitive/questions/gk');
    return res.data;
  },
  getAttentionQuestion: async () => {
    const res = await request('get', '/cognitive/questions/attention');
    return res.data;
  },

  // Sarvam AI Voice
  voiceInteract: async (payload) => {
    const res = await request('post', '/voice/interact', payload);
    return res.data;
  },

  // Caregiver Analytics
  getCaregiverAnalytics: async (patientId = 1) => {
    const res = await request('get', `/caregiver/analytics?patient_id=${patientId}`);
    return res.data;
  },
};
