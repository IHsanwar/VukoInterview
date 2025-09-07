import React from 'react';
import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <div className="row">
      <div className="col-12">
        <div className="jumbotron bg-light p-5 rounded">
          <h1 className="display-4">Vuko Interview</h1>
          <p className="lead">
            Persiapkan interview Anda dengan AI Interview Simulator yang membantu 
            merekam jawaban dan memberikan feedback.
          </p>
          <hr className="my-4" />
          <p>
            Platform lengkap untuk persiapan interview kerja dengan simulasi 
            realistis dan analisis AI.
          </p>
          
          {!isAuthenticated() ? (
            <div className="mt-4">
              <Link className="btn btn-primary btn-lg me-2" to="/register">
                Mulai Sekarang
              </Link>
              <Link className="btn btn-outline-primary btn-lg" to="/login">
                Login
              </Link>
            </div>
          ) : (
            <div className="mt-4">
              <Link className="btn btn-primary btn-lg" to="/interview">
                Mulai Interview
              </Link>
            </div>
          )}
        </div>
      </div>
      
      <div className="col-12 mt-5">
        <div className="row">
          <div className="col-md-4 mb-4">
            <div className="card h-100">
              <div className="card-body text-center">
                <h5 className="card-title">
                  <span className="badge bg-primary">1</span> Rekam Jawaban
                </h5>
                <p className="card-text">
                  Rekam jawaban Anda dengan audio dan dapatkan transkrip otomatis.
                </p>
              </div>
            </div>
          </div>
          
          <div className="col-md-4 mb-4">
            <div className="card h-100">
              <div className="card-body text-center">
                <h5 className="card-title">
                  <span className="badge bg-primary">2</span> AI Feedback
                </h5>
                <p className="card-text">
                  Dapatkan feedback dan penilaian dari AI untuk meningkatkan jawaban Anda.
                </p>
              </div>
            </div>
          </div>
          
          <div className="col-md-4 mb-4">
            <div className="card h-100">
              <div className="card-body text-center">
                <h5 className="card-title">
                  <span className="badge bg-primary">3</span> Dashboard Hasil
                </h5>
                <p className="card-text">
                  Lihat riwayat dan perkembangan Anda melalui dashboard yang informatif.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function
const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};

export default Home;