import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dashboardAPI, interviewAPI } from '../services/api';

const Dashboard = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const response = await dashboardAPI.getAnswersHistory();
      setHistory(response.data);
      setLoading(false);
    } catch (err) {
      setError('Gagal memuat data dashboard: ' + (err.response?.data?.message || err.message));
      setLoading(false);
    }
  };

  const getScoreBadgeClass = (score) => {
    if (score >= 8) return 'score-high';
    if (score >= 6) return 'score-medium';
    return 'score-low';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-2">Memuat data dashboard...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Dashboard Hasil Interview</h2>
        <Link to="/interview" className="btn btn-primary">
          Mulai Interview Baru
        </Link>
      </div>
      
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}
      
      {/* Summary Cards */}
      <div className="row mb-4">
        <div className="col-md-3 mb-3">
          <div className="card bg-primary text-white">
            <div className="card-body">
              <h6 className="card-title">Total Sesi</h6>
              <h3 className="mb-0">{history.length}</h3>
            </div>
          </div>
        </div>
        
        <div className="col-md-3 mb-3">
          <div className="card bg-success text-white">
            <div className="card-body">
              <h6 className="card-title">Rata-rata Skor</h6>
              <h3 className="mb-0">
                {history.length > 0 
                  ? (history.reduce((sum, item) => sum + (item.clarity_score || 0), 0) / history.length).toFixed(1)
                  : '0.0'}
              </h3>
            </div>
          </div>
        </div>
        
        <div className="col-md-3 mb-3">
          <div className="card bg-info text-white">
            <div className="card-body">
              <h6 className="card-title">Pertanyaan Dijawab</h6>
              <h3 className="mb-0">{history.length}</h3>
            </div>
          </div>
        </div>
        
        <div className="col-md-3 mb-3">
          <div className="card bg-warning text-white">
            <div className="card-body">
              <h6 className="card-title">Sesi Terakhir</h6>
              <h3 className="mb-0">
                {history.length > 0 
                  ? formatDate(history[0]?.created_at)
                  : '-'}
              </h3>
            </div>
          </div>
        </div>
      </div>
      
      {/* Recent Sessions */}
      <div className="card">
        <div className="card-header">
          <h5 className="mb-0">Riwayat Interview</h5>
        </div>
        <div className="card-body">
          {history.length === 0 ? (
            <div className="text-center py-4">
              <p className="text-muted">Belum ada sesi interview yang diselesaikan.</p>
              <Link to="/interview" className="btn btn-primary">Mulai Interview</Link>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover">
                <thead>
                  <tr>
                    <th>Tanggal</th>
                    <th>Pertanyaan</th>
                    <th>Skor Kejelasan</th>
                    <th>Skor Struktur</th>
                    <th>Skor Keyakinan</th>
                    <th>Status</th>
                    <th>Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item) => (
                    <tr key={item.answer_id}>
                      <td>{formatDate(item.created_at)}</td>
                      <td>{item.question_text.substring(0, 50)}...</td>
                      <td>
                        {item.clarity_score ? (
                          <span className={`score-badge ${getScoreBadgeClass(item.clarity_score)}`}>
                            {item.clarity_score}
                          </span>
                        ) : (
                          <span className="badge bg-secondary">Processing</span>
                        )}
                      </td>
                      <td>
                        {item.structure_score ? (
                          <span className={`score-badge ${getScoreBadgeClass(item.structure_score)}`}>
                            {item.structure_score}
                          </span>
                        ) : (
                          <span className="badge bg-secondary">Processing</span>
                        )}
                      </td>
                      <td>
                        {item.confidence_score ? (
                          <span className={`score-badge ${getScoreBadgeClass(item.confidence_score)}`}>
                            {item.confidence_score}
                          </span>
                        ) : (
                          <span className="badge bg-secondary">Processing</span>
                        )}
                      </td>
                      <td>
                        {item.transcript_text ? (
                          <span className="badge bg-success">Selesai</span>
                        ) : (
                          <span className="badge bg-warning">Processing</span>
                        )}
                      </td>
                      <td>
                        <Link 
                          to={`/answer/${item.answer_id}`} 
                          className="btn btn-sm btn-outline-primary"
                        >
                          Detail
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;