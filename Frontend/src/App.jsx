import React, { useState, useEffect, useRef } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { 
  Database, Zap, LayoutDashboard, TerminalSquare, 
  DatabaseBackup, Activity, Settings, HelpCircle, 
  UploadCloud, Link as LinkIcon, Sparkles, Send, Paperclip, X
} from 'lucide-react';
import './index.css';

const API_BASE_URL = 'https://sachingoyal27-talk2data.hf.space';

export default function App() {
  const [activeMode, setActiveMode] = useState('dataset'); // 'dataset' | 'sql'
  const [isBackendHealthy, setIsBackendHealthy] = useState(false);
  const [resetKey, setResetKey] = useState(0);
  const [showSupport, setShowSupport] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then(res => setIsBackendHealthy(res.ok))
      .catch(() => setIsBackendHealthy(false));
  }, []);

  const handleNewAnalysis = () => {
    setResetKey(prev => prev + 1);
    toast.success("Started a new analysis session");
  };

  const handleSupportClick = () => {
    setShowSupport(true);
  };

  const handleSettingsClick = () => {
    toast('Settings are coming soon!', { icon: '⚙️' });
  };

  return (
    <div className="app-container">
      <Toaster 
        position="top-right" 
        toastOptions={{ 
          style: { background: '#171f33', color: '#dae2fd', border: '1px solid rgba(70, 69, 84, 0.3)' } 
        }} 
      />
      
      {/* Top Bar */}
      <header className="top-bar">
        <div className="flex items-center gap-6">
          <span className="logo-text">Talk2Data</span>
          <div className="status-badge">
            <div className={`status-dot ${!isBackendHealthy ? 'offline' : ''}`}></div>
            <span className={`status-text ${!isBackendHealthy ? 'offline' : ''}`}>
              {isBackendHealthy ? 'Backend Healthy' : 'Backend Offline'}
            </span>
          </div>
        </div>

        <nav className="top-nav">
          <button 
            className={`nav-btn ${activeMode === 'dataset' ? 'active' : ''}`}
            onClick={() => setActiveMode('dataset')}
          >
            Dataset
          </button>
          <button 
            className={`nav-btn ${activeMode === 'sql' ? 'active' : ''}`}
            onClick={() => setActiveMode('sql')}
          >
            SQL
          </button>
        </nav>

        <div className="icon-btn-container">
          {/* Removed generic buttons based on user feedback to clean up the UI */}
          <div className="profile-img-container" style={{ cursor: 'pointer' }} onClick={() => window.open('https://github.com/SachinGoyal94/PurposePredict_Talk2Data', '_blank')}>
            <img 
              alt="User profile" 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuDfrtHdD5MkxUCGsxkdlNKI7q2WGwFaN3eE3rahPkEl-CoL-Xqg_wlNJ7hI3q-CdpjGtsPFmbsWGqYxfbKnv96GwU0sN3BU1ufLl5b-IUiw2gfV8JlRZJHyqY6FJJ0hLeNBGTSYtW4_CB0Kx3ebacc5Da9JWAhmOkl9acHk-vWwYjkFMwPRlcG9OhrUA8zlSmgcjP1PZJbdcQsIuTlGqXmSKNlSjlcBm4CosijPUZG7cUv3-dvaaHV-V2pyhkvrz7EtBLIaV-wVeU0e" 
            />
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-content">
          <div style={{ marginBottom: '1rem', padding: '0 1rem' }}>
            <h3 className="sidebar-title">Intelligence Layer</h3>
            <p className="sidebar-subtitle">
              <Activity size={12} color="currentColor" /> 
              AI Curator Active
            </p>
          </div>

          <button 
            className={`sidebar-item ${activeMode === 'dataset' ? 'active' : ''}`}
            onClick={() => setActiveMode('dataset')}
          >
            <DatabaseBackup size={20} />
            <span>Datasets</span>
          </button>
          <button 
            className={`sidebar-item ${activeMode === 'sql' ? 'active' : ''}`}
            onClick={() => setActiveMode('sql')}
          >
            <TerminalSquare size={20} />
            <span>SQL Queries</span>
          </button>

          <div style={{ marginTop: '2rem', padding: '0 1rem' }}>
            <button className="btn-primary" onClick={handleNewAnalysis}>New Analysis</button>
          </div>

          <div className="sidebar-bottom">
            <button className="sidebar-item" onClick={handleSettingsClick}>
              <Settings size={20} />
              <span>Settings</span>
            </button>
            <button className="sidebar-item" onClick={handleSupportClick}>
              <HelpCircle size={20} />
              <span>Support</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Area */}
      <main className="main-area">
        <div className="content-scroll">
          <div className="max-w-container">
            {/* Header Section */}
            <div className="page-header">
              <h1 className="page-title">Digital Curator</h1>
              <p className="page-desc">
                The database is speaking. Connect your data source or upload a local dataset to begin the dialogue.
              </p>
            </div>

            {/* Bento Grid layout containing the active mode UI */}
            <div className="bento-grid">
              {activeMode === 'dataset' ? <DatasetMode key={`dataset-${resetKey}`} /> : <SqlMode key={`sql-${resetKey}`} />}
            </div>
            <div className="h-16"></div>
          </div>
        </div>
      </main>
      
      {/* Mobile Nav */}
      <div className="mobile-nav">
        <button className={`mobile-nav-btn ${activeMode === 'dataset' ? 'active' : ''}`} onClick={() => setActiveMode('dataset')}>
          <DatabaseBackup size={24} />
          <span style={{ fontSize: '10px', fontWeight: 'bold' }}>Data</span>
        </button>
        <button className={`mobile-nav-btn ${activeMode === 'sql' ? 'active' : ''}`} onClick={() => setActiveMode('sql')}>
          <TerminalSquare size={24} />
          <span style={{ fontSize: '10px', fontWeight: 'bold' }}>SQL</span>
        </button>
        <button className="mobile-nav-fab" onClick={handleNewAnalysis}>
          <Sparkles size={24} />
        </button>
        <button className="mobile-nav-btn" onClick={handleSettingsClick}>
          <Settings size={24} />
          <span style={{ fontSize: '10px', fontWeight: 'bold' }}>Set</span>
        </button>
        <button className="mobile-nav-btn" onClick={handleSupportClick}>
          <HelpCircle size={24} />
          <span style={{ fontSize: '10px', fontWeight: 'bold' }}>Help</span>
        </button>
      </div>

      {showSupport && (
        <SupportModal onClose={() => setShowSupport(false)} />
      )}
    </div>
  );
}

