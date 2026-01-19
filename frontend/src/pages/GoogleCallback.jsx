import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { googleAPI } from '../services/api';
import { setToken } from '../utils/auth';

function GoogleCallback() {
  const [status, setStatus] = useState('Processing...');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      // Get authorization code from URL
      const params = new URLSearchParams(window.location.search);
      const code = params.get('code');
      const error = params.get('error');

      if (error) {
        setError(`OAuth error: ${error}`);
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      if (!code) {
        setError('No authorization code received');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      try {
        setStatus('Connecting your Google account...');
        
        // Send code to backend
        const response = await googleAPI.handleCallback(code);
        
        // Save JWT token
        setToken(response.data.access_token);
        
        setStatus('Success! Redirecting to chat...');
        setTimeout(() => navigate('/chat'), 1000);
        
      } catch (err) {
        console.error('Callback error:', err);
        setError(err.response?.data?.detail || 'Failed to connect Google account');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [navigate]);

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.spinner}></div>
        <h2 style={styles.title}>{status}</h2>
        {error && <p style={styles.error}>{error}</p>}
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  card: {
    background: 'white',
    padding: '40px',
    borderRadius: '12px',
    boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
    textAlign: 'center',
    maxWidth: '400px',
  },
  spinner: {
    border: '4px solid #f3f3f3',
    borderTop: '4px solid #667eea',
    borderRadius: '50%',
    width: '50px',
    height: '50px',
    animation: 'spin 1s linear infinite',
    margin: '0 auto 20px',
  },
  title: {
    fontSize: '20px',
    color: '#333',
    marginBottom: '10px',
  },
  error: {
    color: '#c33',
    fontSize: '14px',
    marginTop: '10px',
  },
};

// Add keyframes animation
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;
document.head.appendChild(styleSheet);

export default GoogleCallback;