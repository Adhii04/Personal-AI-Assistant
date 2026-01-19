import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { chatAPI, googleAPI, gmailAPI, calendarAPI } from '../services/api';
import { removeToken } from '../utils/auth';

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [googleConnected, setGoogleConnected] = useState(false);
  const [showGooglePrompt, setShowGooglePrompt] = useState(false);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  // Load chat history and check Google connection on mount
  useEffect(() => {
    loadHistory();
    checkGoogleConnection();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadHistory = async () => {
    try {
      const response = await chatAPI.getHistory();
      setMessages(response.data);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const checkGoogleConnection = async () => {
    try {
      const response = await googleAPI.getConnectionStatus();
      setGoogleConnected(response.data.is_connected);
      
      // Show prompt if not connected
      if (!response.data.is_connected) {
        setTimeout(() => setShowGooglePrompt(true), 2000);
      }
    } catch (err) {
      console.error('Failed to check Google connection:', err);
    }
  };

  const handleConnectGoogle = async () => {
    try {
      const response = await googleAPI.getAuthUrl();
      window.location.href = response.data.auth_url;
    } catch (err) {
      setError('Failed to connect Google account');
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setError('');
    setLoading(true);

    // Add user message optimistically
    const tempUserMsg = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      // Use tools endpoint if Google is connected
      const endpoint = googleConnected ? chatAPI.sendMessageWithTools : chatAPI.sendMessage;
      const response = await endpoint(userMessage);
      
      // Add assistant response
      const assistantMsg = {
        id: response.data.message_id,
        role: 'assistant',
        content: response.data.response,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send message');
      // Remove the optimistic user message on error
      setMessages((prev) => prev.filter((msg) => msg.id !== tempUserMsg.id));
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    removeToken();
    navigate('/login');
  };

  const handleClearHistory = async () => {
    if (!window.confirm('Clear all chat history?')) return;
    
    try {
      await chatAPI.clearHistory();
      setMessages([]);
    } catch (err) {
      setError('Failed to clear history');
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.headerTitle}>AI Assistant</h1>
          {googleConnected && (
            <span style={styles.connectedBadge}>✓ Google Connected</span>
          )}
        </div>
        <div style={styles.headerButtons}>
          <button onClick={handleClearHistory} style={styles.clearButton}>
            Clear History
          </button>
          <button onClick={handleLogout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </div>

      {/* Google Connection Prompt */}
      {showGooglePrompt && !googleConnected && (
        <div style={styles.googlePrompt}>
          <div style={styles.promptContent}>
            <h3 style={styles.promptTitle}>🚀 Unlock Full Power!</h3>
            <p style={styles.promptText}>
              Connect your Google account to let me access your Gmail and Calendar
            </p>
            <div style={styles.promptButtons}>
              <button onClick={handleConnectGoogle} style={styles.connectButton}>
                Connect Google
              </button>
              <button onClick={() => setShowGooglePrompt(false)} style={styles.dismissButton}>
                Maybe Later
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div style={styles.messagesContainer}>
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            <h2 style={styles.emptyTitle}>👋 Hello!</h2>
            <p style={styles.emptyText}>
              I'm your AI assistant. Ask me anything!
            </p>
            {googleConnected && (
              <p style={styles.emptyHint}>
                💡 Try: "What's in my inbox?" or "What's on my schedule today?"
              </p>
            )}
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              ...styles.message,
              ...(msg.role === 'user' ? styles.userMessage : styles.assistantMessage),
            }}
          >
            <div style={styles.messageRole}>
              {msg.role === 'user' ? '👤 You' : '🤖 Assistant'}
            </div>
            <div style={styles.messageContent}>{msg.content}</div>
          </div>
        ))}

        {loading && (
          <div style={{ ...styles.message, ...styles.assistantMessage }}>
            <div style={styles.messageRole}>🤖 Assistant</div>
            <div style={styles.messageContent}>
              {googleConnected ? 'Checking your Gmail and Calendar...' : 'Thinking...'}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error */}
      {error && <div style={styles.error}>{error}</div>}

      {/* Input */}
      <form onSubmit={handleSend} style={styles.inputContainer}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            googleConnected
              ? "Ask about emails, calendar, or anything..."
              : "Type your message..."
          }
          style={styles.input}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            ...styles.sendButton,
            ...(loading || !input.trim() ? styles.sendButtonDisabled : {}),
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
}

const styles = {
  container: {
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    background: '#f5f5f5',
  },
  header: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
  },
  headerTitle: {
    margin: 0,
    fontSize: '24px',
  },
  connectedBadge: {
    fontSize: '12px',
    background: 'rgba(255,255,255,0.2)',
    padding: '4px 8px',
    borderRadius: '4px',
    marginLeft: '10px',
  },
  headerButtons: {
    display: 'flex',
    gap: '10px',
  },
  clearButton: {
    background: 'rgba(255,255,255,0.2)',
    color: 'white',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  logoutButton: {
    background: 'rgba(255,255,255,0.9)',
    color: '#667eea',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600',
  },
  googlePrompt: {
    background: '#fff3cd',
    borderBottom: '1px solid #ffc107',
    padding: '16px',
  },
  promptContent: {
    maxWidth: '600px',
    margin: '0 auto',
  },
  promptTitle: {
    margin: '0 0 8px 0',
    fontSize: '18px',
    color: '#856404',
  },
  promptText: {
    margin: '0 0 16px 0',
    color: '#856404',
  },
  promptButtons: {
    display: 'flex',
    gap: '10px',
  },
  connectButton: {
    background: '#667eea',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: '600',
  },
  dismissButton: {
    background: 'transparent',
    color: '#856404',
    border: '1px solid #856404',
    padding: '10px 20px',
    borderRadius: '6px',
    cursor: 'pointer',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  emptyState: {
    textAlign: 'center',
    marginTop: '100px',
  },
  emptyTitle: {
    fontSize: '32px',
    marginBottom: '10px',
  },
  emptyText: {
    color: '#666',
    fontSize: '18px',
  },
  emptyHint: {
    color: '#667eea',
    fontSize: '14px',
    marginTop: '20px',
    fontStyle: 'italic',
  },
  message: {
    padding: '16px',
    borderRadius: '12px',
    maxWidth: '70%',
    wordWrap: 'break-word',
  },
  userMessage: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    alignSelf: 'flex-end',
    marginLeft: 'auto',
  },
  assistantMessage: {
    background: 'white',
    color: '#333',
    alignSelf: 'flex-start',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  messageRole: {
    fontSize: '12px',
    fontWeight: '600',
    marginBottom: '6px',
    opacity: 0.8,
  },
  messageContent: {
    fontSize: '15px',
    lineHeight: '1.5',
    whiteSpace: 'pre-wrap',
  },
  error: {
    background: '#fee',
    color: '#c33',
    padding: '12px 20px',
    margin: '0 20px',
    borderRadius: '6px',
    fontSize: '14px',
  },
  inputContainer: {
    padding: '20px',
    background: 'white',
    borderTop: '1px solid #ddd',
    display: 'flex',
    gap: '10px',
  },
  input: {
    flex: 1,
    padding: '14px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '16px',
    outline: 'none',
  },
  sendButton: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    padding: '14px 32px',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  sendButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
};

export default Chat;