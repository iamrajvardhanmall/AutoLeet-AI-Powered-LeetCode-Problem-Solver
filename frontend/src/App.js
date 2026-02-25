/**
 * App.js
 * Root React component.
 * Sets up React Router with 3 routes:
 *   /          → HomePage  (enter problem number, solve)
 *   /history   → HistoryPage (see all solved problems)
 *   /result/:id → ResultPage (detail view for one problem)
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import HistoryPage from './pages/HistoryPage';
import ResultPage from './pages/ResultPage';

import './App.css';

function App() {
  return (
    <Router>
      {/* Navigation bar is always visible */}
      <Navbar />

      {/* Route definitions */}
      <Routes>
        <Route path="/"           element={<HomePage />} />
        <Route path="/history"    element={<HistoryPage />} />
        <Route path="/result/:id" element={<ResultPage />} />
      </Routes>
    </Router>
  );
}

export default App;