// -------------------------------------------------------------
// SUPPORT MODAL
// -------------------------------------------------------------
function SupportModal({ onClose }) {
  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', 
      backgroundColor: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', 
      zIndex: 100, display: 'flex', justifyContent: 'center', alignItems: 'center'
    }}>
      <div className="card-glass" style={{ 
        width: '400px', minHeight: 'auto', padding: '2rem', 
        position: 'relative', border: '1px solid var(--primary-container)' 
      }}>
        <button onClick={onClose} style={{ 
          position: 'absolute', top: '1rem', right: '1rem', 
          background: 'transparent', border: 'none', color: 'var(--on-surface)', cursor: 'pointer' 
        }}>
          <X size={24} />
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
          <div className="chat-icon-bg">
            <HelpCircle size={20} color="var(--on-tertiary-container)" />
          </div>
          <h2 className="font-headline text-2xl font-bold">Support & Info</h2>
        </div>
        <p style={{ marginBottom: '1.5rem', color: 'var(--on-surface-variant)', lineHeight: 1.5 }}>
          Need help or want to report an issue? Feel free to reach out directly or check out the project code on GitHub!
        </p>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <a href="mailto:sachingoyal9274@gmail.com" className="btn-secondary" style={{ textDecoration: 'none', textAlign: 'center', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}>
            <span className="material-symbols-outlined">mail</span>
            Contact Sachin Goyal
          </a>
          <a href="https://github.com/SachinGoyal94/PurposePredict_Talk2Data" target="_blank" rel="noreferrer" className="btn-primary" style={{ textDecoration: 'none', textAlign: 'center', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}>
            <span className="material-symbols-outlined">code</span>
            View GitHub Repository
          </a>
        </div>
      </div>
    </div>
  )
}

