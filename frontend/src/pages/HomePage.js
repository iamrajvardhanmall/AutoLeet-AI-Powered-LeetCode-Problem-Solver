/**
 * HomePage.js
 *
 * Flow:
 *  1. On mount → check login status via GET /api/solver/login-status/
 *  2. If NOT logged in → show "Login to LeetCode" card
 *       Clicking "Open Login Browser" → POST /api/solver/start-login/
 *       (Chrome opens, user logs in manually, frontend waits)
 *  3. Once logged in → show the Solve card
 *       User enters problem number → POST /api/solver/solve/
 *       Selenium uses saved cookies to submit on LeetCode
 */

import React, { useState, useEffect } from 'react';
import api from '../api';
import Spinner from '../components/Spinner';

// ── Status badge helpers ──────────────────────────────────────────────────────

function getStatusClass(statusStr) {
  if (!statusStr) return 'status-pending';
  const s = statusStr.toLowerCase();
  if (s === 'accepted') return 'status-accepted';
  if (s === 'wrong_answer' || s === 'wrong answer') return 'status-wrong';
  if (s === 'tle' || s.includes('time limit')) return 'status-tle';
  return 'status-error';
}

function getStatusLabel(statusStr) {
  if (!statusStr) return 'Pending';
  const map = {
    accepted:     'Accepted ✅',
    wrong_answer: 'Wrong Answer ❌',
    tle:          'Time Limit Exceeded ⏱️',
    error:        'Error ⚠️',
    pending:      'Pending ⏳',
  };
  return map[statusStr.toLowerCase()] || statusStr;
}

// ── Component ─────────────────────────────────────────────────────────────────

function HomePage() {
  // ── Login state ──────────────────────────────────────────────────────────
  const [loggedIn,      setLoggedIn]      = useState(null);   // null = checking
  const [loginLoading,  setLoginLoading]  = useState(false);  // waiting for manual login
  const [loginError,    setLoginError]    = useState('');

  // ── Solve state ──────────────────────────────────────────────────────────
  const [problemNumber, setProblemNumber] = useState('');
  const [loading,       setLoading]       = useState(false);
  const [result,        setResult]        = useState(null);
  const [error,         setError]         = useState('');

  // ── Check login status on mount ──────────────────────────────────────────
  useEffect(() => {
    checkLoginStatus();
  }, []);

  const checkLoginStatus = async () => {
    try {
      const res = await api.get('/solver/login-status/');
      setLoggedIn(res.data.logged_in);
    } catch {
      setLoggedIn(false);
    }
  };

  // ── Open browser for manual LeetCode login ────────────────────────────────
  const handleLogin = async () => {
    setLoginError('');
    setLoginLoading(true);
    try {
      // This call blocks on the backend until the user finishes logging in
      const res = await api.post('/solver/start-login/');
      if (res.data.success) {
        setLoggedIn(true);
      } else {
        setLoginError(res.data.error || 'Login failed. Please try again.');
      }
    } catch (err) {
      setLoginError(
        err.response?.data?.error || 'Could not open login browser. Is the backend running?'
      );
    } finally {
      setLoginLoading(false);
    }
  };

  // ── Logout ────────────────────────────────────────────────────────────────
  const handleLogout = async () => {
    try {
      await api.post('/solver/logout/');
    } catch { /* ignore */ }
    setLoggedIn(false);
    setResult(null);
    setError('');
  };

  // ── Solve a problem ───────────────────────────────────────────────────────
  const handleSolve = async () => {
    if (!problemNumber || problemNumber < 1) {
      setError('Please enter a valid problem number (e.g., 1).');
      return;
    }
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const response = await api.post('/solver/solve/', {
        problem_number: parseInt(problemNumber),
      });
      setResult(response.data);
    } catch (err) {
      const msg = err.response?.data?.error || 'Something went wrong. Is the backend running?';
      // If session expired, update login state
      if (err.response?.status === 401) {
        setLoggedIn(false);
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // ── Render: checking status ───────────────────────────────────────────────
  if (loggedIn === null) {
    return (
      <div className="container">
        <div className="card">
          <Spinner message="Checking LeetCode login status..." />
        </div>
      </div>
    );
  }

  // ── Render: not logged in ─────────────────────────────────────────────────
  if (!loggedIn) {
    return (
      <div className="container">
        <div className="card login-card">
          <div className="login-icon">🔐</div>
          <h2>Login to LeetCode</h2>
          <p className="login-description">
            To solve and auto-submit problems, you need to log in to your LeetCode account first.
            Click the button below — a Chrome browser window will open so you can log in manually.
            Once you log in, this page will automatically proceed.
          </p>

          {loginLoading ? (
            <Spinner message="Browser opened — please log in to LeetCode in the Chrome window... (timeout: 3 min)" />
          ) : (
            <button
              className="btn btn-primary btn-login"
              onClick={handleLogin}
              disabled={loginLoading}
            >
              🌐 Open LeetCode Login Browser
            </button>
          )}

          {loginError && <div className="error-msg" style={{ marginTop: '16px' }}>{loginError}</div>}
        </div>
      </div>
    );
  }

  // ── Render: logged in → show solve form ──────────────────────────────────
  return (
    <div className="container">

      {/* ── Session Banner ── */}
      <div className="session-banner">
        <span className="session-dot">●</span>
        <span>Logged in to LeetCode</span>
        <button className="btn-logout" onClick={handleLogout}>Logout</button>
      </div>

      {/* ── Input Card ── */}
      <div className="card">
        <h2>Solve a LeetCode Problem</h2>
        <p style={{ marginBottom: '16px', color: '#aaa', fontSize: '0.9rem' }}>
          Enter the problem number and click Solve. The system will scrape the problem,
          generate a Python solution using GPT, and auto-submit it to LeetCode using your session.
        </p>

        <div className="input-group">
          <input
            type="number"
            placeholder="Problem # (e.g. 1)"
            value={problemNumber}
            onChange={(e) => setProblemNumber(e.target.value)}
            min="1"
            disabled={loading}
          />
          <button
            className="btn btn-primary"
            onClick={handleSolve}
            disabled={loading}
          >
            {loading ? 'Solving...' : '⚡ Solve'}
          </button>
        </div>

        {error && <div className="error-msg">{error}</div>}
      </div>

      {/* ── Loading Spinner ── */}
      {loading && (
        <div className="card">
          <Spinner message="Running Selenium + GPT pipeline... This may take 2–4 minutes." />
        </div>
      )}

      {/* ── Result Card ── */}
      {result && !loading && (
        <div className="card result-section">

          {result.cached && (
            <p className="cached-notice">⚡ Retrieved from cache (already solved)</p>
          )}

          <h2>#{result.problem_number} — {result.title}</h2>
          <hr className="divider" />

          <h3>Submission Result</h3>
          <span className={`status-badge ${getStatusClass(result.submission_status)}`}>
            {getStatusLabel(result.submission_status)}
          </span>

          <hr className="divider" />

          <h3>Generated Python Code</h3>
          <div className="code-block">
            <pre>{result.generated_code}</pre>
          </div>

          <hr className="divider" />

          <h3>Problem Description</h3>
          <div className="description-box">
            {result.description}
          </div>
        </div>
      )}

    </div>
  );
}

export default HomePage;

