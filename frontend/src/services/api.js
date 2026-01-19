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

// Google OAuth API calls
export const googleAPI = {
  getAuthUrl: () =>
    api.get('/google/auth-url'),
  
  handleCallback: (code) =>
    api.post('/google/callback', { code }),
  
  connectAccount: (code) =>
    api.post('/google/connect', { code }),
  
  disconnectAccount: () =>
    api.post('/google/disconnect'),
  
  getConnectionStatus: () =>
    api.get('/google/status'),
};

// Gmail API calls
export const gmailAPI = {
  getEmails: (maxResults = 10, query = '') =>
    api.get('/gmail/emails', { params: { max_results: maxResults, query } }),
  
  getEmailDetails: (messageId) =>
    api.get(`/gmail/emails/${messageId}`),
  
  searchEmails: (query, maxResults = 10) =>
    api.post('/gmail/search', { query, max_results: maxResults }),
  
  sendEmail: (to, subject, body) =>
    api.post('/gmail/send', { to, subject, body }),
};

// Calendar API calls
export const calendarAPI = {
  getCalendars: () =>
    api.get('/calendar/calendars'),
  
  getEvents: (maxResults = 10, calendarId = 'primary') =>
    api.get('/calendar/events', { params: { max_results: maxResults, calendar_id: calendarId } }),
  
  getTodayEvents: (calendarId = 'primary') =>
    api.get('/calendar/events/today', { params: { calendar_id: calendarId } }),
  
  getWeekEvents: (calendarId = 'primary') =>
    api.get('/calendar/events/week', { params: { calendar_id: calendarId } }),
  
  searchEvents: (query, maxResults = 25, calendarId = 'primary') =>
    api.post('/calendar/search', { query, max_results: maxResults, calendar_id: calendarId }),
};

// Chat API calls
export const chatAPI = {
  sendMessage: (message) =>
    api.post('/chat/message', { message }),
  
  sendMessageWithTools: (message) =>
    api.post('/chat/message/tools', { message }),
  
  getHistory: (limit = 50) =>
    api.get('/chat/history', { params: { limit } }),
  
  clearHistory: () =>
    api.delete('/chat/history'),
};

export default api;