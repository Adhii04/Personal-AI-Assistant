import axios from 'axios';

// Base URL - change this when deploying
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if it exists
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  register: (email, password) =>
    api.post('/auth/register', { email, password }),
  
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  
  refresh: () =>
    api.post('/auth/refresh'),
};

// Chat API calls
export const chatAPI = {
  sendMessage: (message) =>
    api.post('/chat/message', { message }),
  
  getHistory: (limit = 50) =>
    api.get('/chat/history', { params: { limit } }),
  
  clearHistory: () =>
    api.delete('/chat/history'),
};

export default api;