// -------------------------------------------------------------
// DATASET MODE
// -------------------------------------------------------------
function DatasetMode() {
  const [sessionId, setSessionId] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [chatHistory, setChatHistory] = useState([
    { role: 'ai', text: 'Upload a dataset to begin our dialogue.' }
  ]);
  const [prompt, setPrompt] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch(`${API_BASE_URL}/upload`, { method: 'POST', body: formData });
      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      
      setSessionId(data.session_id);
      toast.success(`Loaded ${data.filename} (${data.row_count} rows)`);
      setChatHistory([
        { role: 'ai', text: `Dataset loaded! Columns identified: ${data.columns.join(', ')}. What would you like to know?` }
      ]);
    } catch (error) {
      toast.error('Failed to upload dataset');
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!prompt.trim() || !sessionId) return;
    
    const userText = prompt;
    setChatHistory(prev => [...prev, { role: 'user', text: userText }]);
    setPrompt("");
    setIsQuerying(true);

    try {
      const res = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, question: userText })
      });
      if (!res.ok) throw new Error("Query failed");
      const data = await res.json();
      
      const newAiMsg = {
        role: 'ai',
        text: data.answer,
        chart: data.chart?.image_b64 ? data.chart.image_b64 : null,
        sourceRef: data.source_ref,
        data: data.data,
      };
      setChatHistory(prev => [...prev, newAiMsg]);
    } catch (err) {
      toast.error("Failed to fetch response");
      setChatHistory(prev => [...prev, { role: 'ai', text: "Error: Could not retrieve answer." }]);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <>
      <div className="card card-upload col-12 lg-col-12" style={{ marginBottom: '1rem' }}>
        <div className="card-upload-inner">
          <div className="card-upload-header">
            <h2 className="font-headline text-2xl font-semibold">Local Repository</h2>
            <span className="badge">Dataset Ready</span>
          </div>
          
          <input 
            type="file" 
            accept=".csv, .xlsx" 
            style={{ display: 'none' }} 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
          />
          <div className="drop-zone" onClick={() => fileInputRef.current?.click()}>
            <div className="drop-icon-box">
              {isUploading ? (
                <div className="loading-spinner" style={{ width: '2rem', height: '2rem', borderTopColor: 'var(--primary)' }} />
              ) : (
                <UploadCloud size={32} className="drop-icon" />
              )}
            </div>
            <h3 className="drop-title">
              {isUploading ? "Processing Dataset..." : "Drag & Drop Dataset"}
            </h3>
            <p className="drop-desc">Support for .csv and .xlsx files</p>
            <button className="btn-secondary" disabled={isUploading}>
              {isUploading ? "Uploading..." : "Browse Files"}
            </button>
          </div>
        </div>
      </div>

      <div className="col-12 lg-col-12">
        <ChatInterface 
          chatHistory={chatHistory} 
          prompt={prompt} 
          setPrompt={setPrompt} 
          handleQuery={handleQuery} 
          isLoading={isQuerying} 
          disabled={!sessionId || isUploading}
          placeholder={sessionId ? "Ask about your dataset..." : "Please upload a dataset first..."}
        />
      </div>
    </>
  );
}

