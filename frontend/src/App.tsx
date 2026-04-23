import { useState, useEffect, useRef } from "react";
import { apiClient, IdentifyResponse, ObjectProfile, Song } from "./services/api";
import { WebSocketClient, ConversationMessage } from "./services/websocket";

const screens = ["home", "loading", "meet", "voice", "singing"];

const loadingMessages = [
  "Scanning molecular structure…",
  "Detecting personality matrix…",
  "Calibrating voice resonance…",
  "Unlocking inner monologue…",
  "Almost ready to speak…",
];

const voiceStyles = [
  { id: "mysterious", label: "Deep & Wise", emoji: "🎙️", desc: "Ancient, knowing" },
  { id: "warm", label: "Bright & Bubbly", emoji: "✨", desc: "Energetic, cheerful" },
  { id: "wise", label: "Raspy & Cool", emoji: "🎸", desc: "Chill, mysterious" },
  { id: "playful", label: "Soft & Dreamy", emoji: "🌙", desc: "Gentle, whimsical" },
];

export default function App() {
  const [screen, setScreen] = useState("home");
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingMsgIdx, setLoadingMsgIdx] = useState(0);
  const [uploadedImg, setUploadedImg] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  
  // Backend data
  const [_identification, setIdentification] = useState<IdentifyResponse | null>(null);
  const [profile, setProfile] = useState<ObjectProfile | null>(null);
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);
  const [conversationMessages, setConversationMessages] = useState<ConversationMessage[]>([]);
  const [currentSong, setCurrentSong] = useState<Song | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // UI state
  const [isPlaying, setIsPlaying] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [playProgress, setPlayProgress] = useState(0);
  const [wsStatus, setWsStatus] = useState<string>("disconnected");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTranscript, setRecordingTranscript] = useState("");
  
  const fileRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);
  const playRef = useRef<number | null>(null);
  const wsClient = useRef<WebSocketClient | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const scribeConnectionRef = useRef<any>(null);

  // Loading animation
  useEffect(() => {
    if (screen !== "loading") return;
    
    const interval = setInterval(() => {
      setLoadingProgress((p) => {
        const next = p + (Math.random() * 4 + 1);
        if (next >= 100) {
          clearInterval(interval);
          return 100;
        }
        return next;
      });
    }, 120);
    
    const msgInterval = setInterval(() => {
      setLoadingMsgIdx((i) => (i + 1) % loadingMessages.length);
    }, 900);
    
    return () => { 
      clearInterval(interval); 
      clearInterval(msgInterval); 
    };
  }, [screen]);

  // Auto-advance from loading when profile is ready
  useEffect(() => {
    if (screen === "loading" && profile && loadingProgress >= 100) {
      setTimeout(() => setScreen("meet"), 500);
    }
  }, [screen, profile, loadingProgress]);

  // Song playback simulation
  useEffect(() => {
    if (!isPlaying || !audioRef.current) return;
    
    playRef.current = setInterval(() => {
      if (audioRef.current) {
        const progress = (audioRef.current.currentTime / audioRef.current.duration) * 100;
        setPlayProgress(progress);
        
        if (audioRef.current.ended) {
          setIsPlaying(false);
          setPlayProgress(0);
        }
      }
    }, 100);
    
    return () => {
      if (playRef.current) clearInterval(playRef.current);
    };
  }, [isPlaying]);

  // WebSocket setup for voice conversation
  useEffect(() => {
    if (screen === "voice" && profile && !wsClient.current) {
      const wsURL = apiClient.getWebSocketURL();
      wsClient.current = new WebSocketClient(wsURL);
      
      wsClient.current.onMessage((message) => {
        setConversationMessages(prev => [...prev, message]);
        
        // Auto-play audio if available
        if (message.audio_url && audioRef.current) {
          audioRef.current.src = message.audio_url;
          audioRef.current.play().catch(err => {
            console.error('Failed to play audio:', err);
          });
        }
      });
      
      wsClient.current.onStatus((status) => {
        setWsStatus(status);
      });
      
      wsClient.current.connect().then(() => {
        // Initialize with profile after connection
        wsClient.current?.initializeWithProfile(profile);
      }).catch(err => {
        console.error('WebSocket connection failed:', err);
        setError('Failed to connect to conversation service');
      });
    }
    
    return () => {
      if (screen !== "voice" && wsClient.current) {
        wsClient.current.disconnect();
        wsClient.current = null;
      }
    };
  }, [screen, profile]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setUploadedImg(url);
      setUploadedFile(file);
    }
  };

  const handleAnalyzeObject = async () => {
    if (!uploadedFile) {
      setError("Please upload an image first");
      return;
    }

    setError(null);
    setIsProcessing(true);
    setScreen("loading");
    setLoadingProgress(0);

    try {
      // Step 1: Identify object
      const identifyResult = await apiClient.identify(uploadedFile);
      setIdentification(identifyResult);
      setLoadingProgress(33);

      // Step 2: Generate profile with default voice style
      const defaultVoice = voiceStyles[0].id;
      setSelectedVoice(defaultVoice);
      
      const profileResult = await apiClient.generateProfile(identifyResult, defaultVoice);
      setProfile(profileResult);
      setLoadingProgress(100);
      
    } catch (err) {
      console.error('Analysis failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to analyze object');
      setScreen("home");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSendMessage = () => {
    if (!chatInput.trim() || !wsClient.current) return;

    const userMessage: ConversationMessage = {
      from: 'user',
      text: chatInput,
      timestamp: Date.now(),
    };

    setConversationMessages(prev => [...prev, userMessage]);
    
    try {
      wsClient.current.sendMessage(chatInput);
      setChatInput("");
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message');
    }
  };

  const startVoiceRecording = async () => {
    try {
      setIsRecording(true);
      setRecordingTranscript("");
      
      // Check if browser supports Web Speech API
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      
      if (!SpeechRecognition) {
        setError('Speech recognition not supported in this browser');
        setIsRecording(false);
        return;
      }
      
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      
      recognition.onresult = (event: any) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }
        
        if (finalTranscript) {
          setChatInput(prev => (prev + ' ' + finalTranscript).trim());
          setRecordingTranscript("");
        } else {
          setRecordingTranscript(interimTranscript);
        }
      };
      
      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setError(`Speech recognition error: ${event.error}`);
        stopVoiceRecording();
      };
      
      recognition.onend = () => {
        if (isRecording) {
          // Restart if still recording
          recognition.start();
        }
      };
      
      recognition.start();
      scribeConnectionRef.current = recognition;
      
    } catch (err) {
      console.error('Failed to start voice recording:', err);
      setError('Failed to start voice recording');
      setIsRecording(false);
    }
  };

  const stopVoiceRecording = () => {
    if (scribeConnectionRef.current) {
      try {
        scribeConnectionRef.current.stop();
      } catch (e) {
        console.error('Error stopping recognition:', e);
      }
      scribeConnectionRef.current = null;
    }
    setIsRecording(false);
    setRecordingTranscript("");
  };

  const toggleVoiceRecording = () => {
    if (isRecording) {
      stopVoiceRecording();
    } else {
      startVoiceRecording();
    }
  };

  const handleRequestSong = async () => {
    if (!profile) return;

    setIsProcessing(true);
    setError(null);

    try {
      const song = await apiClient.sing({
        profile,
        theme: 'upbeat and fun',
      });

      setCurrentSong(song);
      
      // Load audio with error handling
      if (audioRef.current) {
        audioRef.current.src = song.audio_url;
        audioRef.current.load();
        
        // Add event listeners for audio loading
        audioRef.current.onloadeddata = () => {
          console.log('Audio loaded successfully');
        };
        
        audioRef.current.onerror = (e) => {
          console.error('Audio loading error:', e);
          setError('Failed to load audio. The song may still be generating.');
        };
      }
    } catch (err) {
      console.error('Failed to generate song:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate song');
    } finally {
      setIsProcessing(false);
    }
  };

  const togglePlayPause = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const parseLyrics = (lyrics: string) => {
    const lines = lyrics.split('\n').filter(line => line.trim());
    return lines.map((line, i) => ({
      time: `0:${String(i * 4).padStart(2, '0')}`,
      text: line,
    }));
  };

  return (
    <div style={{
      fontFamily: "'Syne', sans-serif",
      background: "#0a0a0f",
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Syne+Mono&display=swap');
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
          --lime: #c8f135;
          --coral: #ff5e5b;
          --sky: #5bf5d3;
          --ink: #0a0a0f;
          --card: #12121a;
          --muted: #2a2a38;
          --text: #f0efea;
          --sub: #7a7a8c;
        }
        
        .phone {
          width: 390px;
          height: 844px;
          background: var(--card);
          border-radius: 44px;
          overflow: hidden;
          position: relative;
          box-shadow: 0 40px 120px rgba(0,0,0,0.8), inset 0 0 0 1px rgba(255,255,255,0.06);
        }
        
        .screen { 
          width: 100%; 
          height: 100%; 
          display: flex; 
          flex-direction: column; 
          position: relative; 
          overflow: hidden; 
        }
        
        .notch {
          width: 120px; 
          height: 34px; 
          background: #000;
          border-radius: 0 0 20px 20px; 
          margin: 0 auto;
          position: absolute; 
          top: 0; 
          left: 50%; 
          transform: translateX(-50%);
          z-index: 10;
        }
        
        .nav-bar {
          position: absolute; 
          bottom: 0; 
          left: 0; 
          right: 0;
          height: 80px; 
          background: rgba(18,18,26,0.95);
          backdrop-filter: blur(12px);
          display: flex; 
          align-items: center; 
          justify-content: center;
          gap: 8px; 
          padding: 0 20px 20px;
          border-top: 1px solid rgba(255,255,255,0.06);
          z-index: 10;
        }
        
        .nav-dot {
          width: 6px; 
          height: 6px; 
          border-radius: 50%;
          background: var(--muted); 
          cursor: pointer; 
          transition: all 0.2s;
        }
        
        .nav-dot.active { 
          background: var(--lime); 
          width: 20px; 
          border-radius: 3px; 
        }
        
        .btn {
          display: inline-flex; 
          align-items: center; 
          justify-content: center;
          gap: 8px; 
          padding: 14px 28px; 
          border-radius: 100px;
          font-family: 'Syne', sans-serif; 
          font-weight: 700; 
          font-size: 15px;
          cursor: pointer; 
          border: none; 
          transition: all 0.2s; 
          text-decoration: none;
        }
        
        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        .btn-lime { 
          background: var(--lime); 
          color: var(--ink); 
        }
        
        .btn-lime:hover:not(:disabled) { 
          transform: scale(1.03); 
          box-shadow: 0 0 24px rgba(200,241,53,0.4); 
        }
        
        .btn-outline { 
          background: transparent; 
          color: var(--text); 
          border: 1.5px solid var(--muted); 
        }
        
        .btn-outline:hover:not(:disabled) { 
          border-color: var(--sky); 
          color: var(--sky); 
        }
        
        .tag {
          display: inline-block; 
          padding: 4px 12px; 
          border-radius: 100px;
          font-size: 11px; 
          font-weight: 700; 
          letter-spacing: 0.08em; 
          text-transform: uppercase;
        }
        
        .tag-lime { 
          background: rgba(200,241,53,0.12); 
          color: var(--lime); 
        }
        
        .tag-coral { 
          background: rgba(255,94,91,0.12); 
          color: var(--coral); 
        }
        
        .tag-sky { 
          background: rgba(91,245,211,0.12); 
          color: var(--sky); 
        }
        
        .scrollable { 
          overflow-y: auto; 
        }
        
        .scrollable::-webkit-scrollbar { 
          display: none; 
        }
        
        @keyframes pulse-ring {
          0% { transform: scale(1); opacity: 0.6; }
          100% { transform: scale(1.8); opacity: 0; }
        }
        
        @keyframes float {
          0%,100% { transform: translateY(0); }
          50% { transform: translateY(-8px); }
        }
        
        @keyframes waveform {
          0%,100% { height: 6px; }
          50% { height: 24px; }
        }
        
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.1); opacity: 0.8; }
        }
        
        .float { 
          animation: float 3s ease-in-out infinite; 
        }
        
        .fade-up { 
          animation: fadeUp 0.4s ease forwards; 
        }
      `}</style>

      {/* Hidden audio element */}
      <audio ref={audioRef} style={{ display: 'none' }} />

      {/* Error toast */}
      {error && (
        <div style={{
          position: 'fixed',
          top: 20,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'var(--coral)',
          color: 'white',
          padding: '12px 24px',
          borderRadius: 12,
          zIndex: 1000,
          fontWeight: 600,
        }}>
          {error}
          <button 
            onClick={() => setError(null)}
            style={{
              marginLeft: 12,
              background: 'none',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              fontSize: 16,
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Nav dots overlay */}
      <div style={{ 
        position: "absolute", 
        zIndex: 100, 
        left: "50%", 
        transform: "translateX(-50%)", 
        top: 16, 
        display: "flex", 
        gap: 6 
      }}>
        {screens.map((s) => (
          <div 
            key={s} 
            className={`nav-dot ${screen === s ? "active" : ""}`} 
            onClick={() => setScreen(s)} 
          />
        ))}
      </div>

      <div className="phone">
        <div className="notch" />

        {/* ─── HOME SCREEN ─── */}
        {screen === "home" && (
          <div className="screen" style={{ background: "linear-gradient(160deg, #0e0e18 0%, #12121f 100%)" }}>
            <div style={{ 
              position: "absolute", 
              top: -60, 
              right: -60, 
              width: 220, 
              height: 220, 
              borderRadius: "50%", 
              background: "radial-gradient(circle, rgba(200,241,53,0.12) 0%, transparent 70%)", 
              pointerEvents: "none" 
            }} />
            <div style={{ 
              position: "absolute", 
              bottom: 120, 
              left: -40, 
              width: 180, 
              height: 180, 
              borderRadius: "50%", 
              background: "radial-gradient(circle, rgba(91,245,211,0.08) 0%, transparent 70%)", 
              pointerEvents: "none" 
            }} />

            <div style={{ padding: "80px 28px 0", flex: 1, display: "flex", flexDirection: "column" }}>
              <div style={{ marginBottom: 32 }}>
                <span className="tag tag-lime" style={{ marginBottom: 14, display: "inline-block" }}>
                  ✦ Objects Speak
                </span>
                <h1 style={{ 
                  color: "var(--text)", 
                  fontSize: 38, 
                  fontWeight: 800, 
                  lineHeight: 1.1, 
                  letterSpacing: "-0.02em" 
                }}>
                  Give Your<br />
                  <span style={{ color: "var(--lime)" }}>Stuff</span> a Voice
                </h1>
                <p style={{ color: "var(--sub)", fontSize: 14, marginTop: 12, lineHeight: 1.6 }}>
                  Point at any object. Discover its personality, hear it speak, make it sing.
                </p>
              </div>

              <div
                onClick={() => fileRef.current?.click()}
                style={{
                  width: "100%", 
                  height: 280,
                  background: uploadedImg ? `url(${uploadedImg}) center/cover` : "var(--muted)",
                  borderRadius: 24, 
                  position: "relative", 
                  overflow: "hidden",
                  cursor: "pointer", 
                  border: "2px dashed rgba(255,255,255,0.1)",
                  display: "flex", 
                  alignItems: "center", 
                  justifyContent: "center",
                  transition: "border-color 0.2s",
                }}
              >
                {!uploadedImg && (
                  <>
                    {["topleft","topright","bottomleft","bottomright"].map(pos => (
                      <div 
                        key={pos} 
                        style={{
                          position: "absolute",
                          top: pos.includes("top") ? 16 : "auto",
                          bottom: pos.includes("bottom") ? 16 : "auto",
                          left: pos.includes("left") ? 16 : "auto",
                          right: pos.includes("right") ? 16 : "auto",
                          width: 20, 
                          height: 20,
                          borderTop: pos.includes("top") ? "2px solid var(--lime)" : "none",
                          borderBottom: pos.includes("bottom") ? "2px solid var(--lime)" : "none",
                          borderLeft: pos.includes("left") ? "2px solid var(--lime)" : "none",
                          borderRight: pos.includes("right") ? "2px solid var(--lime)" : "none",
                        }} 
                      />
                    ))}
                    <div style={{ textAlign: "center" }}>
                      <div style={{ fontSize: 48, marginBottom: 8 }}>📷</div>
                      <p style={{ color: "var(--sub)", fontSize: 13 }}>Tap to take photo</p>
                      <p style={{ color: "var(--sub)", fontSize: 11, marginTop: 4 }}>or use buttons below</p>
                    </div>
                  </>
                )}
                {uploadedImg && (
                  <div style={{
                    position: "absolute", 
                    bottom: 12, 
                    right: 12,
                    background: "rgba(0,0,0,0.6)", 
                    backdropFilter: "blur(8px)",
                    borderRadius: 8, 
                    padding: "6px 12px",
                    color: "var(--lime)", 
                    fontSize: 12, 
                    fontWeight: 700,
                  }}>
                    ✓ Ready to analyze
                  </div>
                )}
              </div>

              <input 
                ref={fileRef} 
                type="file" 
                accept="image/*" 
                capture="environment"
                style={{ display: "none" }} 
                onChange={handleFileChange} 
              />
              
              <input 
                ref={galleryRef} 
                type="file" 
                accept="image/*" 
                style={{ display: "none" }} 
                onChange={handleFileChange} 
              />

              <div style={{ marginTop: 20, display: "flex", gap: 10 }}>
                <button 
                  className="btn btn-lime" 
                  style={{ flex: 1 }} 
                  onClick={handleAnalyzeObject}
                  disabled={!uploadedFile || isProcessing}
                >
                  {isProcessing ? "⏳ Analyzing..." : "⚡ Analyze Object"}
                </button>
                <button 
                  className="btn btn-outline" 
                  style={{ flex: 0, padding: "14px 18px" }} 
                  onClick={() => fileRef.current?.click()}
                  title="Take Photo"
                >
                  📷
                </button>
                <button 
                  className="btn btn-outline" 
                  style={{ flex: 0, padding: "14px 18px" }} 
                  onClick={() => galleryRef.current?.click()}
                  title="Choose from Gallery"
                >
                  🖼️
                </button>
              </div>
            </div>

            <div className="nav-bar">
              {screens.map((s) => 
                <div 
                  key={s} 
                  className={`nav-dot ${screen === s ? "active" : ""}`} 
                  onClick={() => setScreen(s)} 
                />
              )}
            </div>
          </div>
        )}

        {/* ─── LOADING SCREEN ─── */}
        {screen === "loading" && (
          <div className="screen" style={{ background: "#08080f", alignItems: "center", justifyContent: "center" }}>
            {[1,2,3].map(i => (
              <div 
                key={i} 
                style={{
                  position: "absolute",
                  width: 80 + i * 90, 
                  height: 80 + i * 90,
                  borderRadius: "50%",
                  border: `1px solid rgba(200,241,53,${0.08 / i})`,
                  animation: `pulse-ring ${1.5 + i * 0.5}s ease-out ${i * 0.3}s infinite`,
                  pointerEvents: "none",
                }} 
              />
            ))}

            <div style={{ textAlign: "center", zIndex: 1, width: "100%", padding: "0 40px" }}>
              <div style={{
                width: 120, 
                height: 120, 
                borderRadius: 32,
                background: uploadedImg ? `url(${uploadedImg}) center/cover` : "var(--muted)", 
                margin: "0 auto 32px",
                display: "flex", 
                alignItems: "center", 
                justifyContent: "center",
                fontSize: 56, 
                position: "relative",
                boxShadow: "0 0 60px rgba(200,241,53,0.15)",
              }} className="float">
                {!uploadedImg && "📦"}
                <div style={{
                  position: "absolute", 
                  inset: -3, 
                  borderRadius: 35,
                  background: `conic-gradient(var(--lime) ${loadingProgress}%, transparent 0%)`,
                  zIndex: -1,
                  WebkitMask: "radial-gradient(farthest-side, transparent calc(100% - 3px), white 0)",
                  mask: "radial-gradient(farthest-side, transparent calc(100% - 3px), white 0)",
                }} />
              </div>

              <div style={{ marginBottom: 8 }}>
                <span className="tag tag-lime">{Math.round(loadingProgress)}%</span>
              </div>

              <h2 style={{ color: "var(--text)", fontSize: 24, fontWeight: 800, marginBottom: 8 }}>
                Awakening…
              </h2>
              <p style={{ color: "var(--sub)", fontSize: 14, minHeight: 20, transition: "opacity 0.3s" }}>
                {loadingMessages[loadingMsgIdx]}
              </p>

              <div style={{
                width: "100%", 
                height: 4, 
                background: "var(--muted)",
                borderRadius: 100, 
                marginTop: 32, 
                overflow: "hidden",
              }}>
                <div style={{
                  height: "100%", 
                  borderRadius: 100,
                  width: `${loadingProgress}%`,
                  background: "linear-gradient(90deg, var(--sky), var(--lime))",
                  transition: "width 0.15s ease",
                  boxShadow: "0 0 12px rgba(200,241,53,0.5)",
                }} />
              </div>

              <div style={{ marginTop: 32, display: "flex", flexDirection: "column", gap: 10, textAlign: "left" }}>
                {["Visual Analysis", "Personality Engine", "Voice Synthesis"].map((step, i) => {
                  const done = loadingProgress > (i + 1) * 28;
                  const active = loadingProgress > i * 28 && !done;
                  return (
                    <div 
                      key={step} 
                      style={{
                        display: "flex", 
                        alignItems: "center", 
                        gap: 12,
                        padding: "10px 14px", 
                        borderRadius: 12,
                        background: done ? "rgba(200,241,53,0.05)" : active ? "rgba(91,245,211,0.05)" : "transparent",
                        transition: "background 0.3s",
                      }}
                    >
                      <div style={{
                        width: 22, 
                        height: 22, 
                        borderRadius: "50%",
                        background: done ? "var(--lime)" : active ? "var(--sky)" : "var(--muted)",
                        display: "flex", 
                        alignItems: "center", 
                        justifyContent: "center",
                        fontSize: 11, 
                        fontWeight: 700, 
                        color: "#000",
                        transition: "all 0.3s",
                      }}>
                        {done ? "✓" : active ? "…" : i + 1}
                      </div>
                      <span style={{ 
                        color: done ? "var(--lime)" : active ? "var(--sky)" : "var(--sub)", 
                        fontSize: 14, 
                        fontWeight: 600 
                      }}>
                        {step}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ─── MEET YOUR OBJECT ─── */}
        {screen === "meet" && profile && (
          <div className="screen scrollable" style={{ background: "#0d0d15", paddingBottom: 100 }}>
            <div style={{
              position: "absolute", 
              top: 0, 
              left: 0, 
              right: 0, 
              height: 300,
              background: "linear-gradient(180deg, rgba(200,241,53,0.06) 0%, transparent 100%)",
              pointerEvents: "none",
            }} />

            <div style={{ padding: "60px 24px 120px" }}>
              <div style={{ textAlign: "center", marginBottom: 28 }}>
                <div style={{
                  width: 110, 
                  height: 110, 
                  borderRadius: 28, 
                  background: "var(--muted)",
                  margin: "0 auto 16px", 
                  display: "flex", 
                  alignItems: "center",
                  justifyContent: "center", 
                  fontSize: 56,
                  boxShadow: "0 20px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(200,241,53,0.1)",
                }} className="float">
                  {profile.emoji}
                </div>

                <div style={{ display: "flex", gap: 6, justifyContent: "center", marginBottom: 10, flexWrap: "wrap" }}>
                  <span className="tag tag-lime">{profile.species || "Object"}</span>
                  {profile.traits.slice(0, 2).map((trait, i) => (
                    <span key={i} className="tag tag-sky">{trait}</span>
                  ))}
                </div>

                <h2 style={{ color: "var(--text)", fontSize: 30, fontWeight: 800 }}>
                  {profile.name}
                </h2>
                <p style={{ color: "var(--sub)", fontSize: 13, marginTop: 6, lineHeight: 1.5 }}>
                  {profile.backstory.length > 120 ? profile.backstory.substring(0, 120) + "..." : profile.backstory}
                </p>
              </div>

              <div style={{
                display: "grid", 
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: 10, 
                marginBottom: 24,
              }}>
                {[
                  { label: "Species", value: profile.species || "Object" },
                  { label: "Mood", value: profile.traits[0] || "Curious" },
                  { label: "Traits", value: profile.traits.length.toString() },
                ].map(({ label, value }) => (
                  <div 
                    key={label} 
                    style={{
                      background: "var(--muted)", 
                      borderRadius: 16, 
                      padding: "14px 10px",
                      textAlign: "center",
                    }}
                  >
                    <div style={{ color: "var(--lime)", fontSize: 16, fontWeight: 800 }}>
                      {value}
                    </div>
                    <div style={{ color: "var(--sub)", fontSize: 11, marginTop: 2 }}>
                      {label}
                    </div>
                  </div>
                ))}
              </div>

              <div style={{
                background: "var(--muted)", 
                borderRadius: 20, 
                padding: 18, 
                marginBottom: 24,
              }}>
                <p style={{ 
                  color: "var(--sub)", 
                  fontSize: 12, 
                  fontWeight: 700, 
                  textTransform: "uppercase", 
                  letterSpacing: "0.07em", 
                  marginBottom: 8 
                }}>
                  Bio
                </p>
                <p style={{ color: "var(--text)", fontSize: 14, lineHeight: 1.7 }}>
                  {profile.backstory}
                </p>
              </div>

              <p style={{ 
                color: "var(--sub)", 
                fontSize: 12, 
                fontWeight: 700, 
                textTransform: "uppercase", 
                letterSpacing: "0.07em", 
                marginBottom: 12 
              }}>
                Choose a Voice
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 }}>
                {voiceStyles.map((v) => (
                  <div
                    key={v.id}
                    onClick={() => setSelectedVoice(v.id)}
                    style={{
                      padding: "14px 16px", 
                      borderRadius: 16, 
                      cursor: "pointer",
                      background: selectedVoice === v.id ? "rgba(200,241,53,0.08)" : "var(--muted)",
                      border: `1.5px solid ${selectedVoice === v.id ? "var(--lime)" : "transparent"}`,
                      display: "flex", 
                      alignItems: "center", 
                      gap: 14, 
                      transition: "all 0.2s",
                    }}
                  >
                    <span style={{ fontSize: 24 }}>{v.emoji}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ 
                        color: selectedVoice === v.id ? "var(--lime)" : "var(--text)", 
                        fontWeight: 700, 
                        fontSize: 14 
                      }}>
                        {v.label}
                      </div>
                      <div style={{ color: "var(--sub)", fontSize: 12 }}>
                        {v.desc}
                      </div>
                    </div>
                    {selectedVoice === v.id && (
                      <div style={{ 
                        width: 20, 
                        height: 20, 
                        borderRadius: "50%", 
                        background: "var(--lime)", 
                        display: "flex", 
                        alignItems: "center", 
                        justifyContent: "center", 
                        fontSize: 11, 
                        color: "#000", 
                        fontWeight: 700 
                      }}>
                        ✓
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div style={{ display: "flex", gap: 10 }}>
                <button 
                  className="btn btn-lime" 
                  style={{ flex: 1 }} 
                  onClick={() => setScreen("voice")}
                >
                  🎙️ Start Conversation
                </button>
                <button 
                  className="btn btn-outline" 
                  onClick={() => {
                    setScreen("singing");
                    if (!currentSong) handleRequestSong();
                  }}
                >
                  🎵
                </button>
              </div>
            </div>

            <div className="nav-bar">
              {screens.map((s) => 
                <div 
                  key={s} 
                  className={`nav-dot ${screen === s ? "active" : ""}`} 
                  onClick={() => setScreen(s)} 
                />
              )}
            </div>
          </div>
        )}

        {/* ─── VOICE CONVERSATION ─── */}
        {screen === "voice" && profile && (
          <div className="screen" style={{ background: "#09090f" }}>
            <div style={{ 
              position: "absolute", 
              top: 0, 
              left: 0, 
              right: 0, 
              bottom: 0, 
              pointerEvents: "none",
              background: "radial-gradient(ellipse at 50% 30%, rgba(91,245,211,0.05) 0%, transparent 60%)" 
            }} />

            <div style={{ padding: "56px 24px 16px", display: "flex", alignItems: "center", gap: 14 }}>
              <div style={{
                width: 44, 
                height: 44, 
                borderRadius: 14, 
                background: "var(--muted)",
                display: "flex", 
                alignItems: "center", 
                justifyContent: "center", 
                fontSize: 22,
              }}>
                {profile.emoji}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ color: "var(--text)", fontWeight: 700, fontSize: 15 }}>
                  {profile.name}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
                  <div style={{ 
                    width: 6, 
                    height: 6, 
                    borderRadius: "50%", 
                    background: wsStatus === "connected" ? "#4ade80" : "#ff5e5b", 
                    boxShadow: wsStatus === "connected" ? "0 0 8px #4ade80" : "none"
                  }} />
                  <span style={{ color: "var(--sub)", fontSize: 12 }}>
                    {wsStatus === "connected" ? "Listening…" : "Connecting…"}
                  </span>
                </div>
              </div>
              <button 
                className="btn btn-outline" 
                style={{ padding: "8px 14px", fontSize: 12 }} 
                onClick={() => {
                  setScreen("singing");
                  if (!currentSong) handleRequestSong();
                }}
              >
                🎵 Sing
              </button>
            </div>

            <div style={{ 
              height: 60, 
              display: "flex", 
              alignItems: "center", 
              justifyContent: "center", 
              gap: 3, 
              padding: "0 24px" 
            }}>
              {Array.from({ length: 40 }).map((_, i) => (
                <div 
                  key={i} 
                  style={{
                    width: 3, 
                    borderRadius: 2,
                    background: `rgba(91,245,211,${0.3 + Math.random() * 0.4})`,
                    height: 6,
                    animation: `waveform ${0.6 + Math.random() * 0.8}s ease-in-out ${i * 0.03}s infinite alternate`,
                  }} 
                />
              ))}
            </div>

            <div className="scrollable" style={{ 
              flex: 1, 
              padding: "8px 20px", 
              display: "flex", 
              flexDirection: "column", 
              gap: 12 
            }}>
              {conversationMessages.length === 0 && (
                <div style={{ 
                  textAlign: "center", 
                  color: "var(--sub)", 
                  fontSize: 14, 
                  marginTop: 40 
                }}>
                  Start a conversation with {profile.name}...
                </div>
              )}
              {conversationMessages.map((msg, i) => (
                <div 
                  key={i} 
                  style={{
                    display: "flex", 
                    justifyContent: msg.from === "user" ? "flex-end" : "flex-start",
                    animation: "fadeUp 0.3s ease forwards",
                  }}
                >
                  {msg.from === "obj" && (
                    <div style={{ 
                      width: 28, 
                      height: 28, 
                      borderRadius: 8, 
                      background: "var(--muted)", 
                      display: "flex", 
                      alignItems: "center", 
                      justifyContent: "center", 
                      fontSize: 14, 
                      marginRight: 8, 
                      flexShrink: 0, 
                      alignSelf: "flex-end" 
                    }}>
                      {profile.emoji}
                    </div>
                  )}
                  <div style={{
                    maxWidth: "75%", 
                    padding: "11px 14px", 
                    borderRadius: msg.from === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                    background: msg.from === "user" ? "var(--lime)" : "var(--muted)",
                    color: msg.from === "user" ? "#0a0a0f" : "var(--text)",
                    fontSize: 14, 
                    lineHeight: 1.5, 
                    fontWeight: msg.from === "user" ? 600 : 400,
                  }}>
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ 
              padding: "12px 16px 90px", 
              display: "flex", 
              gap: 10, 
              alignItems: "center" 
            }}>
              <div style={{
                flex: 1, 
                background: "var(--muted)", 
                borderRadius: 100,
                display: "flex", 
                alignItems: "center", 
                padding: "0 16px", 
                height: 48,
                border: "1.5px solid rgba(255,255,255,0.06)",
              }}>
                <input
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && !isRecording && handleSendMessage()}
                  placeholder={isRecording ? "Listening..." : recordingTranscript || "Say something…"}
                  disabled={isRecording}
                  style={{
                    background: "none", 
                    border: "none", 
                    outline: "none",
                    color: isRecording ? "var(--lime)" : "var(--text)", 
                    fontSize: 14, 
                    width: "100%",
                    fontFamily: "'Syne', sans-serif",
                  }}
                />
              </div>
              <button 
                onClick={chatInput.trim() ? handleSendMessage : toggleVoiceRecording}
                disabled={wsStatus !== "connected"}
                style={{
                  width: 48, 
                  height: 48, 
                  borderRadius: "50%",
                  background: chatInput.trim() ? "var(--lime)" : isRecording ? "var(--coral)" : "var(--muted)",
                  border: "none", 
                  cursor: "pointer", 
                  fontSize: 18,
                  display: "flex", 
                  alignItems: "center", 
                  justifyContent: "center",
                  transition: "all 0.2s",
                  animation: isRecording ? "pulse 1.5s ease-in-out infinite" : "none",
                }}
              >
                {chatInput.trim() ? "↑" : isRecording ? "⏹" : "🎤"}
              </button>
            </div>

            <div className="nav-bar">
              {screens.map((s) => 
                <div 
                  key={s} 
                  className={`nav-dot ${screen === s ? "active" : ""}`} 
                  onClick={() => setScreen(s)} 
                />
              )}
            </div>
          </div>
        )}

        {/* ─── SINGING SCREEN ─── */}
        {screen === "singing" && profile && (
          <div className="screen" style={{ background: "#08080e" }}>
            <div style={{
              position: "absolute", 
              top: "30%", 
              left: "50%", 
              transform: "translateX(-50%)",
              width: 300, 
              height: 300, 
              borderRadius: "50%",
              background: `radial-gradient(circle, rgba(${isPlaying ? "200,241,53" : "91,245,211"},0.08) 0%, transparent 70%)`,
              transition: "background 1s", 
              pointerEvents: "none",
            }} />

            <div style={{ 
              padding: "56px 24px 100px", 
              display: "flex", 
              flexDirection: "column", 
              height: "100%" 
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 28 }}>
                <button 
                  className="btn btn-outline" 
                  style={{ padding: "8px 14px", fontSize: 12 }} 
                  onClick={() => setScreen("voice")}
                >
                  ← Back
                </button>
                <div style={{ flex: 1 }}>
                  <span className="tag tag-coral">🎵 Now Singing</span>
                </div>
              </div>

              <div style={{ textAlign: "center", marginBottom: 24 }}>
                <div style={{
                  width: 160, 
                  height: 160, 
                  borderRadius: 32,
                  background: "linear-gradient(135deg, #1a1a2e, var(--muted))",
                  margin: "0 auto 16px",
                  display: "flex", 
                  alignItems: "center", 
                  justifyContent: "center",
                  fontSize: 72, 
                  position: "relative",
                  boxShadow: isPlaying 
                    ? "0 0 60px rgba(200,241,53,0.2), 0 20px 60px rgba(0,0,0,0.6)" 
                    : "0 20px 60px rgba(0,0,0,0.6)",
                  transition: "box-shadow 0.5s",
                  animation: isPlaying ? "spin-slow 8s linear infinite" : "none",
                }}>
                  {profile.emoji}
                </div>

                <h3 style={{ color: "var(--text)", fontSize: 20, fontWeight: 800 }}>
                  {profile.name}'s Song
                </h3>
                <p style={{ color: "var(--sub)", fontSize: 13, marginTop: 4 }}>
                  {profile.name} · 2024
                </p>
              </div>

              {!currentSong && !isProcessing && (
                <div style={{ textAlign: "center", marginTop: 40 }}>
                  <button 
                    className="btn btn-lime"
                    onClick={handleRequestSong}
                  >
                    🎵 Generate Song
                  </button>
                </div>
              )}

              {isProcessing && (
                <div style={{ textAlign: "center", color: "var(--sub)", marginTop: 40 }}>
                  <div className="float" style={{ fontSize: 48, marginBottom: 16 }}>🎵</div>
                  <p>Composing a masterpiece...</p>
                </div>
              )}

              {currentSong && (
                <>
                  <div className="scrollable" style={{ flex: 1, marginBottom: 16 }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      {parseLyrics(currentSong.lyrics).map((line, i) => {
                        const currentTime = audioRef.current?.currentTime || 0;
                        const duration = audioRef.current?.duration || 1;
                        const lineProgress = i / parseLyrics(currentSong.lyrics).length;
                        const playbackProgress = currentTime / duration;
                        const isActive = Math.abs(lineProgress - playbackProgress) < 0.1;
                        
                        return (
                          <div 
                            key={i} 
                            style={{
                              padding: "10px 14px", 
                              borderRadius: 12, 
                              transition: "all 0.3s",
                              background: isActive ? "rgba(200,241,53,0.08)" : "transparent",
                              borderLeft: `3px solid ${isActive ? "var(--lime)" : "transparent"}`,
                              display: "flex", 
                              gap: 12, 
                              alignItems: "center",
                            }}
                          >
                            <span style={{ 
                              color: "var(--muted)", 
                              fontSize: 11, 
                              fontFamily: "'Syne Mono', monospace", 
                              minWidth: 30 
                            }}>
                              {line.time}
                            </span>
                            <span style={{
                              fontSize: isActive ? 16 : 14,
                              fontWeight: isActive ? 700 : 400,
                              color: isActive ? "var(--lime)" : "var(--text)",
                              transition: "all 0.3s",
                            }}>
                              {line.text}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div style={{ marginBottom: 16 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                      <span style={{ 
                        color: "var(--sub)", 
                        fontSize: 12, 
                        fontFamily: "'Syne Mono', monospace" 
                      }}>
                        {Math.floor(audioRef.current?.currentTime || 0)}s
                      </span>
                      <span style={{ 
                        color: "var(--sub)", 
                        fontSize: 12, 
                        fontFamily: "'Syne Mono', monospace" 
                      }}>
                        {Math.floor(audioRef.current?.duration || 0)}s
                      </span>
                    </div>
                    <div style={{
                      width: "100%", 
                      height: 4, 
                      background: "var(--muted)", 
                      borderRadius: 100, 
                      overflow: "hidden",
                    }}>
                      <div style={{
                        height: "100%", 
                        background: "linear-gradient(90deg, var(--coral), var(--lime))",
                        width: `${playProgress}%`, 
                        borderRadius: 100, 
                        transition: "width 0.1s",
                        boxShadow: "0 0 8px rgba(255,94,91,0.4)",
                      }} />
                    </div>
                  </div>

                  <div style={{ 
                    display: "flex", 
                    alignItems: "center", 
                    justifyContent: "center", 
                    gap: 20 
                  }}>
                    <button 
                      onClick={togglePlayPause}
                      style={{
                        width: 64, 
                        height: 64, 
                        borderRadius: "50%",
                        background: isPlaying ? "var(--lime)" : "var(--coral)",
                        border: "none", 
                        cursor: "pointer", 
                        fontSize: 24,
                        display: "flex", 
                        alignItems: "center", 
                        justifyContent: "center",
                        boxShadow: isPlaying 
                          ? "0 0 30px rgba(200,241,53,0.4)" 
                          : "0 0 30px rgba(255,94,91,0.4)",
                        transition: "all 0.3s",
                      }}
                    >
                      {isPlaying ? "⏸" : "▶"}
                    </button>
                  </div>

                  <div style={{ textAlign: "center", marginTop: 16 }}>
                    <button 
                      className="btn btn-outline"
                      onClick={handleRequestSong}
                      disabled={isProcessing}
                    >
                      🔄 Request Another Song
                    </button>
                  </div>
                </>
              )}
            </div>

            <div className="nav-bar">
              {screens.map((s) => 
                <div 
                  key={s} 
                  className={`nav-dot ${screen === s ? "active" : ""}`} 
                  onClick={() => setScreen(s)} 
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
