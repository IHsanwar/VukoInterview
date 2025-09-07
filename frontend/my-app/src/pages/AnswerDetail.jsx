import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios'; // pakai axios langsung

const AnswerDetail = () => {
  const { id } = useParams();
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadAnswerDetail();
  }, [id]);

  const loadAnswerDetail = async () => {
    try {
      setLoading(true);

      // ambil token JWT dari localStorage (sesuai setup auth lo)
      const token = localStorage.getItem("token");

      const response = await axios.get(
        `http://localhost:5000/api/dashboard/answers/${id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      setAnswer(response.data);
      setLoading(false);
    } catch (err) {
      setError(
        'Gagal memuat detail jawaban: ' +
          (err.response?.data?.message || err.message)
      );
      setLoading(false);
    }
  };

  const getScoreBadgeClass = (score) => {
    if (score >= 8) return 'score-high';
    if (score >= 6) return 'score-medium';
    return 'score-low';
  };

  // ... sisanya tetap sama persis

  if (loading) {
    return (
      <div className="text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-2">Memuat detail jawaban...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        {error}
        <button 
          className="btn btn-primary ms-3" 
          onClick={() => navigate('/dashboard')}
        >
          Kembali ke Dashboard
        </button>
      </div>
    );
  }

  if (!answer) {
    return (
      <div className="alert alert-warning" role="alert">
        Data jawaban tidak ditemukan.
        <button 
          className="btn btn-primary ms-3" 
          onClick={() => navigate('/dashboard')}
        >
          Kembali ke Dashboard
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Detail Jawaban Interview</h2>
        <button 
          className="btn btn-secondary" 
          onClick={() => navigate('/dashboard')}
        >
          Kembali
        </button>
      </div>
      
      <div className="row">
        <div className="col-md-8">
          <div className="card mb-4">
            <div className="card-header">
              <h5 className="mb-0">Transkrip Jawaban</h5>
            </div>
            <div className="card-body">
              {answer.transcript_text ? (
                <p className="mb-0">{answer.transcript_text}</p>
              ) : (
                <p className="text-muted">Transkrip belum tersedia. Proses sedang berjalan...</p>
              )}
            </div>
          </div>
          
          <div className="card mb-4">
            <div className="card-header">
              <h5 className="mb-0">Ringkasan</h5>
            </div>
            <div className="card-body">
              {answer.summary ? (
                <p className="mb-0">{answer.summary}</p>
              ) : (
                <p className="text-muted">Ringkasan belum tersedia. Proses sedang berjalan...</p>
              )}
            </div>
          </div>
          
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">Feedback AI</h5>
            </div>
            <div className="card-body">
              {answer.feedback ? (
                <pre className="mb-0" style={{whiteSpace: 'pre-wrap'}}>{answer.feedback}</pre>
              ) : (
                <p className="text-muted">Feedback belum tersedia. Proses sedang berjalan...</p>
              )}
            </div>
          </div>
        </div>
        
        <div className="col-md-4">
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">Evaluasi</h5>
            </div>
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <span>Kejelasan:</span>
                {answer.clarity_score ? (
                  <span className={`score-badge ${getScoreBadgeClass(answer.clarity_score)}`}>
                    {answer.clarity_score}/10
                  </span>
                ) : (
                  <span className="badge bg-secondary">Processing</span>
                )}
              </div>
              
              <div className="d-flex justify-content-between align-items-center mb-3">
                <span>Struktur:</span>
                {answer.structure_score ? (
                  <span className={`score-badge ${getScoreBadgeClass(answer.structure_score)}`}>
                    {answer.structure_score}/10
                  </span>
                ) : (
                  <span className="badge bg-secondary">Processing</span>
                )}
              </div>
              
              <div className="d-flex justify-content-between align-items-center">
                <span>Keyakinan:</span>
                {answer.confidence_score ? (
                  <span className={`score-badge ${getScoreBadgeClass(answer.confidence_score)}`}>
                    {answer.confidence_score}/10
                  </span>
                ) : (
                  <span className="badge bg-secondary">Processing</span>
                )}
              </div>
              
              <hr />
              
              <div className="text-muted">
                <small>
                  Dibuat pada: {new Date(answer.created_at).toLocaleString('id-ID')}
                </small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnswerDetail;