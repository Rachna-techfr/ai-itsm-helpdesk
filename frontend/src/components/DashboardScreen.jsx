import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Package,
  TrendingUp,
  Filter,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Check,
  X,
  Search,
  Eye,
} from 'lucide-react';
import { fetchTickets, fetchRequests, fetchDashboardStats, decideSoftwareRequest, escalateTicket } from '../api';

export default function DashboardScreen({ onSelectTicket }) {
  const [stats, setStats] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [requests, setRequests] = useState([]);
  const [filter, setFilter] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sData, tData, rData] = await Promise.all([
        fetchDashboardStats(),
        fetchTickets(filter),
        fetchRequests(),
      ]);
      setStats(sData);
      setTickets(tData);
      setRequests(rData);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filter]);

  const handleDecideRequest = async (number, decision) => {
    try {
      await decideSoftwareRequest(number, decision);
      loadData();
    } catch (err) {
      alert('Error updating request: ' + err.message);
    }
  };

  const handleEscalate = async (number) => {
    try {
      await escalateTicket(number, 'Analyst escalated from ITSM Dashboard');
      loadData();
    } catch (err) {
      alert('Error escalating ticket: ' + err.message);
    }
  };

  const filteredTickets = tickets.filter((t) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      t.number.toLowerCase().includes(term) ||
      t.caller_name.toLowerCase().includes(term) ||
      t.description.toLowerCase().includes(term) ||
      t.classification?.summary?.toLowerCase().includes(term)
    );
  });

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* KPI METRIC CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        {[
          { label: 'Total Incidents', value: stats?.total_tickets ?? '--', sub: 'Logged in ServiceNow', color: '#3b82f6', icon: LayoutDashboard },
          { label: 'Active Open', value: stats?.open_tickets ?? '--', sub: 'Requires Attention', color: '#f59e0b', icon: Clock },
          { label: 'AI Self-Healed', value: stats?.ai_resolved ?? '--', sub: 'Zero-touch resolution', color: '#10b981', icon: CheckCircle2 },
          { label: 'Escalated Tier-2', value: stats?.escalated ?? '--', sub: 'Human in the loop', color: '#f43f5e', icon: AlertTriangle },
          { label: 'Software Requests', value: stats?.software_requests_total ?? '--', sub: `${stats?.software_requests_completed ?? 0} Completed`, color: '#06b6d4', icon: Package },
          { label: 'Autonomous Rate', value: `${stats?.automation_rate ?? 0}%`, sub: `Avg MTTR: ${stats?.mttr_minutes ?? 1.4} min`, color: '#8b5cf6', icon: TrendingUp },
        ].map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={i}
              style={{
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                padding: '1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{card.label}</span>
                <div style={{ padding: '0.35rem', borderRadius: '6px', backgroundColor: `${card.color}20`, color: card.color }}>
                  <Icon size={16} />
                </div>
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.02em' }}>
                {card.value}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                {card.sub}
              </div>
            </div>
          );
        })}
      </div>

      {/* MAIN TWO-COLUMN CONTENT */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem' }}>
        {/* INCIDENTS TABLE */}
        <div style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}>
          {/* Table Header Controls */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>ServiceNow Incidents Queue</h2>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Real-time synchronization with ServiceNow Table API</p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {/* Search */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', backgroundColor: 'var(--bg-card)', padding: '0.35rem 0.65rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <Search size={14} style={{ color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Filter tickets..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{ backgroundColor: 'transparent', border: 'none', outline: 'none', color: '#fff', fontSize: '0.78rem', width: '120px' }}
                />
              </div>

              {/* Status Filters */}
              <div style={{ display: 'flex', gap: '0.25rem', backgroundColor: 'var(--bg-card)', padding: '0.2rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                {['All', 'Open', 'Resolved', 'Escalated'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setFilter(st)}
                    style={{
                      padding: '0.25rem 0.6rem',
                      borderRadius: '6px',
                      border: 'none',
                      backgroundColor: filter === st ? 'var(--accent-blue)' : 'transparent',
                      color: filter === st ? '#fff' : 'var(--text-secondary)',
                      fontSize: '0.72rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Table */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)', fontSize: '0.72rem', textTransform: 'uppercase' }}>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Ticket #</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Caller</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Category</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Summary</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Priority</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>State</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>AI Self-Heal</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredTickets.map((t) => {
                  const isResolved = t.status === 'Resolved';
                  const isEscalated = t.status === 'Escalated';
                  return (
                    <tr
                      key={t.number}
                      style={{
                        borderBottom: '1px solid var(--border-color)',
                        backgroundColor: 'transparent',
                        transition: 'background 0.15s ease',
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-card)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                    >
                      <td style={{ padding: '0.6rem 0.75rem', fontWeight: 700, color: '#38bdf8' }}>
                        {t.number}
                      </td>
                      <td style={{ padding: '0.6rem 0.75rem' }}>
                        <div>{t.caller_name}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{t.department}</div>
                      </td>
                      <td style={{ padding: '0.6rem 0.75rem', color: 'var(--text-secondary)' }}>
                        {t.classification?.category} / {t.classification?.subcategory}
                      </td>
                      <td style={{ padding: '0.6rem 0.75rem', maxWidth: '240px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {t.classification?.summary || t.description}
                      </td>
                      <td style={{ padding: '0.6rem 0.75rem' }}>
                        <span style={{
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          padding: '0.15rem 0.45rem',
                          borderRadius: '4px',
                          backgroundColor: t.classification?.priority === 'P1' ? '#7f1d1d' : t.classification?.priority === 'P2' ? '#7c2d12' : '#1e293b',
                          color: t.classification?.priority === 'P1' ? '#fca5a5' : t.classification?.priority === 'P2' ? '#fdba74' : '#94a3b8',
                        }}>
                          {t.classification?.priority || 'P3'}
                        </span>
                      </td>
                      <td style={{ padding: '0.6rem 0.75rem' }}>
                        <span style={{
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          padding: '0.15rem 0.45rem',
                          borderRadius: '4px',
                          backgroundColor: isResolved ? '#064e3b' : isEscalated ? '#7f1d1d' : '#1e3a8a',
                          color: isResolved ? '#34d399' : isEscalated ? '#fca5a5' : '#93c5fd',
                        }}>
                          {t.status}
                        </span>
                      </td>
                      <td style={{ padding: '0.6rem 0.75rem' }}>
                        {t.ai_resolved ? (
                          <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.72rem', fontWeight: 600 }}>
                            <CheckCircle2 size={13} /> Auto
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Manual</span>
                        )}
                      </td>
                      <td style={{ padding: '0.6rem 0.75rem' }}>
                        <div style={{ display: 'flex', gap: '0.35rem' }}>
                          <button
                            onClick={() => setSelectedTicket(t)}
                            title="Inspect details"
                            style={{
                              backgroundColor: 'var(--bg-card)',
                              border: '1px solid var(--border-color)',
                              color: 'var(--text-secondary)',
                              padding: '0.3rem',
                              borderRadius: '4px',
                              cursor: 'pointer',
                            }}
                          >
                            <Eye size={13} />
                          </button>
                          {t.status === 'Open' && (
                            <button
                              onClick={() => handleEscalate(t.number)}
                              title="Escalate to Tier 2"
                              style={{
                                backgroundColor: '#7f1d1d',
                                border: 'none',
                                color: '#fca5a5',
                                padding: '0.2rem 0.45rem',
                                borderRadius: '4px',
                                fontSize: '0.7rem',
                                cursor: 'pointer',
                              }}
                            >
                              Escalate
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* SOFTWARE PROVISIONING REQUESTS */}
        <div style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}>
          <div>
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>Software Requests</h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Service Catalog & Mock Intune API</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', maxHeight: '550px' }}>
            {requests.map((r) => {
              const isPending = r.status === 'Pending approval';
              const isCompleted = r.status === 'Completed';
              return (
                <div
                  key={r.number}
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    padding: '0.85rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 700, color: '#38bdf8', fontSize: '0.85rem' }}>{r.number}</span>
                    <span style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      backgroundColor: isCompleted ? '#064e3b' : isPending ? '#78350f' : '#1e3a8a',
                      color: isCompleted ? '#34d399' : isPending ? '#fbbf24' : '#93c5fd',
                    }}>
                      {r.status}
                    </span>
                  </div>

                  <div>
                    <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.85rem' }}>{r.software}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                      Requester: {r.requester_name} ({r.department})
                    </div>
                  </div>

                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {r.reason}
                  </div>

                  {/* Manager Approval Controls */}
                  {isPending && (
                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
                      <button
                        onClick={() => handleDecideRequest(r.number, 'approve')}
                        style={{
                          flex: 1,
                          backgroundColor: '#059669',
                          color: '#fff',
                          border: 'none',
                          padding: '0.35rem',
                          borderRadius: '6px',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.25rem',
                        }}
                      >
                        <Check size={13} /> Approve
                      </button>
                      <button
                        onClick={() => handleDecideRequest(r.number, 'reject')}
                        style={{
                          flex: 1,
                          backgroundColor: '#b91c1c',
                          color: '#fff',
                          border: 'none',
                          padding: '0.35rem',
                          borderRadius: '6px',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.25rem',
                        }}
                      >
                        <X size={13} /> Reject
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* TICKET DETAIL DRAWER / MODAL */}
      {selectedTicket && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 50,
          padding: '1rem',
        }}>
          <div style={{
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            width: '100%',
            maxWidth: '650px',
            maxHeight: '85vh',
            overflowY: 'auto',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff' }}>
                  {selectedTicket.number}: {selectedTicket.classification?.summary || selectedTicket.description}
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Caller: {selectedTicket.caller_name} ({selectedTicket.department})
                </span>
              </div>
              <button
                onClick={() => setSelectedTicket(null)}
                style={{ backgroundColor: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            {/* ServiceNow Table Record */}
            <div style={{ backgroundColor: 'var(--bg-card)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', marginBottom: '0.4rem' }}>
                SERVICENOW RECORD SPECIFICATION:
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.4rem', fontSize: '0.78rem' }}>
                <div><strong>Table:</strong> incident</div>
                <div><strong>Number:</strong> {selectedTicket.servicenow?.number}</div>
                <div><strong>sys_id:</strong> <code style={{ color: '#34d399' }}>{selectedTicket.servicenow?.sys_id}</code></div>
                <div><strong>State:</strong> {selectedTicket.servicenow?.state}</div>
                <div><strong>Priority:</strong> {selectedTicket.classification?.priority}</div>
                <div><strong>Assignment Group:</strong> {selectedTicket.classification?.assignment_group}</div>
              </div>
            </div>

            {/* Timeline */}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                AUDIT TIMELINE:
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {selectedTicket.timeline?.map((tl, i) => (
                  <div key={i} style={{ fontSize: '0.75rem', backgroundColor: 'var(--bg-card)', padding: '0.4rem 0.6rem', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#38bdf8', fontWeight: 600 }}>
                      <span>{tl.action}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>{tl.at}</span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)' }}>{tl.detail} ({tl.actor})</div>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => setSelectedTicket(null)}
              style={{
                backgroundColor: 'var(--accent-blue)',
                color: '#fff',
                border: 'none',
                padding: '0.6rem',
                borderRadius: '8px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

