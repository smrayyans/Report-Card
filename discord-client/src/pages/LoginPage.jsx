import { useEffect, useRef, useState } from 'react';
import { Navigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import useToast from '../hooks/useToast';
import api, { getApiBase, setApiBase } from '../services/api';

export default function LoginPage() {
  const pushToast = useToast();
  const user = useAuthStore((state) => state.user);
  const login = useAuthStore((state) => state.login);
  const loading = useAuthStore((state) => state.loading);

  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [connectionOpen, setConnectionOpen] = useState(false);
  const [serverInput, setServerInput] = useState(getApiBase());
  const [healthStatus, setHealthStatus] = useState(null);
  const [serverReady, setServerReady] = useState(false);
  const [serverChecking, setServerChecking] = useState(true);
  const [connectionMode, setConnectionMode] = useState('host');
  const [hostIpInput, setHostIpInput] = useState('');
  const [healthProgress, setHealthProgress] = useState(0);
  const [healthElapsed, setHealthElapsed] = useState(0);
  const [healthError, setHealthError] = useState('');
  const healthStartRef = useRef(Date.now());

  useEffect(() => {
    if (!connectionOpen) {
      setServerInput(getApiBase());
      setHealthStatus(null);
    }
  }, [connectionOpen]);

  useEffect(() => {
    let cancelled = false;

    const pollHealth = async () => {
      setServerChecking(true);
      healthStartRef.current = Date.now();
      setHealthElapsed(0);
      setHealthProgress(0);
      setHealthError('');
      const maxAttempts = 10;
      for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
        try {
          const response = await api.get('/health');
          if (response.data?.status === 'ok') {
            if (!cancelled) {
              setServerReady(true);
              setServerChecking(false);
              setHealthProgress(100);
              setHealthError('');
            }
            return;
          }
        } catch (error) {
          if (!cancelled) {
            setHealthError(error?.response?.data?.detail || error?.message || '');
          }
        }
        if (!cancelled) {
          setHealthProgress(Math.round(((attempt + 1) / maxAttempts) * 100));
          setHealthElapsed(Math.round((Date.now() - healthStartRef.current) / 1000));
        }
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
      if (!cancelled) {
        setServerReady(false);
        setServerChecking(false);
        setHealthElapsed(Math.round((Date.now() - healthStartRef.current) / 1000));
      }
    };

    pollHealth();
    const intervalId = setInterval(pollHealth, 8000);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [serverInput]);

  useEffect(() => {
    const loadConfig = async () => {
      const storedMode = localStorage.getItem('faizan-connection-mode');
      const storedIp = localStorage.getItem('faizan-host-ip');
      if (storedMode) {
        setConnectionMode(storedMode);
      }
      if (storedIp) {
        setHostIpInput(storedIp);
      }
      if (window?.desktop?.getConnectionConfig) {
        const saved = await window.desktop.getConnectionConfig();
        if (saved?.mode) {
          setConnectionMode(saved.mode);
        }
        if (saved?.hostIp) {
          setHostIpInput(saved.hostIp);
        }
      }
    };
    loadConfig();
  }, []);

  useEffect(() => {
    if (serverReady) {
      const fetchConfig = async () => {
        try {
          const { data } = await api.get('/db/config');
          if (data?.host && data.host !== '127.0.0.1' && data.host !== 'localhost') {
            setConnectionMode('client');
            setHostIpInput(data.host);
          } else {
            setConnectionMode('host');
          }
        } catch (error) {
          console.error('Failed to sync initial DB config:', error);
        }
      };
      fetchConfig();
    }
  }, [serverReady]);

  const handleTestConnection = async () => {
    try {
      const response = await api.get('/health');
      if (response.data?.status === 'ok') {
        setHealthStatus('ok');
        setHealthError('');
        pushToast({ type: 'success', title: 'Connected', message: 'Server is reachable.' });
      } else {
        setHealthStatus('fail');
        setHealthError('Server responded unexpectedly.');
        pushToast({ type: 'error', title: 'Not ready', message: 'Server responded unexpectedly.' });
      }
    } catch (error) {
      setHealthStatus('fail');
      setHealthError(error.response?.data?.detail || error.message);
      pushToast({
        type: 'error',
        title: 'Connection failed',
        message: error.response?.data?.detail || 'Could not reach the server.',
      });
    }
  };

  const handleSaveServer = () => {
    const nextBase = setApiBase(serverInput);
    setServerInput(nextBase);
    pushToast({ type: 'success', title: 'Saved', message: `Server set to ${nextBase}.` });
  };

  const handleSaveConnection = async () => {
    // 1. Save UI preferences locally
    localStorage.setItem('faizan-connection-mode', connectionMode);
    localStorage.setItem('faizan-host-ip', hostIpInput.trim());
    
    if (window?.desktop?.saveConnectionConfig) {
      await window.desktop.saveConnectionConfig({
        mode: connectionMode,
        hostIp: hostIpInput.trim(),
        updatedAt: new Date().toISOString(),
      });
    }

    // 2. Update Backend DB Config
    try {
      const { data: currentConfig } = await api.get('/db/config');
      const newHost = connectionMode === 'host' ? '127.0.0.1' : hostIpInput.trim();
      
      if (!newHost) {
        pushToast({ type: 'warning', title: 'Invalid IP', message: 'Please enter a valid Host IP.' });
        return;
      }

      await api.put('/db/config', { ...currentConfig, host: newHost });
      pushToast({ type: 'success', title: 'Connection Saved', message: `Database host set to ${newHost}` });
    } catch (error) {
      console.error(error);
      pushToast({ type: 'error', title: 'Save Failed', message: 'Could not update backend configuration.' });
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!credentials.username || !credentials.password) {
      pushToast({ type: 'warning', title: 'Missing info', message: 'Please enter both username and password.' });
      return;
    }

    try {
      await login(credentials.username, credentials.password);
      pushToast({ type: 'success', title: 'Welcome back', message: 'Authentication successful.' });
    } catch (error) {
      pushToast({ type: 'error', title: 'Login failed', message: error.message });
    }
  };

  if (user?.user_id) {
    return <Navigate to="/students" replace />;
  }

  return (
    <div className="login-screen">
      <div className="login-card glass-surface">
        <div className="login-branding">
          <p className="eyebrow">Faizan Academy</p>
          <h2>Report Studio</h2>
          <p className="muted">Sign in with your staff credentials to enter the Discord-quality console.</p>
        </div>
        <form className="login-form" onSubmit={handleSubmit}>
          <div className={`login-status ${serverReady ? 'is-ok' : 'is-warn'}`}>
            <span className={`login-status-icon ${serverChecking ? 'is-spin' : ''}`} />
            <span>
              {serverChecking && `Starting server... (${healthElapsed}s)`}
              {!serverChecking && serverReady && 'Server ready'}
              {!serverChecking && !serverReady && `Server not reachable (${healthElapsed}s)`}
            </span>
          </div>
          <div className="login-progress">
            <div className="login-progress-bar" style={{ width: `${healthProgress}%` }} />
          </div>
          {!serverChecking && !serverReady && healthError && (
            <div className="login-status-error">{healthError}</div>
          )}
          <div className="login-connection-mode">
            <button
              type="button"
              className={`btn ${connectionMode === 'host' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setConnectionMode('host')}
            >
              This PC is Host
            </button>
            <button
              type="button"
              className={`btn ${connectionMode === 'client' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setConnectionMode('client')}
            >
              This PC is User
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={handleSaveConnection}
            >
              Save Mode
            </button>
          </div>
          {connectionMode === 'client' && (
            <label>
              <span>Host IP Address</span>
              <input
                className="input dark"
                type="text"
                value={hostIpInput}
                onChange={(event) => setHostIpInput(event.target.value)}
                placeholder="e.g., 192.168.0.x"
              />
            </label>
          )}
          <label>
            <span>Username</span>
            <input
              className="input dark"
              type="text"
              value={credentials.username}
              onChange={(event) => setCredentials((prev) => ({ ...prev, username: event.target.value }))}
              placeholder="e.g., admin"
            />
          </label>
          <label>
            <span>Password</span>
            <input
              className="input dark"
              type="password"
              value={credentials.password}
              onChange={(event) => setCredentials((prev) => ({ ...prev, password: event.target.value }))}
              placeholder="******"
            />
          </label>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Authenticating...' : 'Enter Studio'}
          </button>
        </form>
        <button className="btn btn-ghost" type="button" onClick={() => setConnectionOpen(true)}>
          Connection Settings
        </button>
      </div>
      {connectionOpen && (
        <div style={{ position: 'fixed', inset: 0, display: 'grid', placeItems: 'center', overflow: 'hidden', zIndex: 20 }}>
          <div className="modal-backdrop" onClick={() => setConnectionOpen(false)} />
          <div className="modal-panel glass-surface" onClick={(e) => e.stopPropagation()}>
            <header>
              <div>
                <p className="eyebrow">Connection</p>
                <h3>Server endpoint</h3>
              </div>
              <button className="btn btn-text" onClick={() => setConnectionOpen(false)}>
                Close
              </button>
            </header>
            <label>
              <span>API Base URL</span>
              <input
                className="input dark"
                value={serverInput}
                onChange={(event) => setServerInput(event.target.value)}
                placeholder="http://127.0.0.1:8000"
              />
            </label>
            <footer className="modal-footer">
              <div className="remarks-actions">
                <button className="btn btn-secondary" type="button" onClick={handleTestConnection}>
                  Test Connection
                </button>
                {healthStatus === 'ok' && <span className="muted">Server reachable</span>}
                {healthStatus === 'fail' && <span className="muted">Server unreachable</span>}
              </div>
              <button className="btn btn-primary" type="button" onClick={handleSaveServer}>
                Save
              </button>
            </footer>
          </div>
        </div>
      )}
    </div>
  );
}

