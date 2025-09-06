import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { interviewAPI } from '../services/api';

const Interview = () => {
  const [sessionId, setSessionId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState('');
  const videoChunksRef = useRef([]);
  const mediaRecorderRef = useRef(null);
  const timerRef = useRef(null);
  const navigate = useNavigate();
  const webcamRef = useRef(null);

  // Start new session
  useEffect(() => {
    startNewSession();

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Start webcam
  useEffect(() => {
    const startWebcam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { width: 640, height: 480 }, 
          audio: true 
        });
        if (webcamRef.current) {
          webcamRef.current.srcObject = stream;
        }
        console.log('Webcam stream ready');
      } catch (err) {
        console.error("Error accessing webcam:", err);
        setError("Tidak bisa mengakses kamera: " + err.message);
      }
    };

    startWebcam();

    return () => {
      if (webcamRef.current && webcamRef.current.srcObject) {
        const tracks = webcamRef.current.srcObject.getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, []);

  const startNewSession = async () => {
    try {
      const rolesResponse = await interviewAPI.getRoles();
      const roleId = rolesResponse.data[0]?.id || 1;
      
      const sessionResponse = await interviewAPI.startSession({ role_id: roleId });
      setSessionId(sessionResponse.data.session_id);
      
      await loadQuestions(sessionResponse.data.session_id);
    } catch (err) {
      setError('Gagal memulai sesi interview: ' + (err.response?.data?.message || err.message));
    }
  };

  const loadQuestions = async (sessionId) => {
    try {
      const response = await interviewAPI.getQuestions(sessionId);
      setQuestions(response.data);
    } catch (err) {
      setError('Gagal memuat pertanyaan: ' + (err.response?.data?.message || err.message));
    }
  };

  // Fungsi untuk menunggu stream tersedia
  const waitForStream = () => {
    return new Promise((resolve, reject) => {
      let attempts = 0;
      const maxAttempts = 50; // 5 detik (50 * 100ms)
      
      const checkStream = () => {
        attempts++;
        if (webcamRef.current && webcamRef.current.srcObject instanceof MediaStream) {
          console.log('Stream found after', attempts, 'attempts');
          resolve(webcamRef.current.srcObject);
        } else if (attempts >= maxAttempts) {
          reject(new Error('Stream tidak tersedia setelah menunggu'));
        } else {
          setTimeout(checkStream, 100);
        }
      };
      
      checkStream();
    });
  };

  const startRecording = async () => {
    try {
      console.log('Starting recording process...');
      
      // Tunggu stream tersedia
      let stream;
      try {
        stream = await waitForStream();
        console.log('Stream acquired:', stream);
      } catch (waitError) {
        // Fallback: coba dapatkan stream langsung
        if (webcamRef.current && webcamRef.current.srcObject instanceof MediaStream) {
          stream = webcamRef.current.srcObject;
          console.log('Using direct stream');
        } else {
          throw new Error('Stream kamera belum tersedia');
        }
      }

      // Validasi stream
      if (!stream || !(stream instanceof MediaStream)) {
        throw new Error('Stream tidak valid');
      }

      // Reset chunks
      videoChunksRef.current = [];
      
      // Cek MIME type yang didukung
      const mimeType = getSupportedMimeType();
      
      // Buat MediaRecorder
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });

      // Event handlers
      mediaRecorderRef.current.ondataavailable = (event) => {
        console.log('Data available:', event.data.size);
        if (event.data.size > 0) {
          videoChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        console.log('Recorder stopped, chunks length:', videoChunksRef.current.length);
        uploadRecording();
      };

      mediaRecorderRef.current.onerror = (event) => {
        console.error('Recorder error:', event.error);
        setError('Error saat merekam: ' + event.error.message);
      };

      // Start recording dengan time slice 1 detik
      mediaRecorderRef.current.start(1000);
      setIsRecording(true);
      startTimer();
      
      console.log('Recording started with MIME type:', mimeType);
    } catch (err) {
      console.error('Start recording error:', err);
      setError("Gagal merekam: " + err.message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      console.log('Stopping recording...');
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const startTimer = () => {
    setSeconds(0);
    timerRef.current = setInterval(() => {
      setSeconds(prev => prev + 1);
    }, 1000);
  };

  const uploadRecording = async () => {
    console.log('Upload recording called, chunks:', videoChunksRef.current.length);
    
    if (videoChunksRef.current.length === 0) {
      setError("Tidak ada data untuk diunggah.");
      return;
    }

    try {
      // Buat blob dari chunks
      const videoBlob = new Blob(videoChunksRef.current, { type: 'video/webm' });
      console.log('Blob size:', videoBlob.size);
      
      if (videoBlob.size === 0) {
        setError("File rekaman kosong.");
        return;
      }

      // Buat FormData
      const formData = new FormData();
      formData.append('video', videoBlob, 'recording.webm');
      formData.append('session_id', sessionId);
      formData.append('question_id', questions[currentQuestionIndex].id);
      
      console.log('Uploading file size:', videoBlob.size);
      console.log('Session ID:', sessionId);
      console.log('Question ID:', questions[currentQuestionIndex].id);

      // Upload ke backend
      const response = await interviewAPI.uploadAnswer(formData);
      console.log('Upload response:', response.data);
      
      alert('Jawaban berhasil disimpan!');
    } catch (err) {
      console.error('Upload error:', err);
      setError('Gagal mengunggah jawaban: ' + (err.response?.data?.message || err.message));
    }
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setSeconds(0);
    } else {
      alert('Interview selesai!');
      navigate('/dashboard');
    }
  };

  // Helper function untuk mendapatkan MIME type yang didukung
  const getSupportedMimeType = () => {
    const mimeTypes = [
      'video/webm; codecs=vp9',
      'video/webm; codecs=vp8',
      'video/webm'
    ];
    
    for (let type of mimeTypes) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    
    // Fallback ke default
    return 'video/webm';
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!sessionId || questions.length === 0) {
    return (
      <div className="text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-2">Memuat sesi interview...</p>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Interview Session</h2>
        <div className="timer badge bg-primary fs-6 p-2">
          {formatTime(seconds)}
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <div className="question-card mb-4">
        <h4>
          Pertanyaan {currentQuestionIndex + 1} dari {questions.length}
        </h4>
        <p className="lead mt-3">{currentQuestion.question_text}</p>
      </div>

      <div className="card mb-4">
        <div className="card-body">
          <h5 className="card-title">Rekam Jawaban Anda</h5>
          <p className="text-muted">
            Klik tombol di bawah untuk mulai merekam jawaban Anda.
          </p>

          <div className="recording-controls mb-3 d-flex gap-2">
            <button
              className="btn btn-primary"
              onClick={startRecording}
              disabled={isRecording}
            >
              <i className="bi bi-mic"></i> Mulai Rekam
            </button>

            <button
              className="btn btn-danger"
              onClick={stopRecording}
              disabled={!isRecording}
            >
              <i className="bi bi-stop-fill"></i> Stop Rekam
            </button>

            <button
              className="btn btn-success"
              onClick={nextQuestion}
              disabled={isRecording}
            >
              <i className="bi bi-arrow-right"></i> Pertanyaan Berikutnya
            </button>
          </div>

          {isRecording && (
            <div className="alert alert-info">
              <div className="d-flex align-items-center">
                <div className="spinner-grow spinner-grow-sm me-2" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <span>Sedang merekam... Berbicaralah sekarang.</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Webcam Preview */}
      <div className="text-center">
        <h5 className="mb-3">Kamera Anda</h5>
        <video
          ref={webcamRef}
          autoPlay
          playsInline
          muted
          style={{
            width: "100%",
            maxWidth: "600px",
            height: "auto",
            border: "2px solid #ccc",
            borderRadius: "10px",
            backgroundColor: "#000"
          }}
        />
      </div>
    </div>
  );
};

export default Interview;