// -------------------------------------------------------------
// SQL DATABASE MODE
// -------------------------------------------------------------
function SqlMode() {
  const [credentials, setCredentials] = useState({
    mysql_host: '',
    mysql_port: '3306',
    mysql_user: '',
    mysql_password: '',
    mysql_db: ''
  });
  
  const [isConfigured, setIsConfigured] = useState(false);
  const [chatHistory, setChatHistory] = useState([
    { role: 'ai', text: 'Enter database credentials on the left and establish connection to begin.' }
  ]);
  const [prompt, setPrompt] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);

  const handleConnect = (e) => {
    e.preventDefault();
    if (!credentials.mysql_host || !credentials.mysql_user) {
      toast.error("Please fill required fields (Host, User)");
      return;
    }
    setIsConfigured(true);
    toast.success("Connection credentials saved");
    setChatHistory([{ role: 'ai', text: `Connected to ${credentials.mysql_host}! How can I help you query the database today?` }]);
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    if (!isConfigured) {
      toast.error("Configure DB credentials first!");
      return;
    }

    const userText = prompt;
    setChatHistory(prev => [...prev, { role: 'user', text: userText }]);
    setPrompt("");
    setIsQuerying(true);

    try {
      const payload = { query: userText, ...credentials };
      const res = await fetch(`${API_BASE_URL}/db/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("DB Query failed");
      const data = await res.json();
      
      setChatHistory(prev => [...prev, { role: 'ai', text: data.response || "Query successful." }]);
    } catch (err) {
      toast.error("Query failed");
      setChatHistory(prev => [...prev, { role: 'ai', text: "Error: Could not retrieve answer from SQL database." }]);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <>
      <div className="card card-sql col-12 lg-col-4">
        <div className="sql-header">
          <Database className="sql-icon fill" size={24} />
          <h2 className="sql-title">SQL Gateway</h2>
        </div>

        <form onSubmit={handleConnect} className="flex flex-col gap-4" style={{ flex: 1 }}>
          <div className="input-group">
            <label className="input-label">Endpoint Host</label>
            <input 
              className="input-field" 
              placeholder="db.server.internal" 
              type="text" 
              value={credentials.mysql_host}
              onChange={e => setCredentials({...credentials, mysql_host: e.target.value})}
            />
          </div>
          
          <div className="grid-cols-2">
            <div className="input-group">
              <label className="input-label">Username</label>
              <input 
                className="input-field" 
                placeholder="admin" 
                type="text" 
                value={credentials.mysql_user}
                onChange={e => setCredentials({...credentials, mysql_user: e.target.value})}
              />
            </div>
            <div className="input-group">
              <label className="input-label">Password</label>
              <input 
                className="input-field" 
                placeholder="••••••••" 
                type="password"
                value={credentials.mysql_password}
                onChange={e => setCredentials({...credentials, mysql_password: e.target.value})} 
              />
            </div>
          </div>
          
          <div className="input-group">
            <label className="input-label">Database Name</label>
            <input 
              className="input-field" 
              placeholder="production_v2" 
              type="text" 
              value={credentials.mysql_db}
              onChange={e => setCredentials({...credentials, mysql_db: e.target.value})}
            />
          </div>

          <div className="input-group">
            <label className="input-label">Port</label>
            <input 
              className="input-field" 
              placeholder="3306" 
              type="text" 
              value={credentials.mysql_port}
              onChange={e => setCredentials({...credentials, mysql_port: e.target.value})}
            />
          </div>

          <button type="submit" className="btn-outline">
            <LinkIcon size={20} />
            {isConfigured ? 'Update Configuration' : 'Establish Connection'}
          </button>
        </form>
      </div>

      <div className="col-12 lg-col-8">
        <ChatInterface 
          chatHistory={chatHistory} 
          prompt={prompt} 
          setPrompt={setPrompt} 
          handleQuery={handleQuery} 
          isLoading={isQuerying} 
          disabled={!isConfigured}
          placeholder={isConfigured ? "Ask the database..." : "Enter credentials first..."}
        />
      </div>
    </>
  );
}

// -------------------------------------------------------------
// CHAT INTERFACE COMPONENT
// -------------------------------------------------------------
function ChatInterface({ chatHistory, prompt, setPrompt, handleQuery, isLoading, disabled, placeholder }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory, isLoading]);

  return (
    <div className="card card-glass" style={{ height: '100%' }}>
      <div className="chat-header">
        <div className="chat-icon-bg">
          <Sparkles size={20} color="var(--on-tertiary-container)" />
        </div>
        <div>
          <h3 className="chat-title">Conversational Layer</h3>
          <p className="chat-desc">Ask natural language questions about your data</p>
        </div>
      </div>

      <div className="chat-history" ref={scrollRef}>
        {chatHistory.map((msg, idx) => (
          <div key={idx} className={msg.role === 'user' ? "msg-user" : "msg-ai"}>
            {msg.role === 'user' ? (
              <div className="msg-bubble-user">
                {msg.text}
              </div>
            ) : (
              <div className="msg-content-ai">
                <div className="msg-bubble-ai">
                  {msg.text}
                </div>
                
                {msg.chart && (
                  <img 
                    src={`data:image/png;base64,${msg.chart}`} 
                    alt="Auto-generated chart" 
                    style={{ borderRadius: 'var(--border-radius-xl)', marginTop: '0.5rem', maxWidth: '100%', boxShadow: '0 4px 12px rgba(0,0,0,0.2)' }} 
                  />
                )}

                {msg.sourceRef && msg.sourceRef.length > 0 && (
                  <div className="insight-chip">
                    <Zap size={14} />
                    Sources: {msg.sourceRef.join(', ')}
                  </div>
                )}

                {msg.data && msg.data.length > 0 && (
                  <div className="table-container">
                    <table className="data-table">
                      <thead>
                        <tr>
                          {Object.keys(msg.data[0]).map((key) => (
                            <th key={key}>{key}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {msg.data.map((row, i) => (
                          <tr key={i}>
                            {Object.values(row).map((val, cellIdx) => (
                              <td key={cellIdx} className={cellIdx === 0 ? "td-highlight" : ""}>{String(val)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="msg-ai loader-pulse">
            <div className="msg-content-ai">
              <div className="msg-bubble-ai" style={{ width: 'fit-content', padding: '0.75rem 1.25rem' }}>
                <span className="loading-spinner" style={{ display: 'inline-block', width: '1rem', height: '1rem', verticalAlign: 'middle', marginRight: '0.5rem' }}></span>
                Analyzing data...
              </div>
            </div>
          </div>
        )}
      </div>

      <form className="chat-input-wrapper" onSubmit={handleQuery}>
        <div className="chat-input-glow"></div>
        <div className="chat-input-inner">
          <button type="button" className="btn-icon">
            <Paperclip size={20} />
          </button>
          <input 
            className="chat-input" 
            placeholder={placeholder} 
            type="text" 
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={disabled || isLoading}
          />
          <button type="submit" className="btn-send" disabled={disabled || isLoading || !prompt.trim()}>
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
