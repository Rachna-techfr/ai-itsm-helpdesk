import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ChatScreen from './components/ChatScreen';
import DashboardScreen from './components/DashboardScreen';
import AnalysisScreen from './components/AnalysisScreen';
import KnowledgeScreen from './components/KnowledgeScreen';
import { fetchHealth, resetStoreSeed } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [health, setHealth] = useState(null);
  const [toast, setToast] = useState(null);

  const loadHealth = async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      console.error('Failed to load system health:', err);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  const handleReset = async () => {
    if (!window.confirm('Reset all demonstration tickets and logs to default seed state?')) return;
    try {
      await resetStoreSeed();
      await loadHealth();
      setToast('System data reset to default seed state successfully.');
      setTimeout(() => setToast(null), 3500);
    } catch (err) {
      alert('Failed to reset store: ' + err.message);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-primary)' }}>
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        onReset={handleReset}
      />

      {/* Toast Notification */}
      {toast && (
        <div style={{
          position: 'fixed',
          bottom: '1.5rem',
          right: '1.5rem',
          backgroundColor: '#064e3b',
          color: '#34d399',
          border: '1px solid #059669',
          padding: '0.75rem 1.25rem',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          zIndex: 100,
          fontSize: '0.85rem',
          fontWeight: 600,
        }}>
          {toast}
        </div>
      )}

      {/* Main Screen Container */}
      <main style={{ flex: 1, padding: '0.5rem 0' }}>
        {activeTab === 'chat' && (
          <ChatScreen onTicketCreated={() => loadHealth()} />
        )}
        {activeTab === 'dashboard' && (
          <DashboardScreen onSelectTicket={(t) => setActiveTab('analysis')} />
        )}
        {activeTab === 'analysis' && (
          <AnalysisScreen />
        )}
        {activeTab === 'kb' && (
          <KnowledgeScreen />
        )}
      </main>
    </div>
  );
}
