import React from 'react';

const LoadingSpinner = ({ active, message }) => {
  if (!active) return null;
  
  return (
    <div className="loading-overlay active">
      <div className="text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <div className="loading-text">{message}</div>
      </div>
    </div>
  );
};

export default LoadingSpinner;