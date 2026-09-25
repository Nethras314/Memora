import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const API_BASE = process.env.EXPO_PUBLIC_API_URL || 'http://192.168.1.5:8000/api';
const TOKEN_KEY = 'memora_token';

async function getToken() {
  try {
    return (await SecureStore.getItemAsync(TOKEN_KEY)) || '';
  } catch {
    return '';
  }
}

export async function setToken(token) {
  try {
    if (token) await SecureStore.setItemAsync(TOKEN_KEY, token);
    else await SecureStore.deleteItemAsync(TOKEN_KEY);
  } catch {}
}

async function headers(extra = {}) {
  const token = await getToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : { ...extra };
}

async function req(method, url, data, config = {}) {
  const h = await headers(config.headers);
  const full = `${API_BASE}${url}`;
  if (method === 'get' || method === 'delete') return (await axios[method](full, { ...config, headers: h })).data;
  return (await axios[method](full, data, { ...config, headers: h })).data;
}

export const api = {
  signup: async (payload) => {
    const res = await axios.post(`${API_BASE}/auth/signup`, payload);
    if (res.data?.access_token) await setToken(res.data.access_token);
    return res.data;
  },
  login: async (payload) => {
    const res = await axios.post(`${API_BASE}/auth/login`, payload);
    if (res.data?.access_token) await setToken(res.data.access_token);
    return res.data;
  },
  logout: () => setToken(''),
  me: () => req('get', '/auth/me'),
  verifyPin: (pin, patient_id) => req('post', '/auth/verify-pin', { pin, patient_id }),

  getPatients: () => req('get', '/patients'),

  getMemories: (patientId = 1) => req('get', `/memories?patient_id=${patientId}`),
  createMemory: (formData) => req('post', '/memories', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  updateMemory: (id, formData, patientId = 1) =>
    req('put', `/memories/${id}?patient_id=${patientId}`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  deleteMemory: (id, patientId = 1) => req('delete', `/memories/${id}?patient_id=${patientId}`),

  getTasks: (patientId = 1) => req('get', `/routines/tasks?patient_id=${patientId}`),
  createTask: (payload) => req('post', '/routines/tasks', payload),
  toggleTask: (id, patientId = 1) => req('post', `/routines/tasks/${id}/toggle?patient_id=${patientId}`),
  deleteTask: (id, patientId = 1) => req('delete', `/routines/tasks/${id}?patient_id=${patientId}`),
  resetTasks: (patientId = 1) => req('post', `/routines/tasks/reset?patient_id=${patientId}`),

  getReminders: (patientId = 1) => req('get', `/routines/reminders?patient_id=${patientId}`),
  createReminder: (payload) => req('post', '/routines/reminders', payload),
  updateReminder: (id, payload, patientId = 1) => req('put', `/routines/reminders/${id}?patient_id=${patientId}`, payload),
  deleteReminder: (id, patientId = 1) => req('delete', `/routines/reminders/${id}?patient_id=${patientId}`),
  toggleReminder: (id, patientId = 1) => req('post', `/routines/reminders/${id}/toggle?patient_id=${patientId}`),
  toggleReminderEnabled: (id, patientId = 1) => req('post', `/routines/reminders/${id}/toggle-enabled?patient_id=${patientId}`),

  getNextGame: (patientId = 1, gameType = 'sequence_memory') =>
    req('get', `/cognitive/next-game?patient_id=${patientId}&game_type=${gameType}`),
  logCognitiveSession: (payload) => req('post', '/cognitive/log-session', payload),
  getGkQuestion: () => req('get', '/cognitive/questions/gk'),
  getAttentionQuestion: () => req('get', '/cognitive/questions/attention'),

  voiceInteract: (payload) => req('post', '/voice/interact', payload),
  getProgress: (patientId = 1) => req('get', `/caregiver/analytics?patient_id=${patientId}`),
};
