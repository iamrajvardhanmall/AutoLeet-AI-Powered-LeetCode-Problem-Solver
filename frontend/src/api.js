/**
 * api.js
 * Centralised Axios configuration for all API calls.
 * Change BASE_URL here if backend runs on a different port.
 */

import axios from 'axios';

// Base URL of our Django backend
const BASE_URL = 'http://127.0.0.1:8000/api';

// Create an Axios instance with default settings
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes — Selenium + GPT can take a while
});

export default api;
