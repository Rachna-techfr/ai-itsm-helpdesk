import React from 'react';
import { Bot, LayoutDashboard, Brain, BookOpen, RefreshCw, Server, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, health, onReset }) {
  return (
    <header style={{
      backgroundColor: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-color)',
      padding: '0.875rem 1.75rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 40,
    }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
          color: '#fff',
          padding: '0.5rem',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
        }}>
          <Bot size={22} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontWeight: 800, fontSize: '1.15rem', letterSpacing: '-0.02em', color: '#fff' }}>
              SORIM.<span style={{ color: '#38bdf8' }}>AI</span>
            </span>
            <span style={{
              fontSize: '0.65rem',
              backgroundColor: '#1e3a5f',
              color: '#38bdf8',
              fontWeight: 700,
              padding: '0.15rem 0.5rem',
              borderRadius: '9999px',
              border: '1px solid #2563eb40',
              textTransform: 'uppercase',
            }}>
              ITSM AI Agent
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Autonomous Helpdesk & ServiceNow Integration
          </p>
        </div>
      </div>

      {/* Nav Tabs */}
      <nav style={{ display: 'flex', gap: '0.35rem', backgroundColor: 'var(--bg-primary)', padding: '0.3rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
        {[
          { id: 'chat', label: 'Employee Self-Service', icon: Bot },
          { id: 'dashboard', label: 'ITSM Dashboard', icon: LayoutDashboard },
          { id: 'analysis', label: 'AI Analysis & Audit', icon: Brain },
          { id: 'kb', label: 'Knowledge Base (RAG)', icon: BookOpen },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.55rem 0.95rem',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.85rem',
                transition: 'all 0.15s ease',
                backgroundColor: isActive ? 'var(--accent-blue)' : 'transparent',
                color: isActive ? '#fff' : 'var(--text-secondary)',
                boxShadow: isActive ? '0 2px 8px rgba(59, 130, 246, 0.4)' : 'none',
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Health status & Seed reset */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.75rem',
          backgroundColor: '#0f291e',
          color: '#34d399',
          padding: '0.35rem 0.75rem',
          borderRadius: '9999px',
          border: '1px solid #05966940',
        }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block' }} />
          <span>{health?.embeddings || 'MiniLM'}</span>
          <span style={{ color: '#059669' }}>•</span>
          <span>{health?.servicenow?.includes('Live') ? 'ServiceNow Live' : 'ServiceNow Mock'}</span>
        </div>

        <button
          onClick={onReset}
          title="Reset demonstration data"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.45rem 0.75rem',
            borderRadius: '8px',
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border-color)',
            fontSize: '0.75rem',
            cursor: 'pointer',
            transition: 'background 0.2s',
          }}
        >
          <RefreshCw size={13} />
          Reset Demo
        </button>
      </div>
    </header>
  );
}

