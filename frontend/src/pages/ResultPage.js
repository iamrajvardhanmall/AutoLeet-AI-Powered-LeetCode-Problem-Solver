/**
 * ResultPage.js
 *
 * Shows the full detail of a single solved problem.
 * Accessed by clicking a row in the history table.
 * URL: /result/:id
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';
import Spinner from '../components/Spinner';

function ResultPage() {
  const { id } = useParams();            // Problem DB id from URL
  const navigate = useNavigate();

  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProblemDetail();
  }, [id]);

  const fetchProblemDetail = async () => {
    try {
      const response = await api.get(`/dashboard/history/${id}/`);
      setProblem(response.data);
    } catch (err) {
      setError('Problem not found or server error.');
    } finally {
      setLoading(false);
    }
  };

  const statusLabel = {
    accepted: 'Accepted ✅',
    wrong_answer: 'Wrong Answer ❌',
    tle: 'Time Limit Exceeded ⏱️',
    error: 'Error ⚠️',
    pending: 'Pending ⏳',
  };

  const getStatusClass = (s) => {
    if (s === 'accepted') return 'status-accepted';
    if (s === 'wrong_answer') return 'status-wrong';
    if (s === 'tle') return 'status-tle';
    return 'status-error';
  };

  return (
    <div className="container">

      {/* Back button */}
      <button
        className="btn btn-secondary"
        onClick={() => navigate('/history')}
        style={{ marginBottom: '20px' }}
      >
        ← Back to History
      </button>

      {loading && <div className="card"><Spinner message="Loading..." /></div>}
      {error && <div className="error-msg">{error}</div>}

      {problem && !loading && (
        <div className="card result-section">
          <h2>#{problem.problem_number} — {problem.title}</h2>
          <p style={{ color: '#aaa', fontSize: '0.85rem', marginBottom: '15px' }}>
            Scraped on: {new Date(problem.created_at).toLocaleString()}
          </p>
          <hr className="divider" />

          {/* All solutions for this problem */}
          {problem.solutions.map((solution, idx) => (
            <div key={solution.id} style={{ marginBottom: '25px' }}>
              <h3>Solution #{idx + 1}</h3>
              <span className={`status-badge ${getStatusClass(solution.submission_status)}`}>
                {statusLabel[solution.submission_status] || solution.submission_status}
              </span>
              <p style={{ color: '#aaa', fontSize: '0.8rem', marginBottom: '10px' }}>
                {new Date(solution.created_at).toLocaleString()}
              </p>
              <div className="code-block">
                <pre>{solution.generated_code}</pre>
              </div>
            </div>
          ))}

          <hr className="divider" />

          {/* Problem description */}
          <h3>Problem Description</h3>
          <div className="description-box" style={{ marginTop: '10px' }}>
            {problem.description}
          </div>
        </div>
      )}
    </div>
  );
}

export default ResultPage;
