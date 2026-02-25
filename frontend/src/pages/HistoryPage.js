/**
 * HistoryPage.js
 *
 * Shows a table of all previously solved problems.
 * Fetches data from GET /api/dashboard/history/
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import Spinner from '../components/Spinner';

function HistoryPage() {
  const [history, setHistory] = useState([]);    // List of problems
  const [loading, setLoading] = useState(true);  // Loading state
  const [error, setError] = useState('');

  const navigate = useNavigate();

  // Fetch history when component mounts
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await api.get('/dashboard/history/');
      setHistory(response.data);
    } catch (err) {
      setError('Failed to load history. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  // Get the latest solution status for a problem
  const getLatestStatus = (solutions) => {
    if (!solutions || solutions.length === 0) return 'N/A';
    // solutions are ordered by created_at in serializer
    return solutions[solutions.length - 1].submission_status;
  };

  const statusLabel = {
    accepted: '✅ Accepted',
    wrong_answer: '❌ Wrong Answer',
    tle: '⏱️ TLE',
    error: '⚠️ Error',
    pending: '⏳ Pending',
  };

  return (
    <div className="container">
      <div className="card">
        <h2>Solved Problems History</h2>
        <p style={{ color: '#aaa', fontSize: '0.9rem', marginBottom: '20px' }}>
          All problems that have been processed by the auto-solver.
        </p>

        {/* Loading */}
        {loading && <Spinner message="Loading history..." />}

        {/* Error */}
        {error && <div className="error-msg">{error}</div>}

        {/* No data */}
        {!loading && !error && history.length === 0 && (
          <p style={{ color: '#aaa' }}>No problems solved yet. Go to Home and solve one!</p>
        )}

        {/* History table */}
        {!loading && history.length > 0 && (
          <table className="history-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Problem No.</th>
                <th>Title</th>
                <th>Status</th>
                <th>Solved At</th>
              </tr>
            </thead>
            <tbody>
              {history.map((problem, index) => {
                const latestStatus = getLatestStatus(problem.solutions);
                return (
                  <tr
                    key={problem.id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/result/${problem.id}`)}
                    title="Click to view details"
                  >
                    <td>{index + 1}</td>
                    <td>{problem.problem_number}</td>
                    <td>{problem.title}</td>
                    <td>{statusLabel[latestStatus] || latestStatus}</td>
                    <td>{new Date(problem.created_at).toLocaleString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default HistoryPage;
