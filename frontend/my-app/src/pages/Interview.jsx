import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { interviewAPI } from "../services/api";

const Interview = () => {
  const [sessionId, setSessionId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState("");
  const [initialized, setInitialized] = useState(false);
  const [faceWarning, setFaceWarning] = useState("");
  const [cameraStarted, setCameraStarted] = useState(false);

  const videoChunksRef = useRef([]);
  const mediaRecorderRef = useRef(null);
  const timerRef = useRef(null);
  const streamRef = useRef(null);
  const webcamRef = useRef(null);

  const navigate = useNavigate();

  // --- Start webcam function ---
  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: true,
      });

      if (webcamRef.current) {
        webcamRef.current.srcObject = stream;
        await webcamRef.current.play().catch((err) => {
          console.error("Video play error:", err);
        });
      }

      streamRef.current = stream;
      setCameraStarted(true);
      console.log("Webcam started");
    } catch (err) {
      console.error("Error accessing webcam:", err);
      setError("Tidak bisa mengakses kamera: " + err.message);
    }
  };

  // --- Cleanup kamera saat unmount ---
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // --- Start new session ---
  const startNewSession = async () => {
    try {
      const rolesResponse = await interviewAPI.getRoles();
      const roleId = rolesResponse.data[0]?.id || 1;

      const sessionResponse = await interviewAPI.startSession({
        role_id: roleId,
      });
      setSessionId(sessionResponse.data.session_id);

      await loadQuestions(sessionResponse.data.session_id);
    } catch (err) {
      setError(
        "Gagal memulai sesi interview: " +
          (err.response?.data?.message || err.message)
      );
    }
  };

  const loadQuestions = async (sessionId) => {
    try {
      const response = await interviewAPI.getQuestions(sessionId);
      setQuestions(response.data);
    } catch (err) {
      setError(
        "Gagal memuat pertanyaan: " +
          (err.response?.data?.message || err.message)
      );
    }
  };

  // --- Init session ---
  useEffect(() => {
    if (!initialized) {
      startNewSession();
      setInitialized(true);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [initialized]);

  // --- Recording ---
  const startRecording = async () => {
    try {
      let stream = streamRef.current;
      if (!stream) throw new Error("Stream kamera belum tersedia");

      videoChunksRef.current = [];
      const mimeType = getSupportedMimeType();
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          videoChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        uploadRecording();
      };

      mediaRecorderRef.current.start(1000);
      setIsRecording(true);
      startTimer();
    } catch (err) {
      console.error("Start recording error:", err);
      setError("Gagal merekam: " + err.message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  // --- Face capture ---
  const captureFace = async () => {
    if (!webcamRef.current) {
      alert("Webcam belum siap");
      return;
    }
    const video = webcamRef.current;
    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, width, height);

    const imgBase64 = canvas.toDataURL("image/jpeg", 0.9);

    try {
      const response = await fetch(
        "http://localhost:5000/api/face/detect-face",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: imgBase64 }),
        }
      );

      const data = await response.json();
      if (data.face_count > 0) {
        alert(`✅ Wajah terdeteksi: ${data.face_count}`);
      } else {
        alert("⚠️ Tidak ada wajah terdeteksi.");
      }
    } catch (err) {
      console.error("Face detection error:", err);
      alert("❌ Gagal mendeteksi wajah: " + err.message);
    }
  };

  // --- Timer ---
  const startTimer = () => {
    setSeconds(0);
    timerRef.current = setInterval(() => {
      setSeconds((prev) => prev + 1);
    }, 1000);
  };

  // --- Upload video ---
  const uploadRecording = async () => {
    if (videoChunksRef.current.length === 0) {
      setError("Tidak ada data untuk diunggah.");
      return;
    }
    try {
      const videoBlob = new Blob(videoChunksRef.current, { type: "video/webm" });
      if (videoBlob.size === 0) {
        setError("File rekaman kosong.");
        return;
      }
      const formData = new FormData();
      formData.append("video", videoBlob, "recording.webm");
      formData.append("session_id", sessionId);
      formData.append("question_id", questions[currentQuestionIndex].id);

      await interviewAPI.uploadAnswer(formData);
      alert("Jawaban berhasil disimpan!");
    } catch (err) {
      setError(
        "Gagal mengunggah jawaban: " +
          (err.response?.data?.message || err.message)
      );
    }
  };

  const finishInterview = async () => {
    try {
      await interviewAPI.completeSession({ session_id: sessionId });
      alert("Interview selesai!");
      navigate("/dashboard");
    } catch (err) {
      setError(
        "Gagal menyelesaikan sesi: " +
          (err.response?.data?.message || err.message)
      );
    }
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
      setSeconds(0);
    } else {
      finishInterview();
    }
  };

  // --- Face check loop ---
  const captureAndCheckFaces = async () => {
    if (!webcamRef.current) return;
    const video = webcamRef.current;
    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, width, height);
    const imgBase64 = canvas.toDataURL("image/jpeg", 0.9);

    try {
      const response = await fetch(
        "http://localhost:5000/api/face/detect-face",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: imgBase64 }),
        }
      );
      const data = await response.json();
      if (data.face_count > 1) {
        setFaceWarning(
          `⚠️ Terdeteksi ${data.face_count} wajah! Pastikan mengerjakan tes ini sendiri.`
        );
      } else {
        setFaceWarning("");
      }
    } catch (err) {
      console.error("Face detection error:", err);
    }
  };

  useEffect(() => {
    let intervalId;
    if (cameraStarted) {
      intervalId = setInterval(() => {
        captureAndCheckFaces();
      }, 10000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [cameraStarted]);

  // --- Helpers ---
  const getSupportedMimeType = () => {
    const mimeTypes = [
      "video/webm; codecs=vp9",
      "video/webm; codecs=vp8",
      "video/webm",
    ];
    for (let type of mimeTypes) {
      if (MediaRecorder.isTypeSupported(type)) return type;
    }
    return "video/webm";
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  // --- UI ---
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
          <div className="recording-controls mb-3 d-flex gap-2">
            <button
              className="btn btn-primary"
              onClick={startRecording}
              disabled={isRecording}
            >
              Mulai Rekam
            </button>
            <button
              className="btn btn-danger"
              onClick={stopRecording}
              disabled={!isRecording}
            >
              Stop Rekam
            </button>
            <button className="btn btn-warning" onClick={captureFace}>
              Deteksi Wajah
            </button>
            <button
              className="btn btn-success"
              onClick={nextQuestion}
              disabled={isRecording}
            >
              Pertanyaan Berikutnya
            </button>
          </div>
          {isRecording && (
            <div className="alert alert-info">Sedang merekam...</div>
          )}
        </div>
      </div>

      {/* Webcam */}
      <div className="text-center">
        <h5 className="mb-3">Kamera Anda</h5>
        {!cameraStarted && (
          <button className="btn btn-secondary mb-3" onClick={startWebcam}>
            Start Kamera
          </button>
        )}
        <video
          ref={webcamRef}
          autoPlay
          playsInline
          muted
          style={{
            width: "100%",
            maxWidth: "600px",
            border: "2px solid #ccc",
            borderRadius: "10px",
            backgroundColor: "#000",
          }}
        />
      </div>

      {faceWarning && (
        <div className="alert alert-warning mt-3">{faceWarning}</div>
      )}
    </div>
  );
};

export default Interview;