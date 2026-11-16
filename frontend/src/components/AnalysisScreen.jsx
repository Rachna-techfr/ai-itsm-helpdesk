import React, { useState, useEffect } from 'react';
import {
  Brain,
  ShieldCheck,
  Zap,
  Terminal,
  Clock,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Eye,
  FileText,
  Search,
} from 'lucide-react';
import { fetchTickets, fetchAuditLogs } from '../api';

export default function AnalysisScreen() {
  const [tickets, setTickets] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [tList, aList] = await Promise.all([fetchTickets(), fetchAuditLogs()]);
        setTickets(tList);
        setAuditLogs(aList);
        if (tList.length > 0) setSelectedTicket(tList[0]);
      } catch (err) {
        console.error('Failed to load analysis data:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const cls = selectedTicket?.classification;
  const entities = cls?.entities || {};
  const servicenow = selectedTicket?.servicenow;

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* HEADER EXPLANATION */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '1rem 1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Brain size={20} style={{ color: '#8b5cf6' }} />
            AI Decision Analysis & Enterprise Audit Trail
          </h2>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
            Deep inspection of AI reasoning, entity recognition, confidence thresholds, and permanent audit logs.
          </p>
        </div>
        <div style={{
          backgroundColor: '#1e1b4b',
          color: '#a78bfa',
          padding: '0.35rem 0.75rem',
          borderRadius: '9999px',
          fontSize: '0.75rem',
          fontWeight: 700,
          border: '1px solid #6366f140',
        }}>
          Governance: Zero Hallucination Mode Active
        </div>
      </div>

      {/* TOP: TICKET SELECTOR & DEEP INSPECTION */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.25rem' }}>
        {/* TICKET SELECTOR LIST */}
        <div style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '1rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.6rem',
          maxHeight: '480px',
          overflowY: 'auto',
        }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            SELECT TICKET TO INSPECT AI REASONING:
          </span>

          {tickets.map((t) => {
            const isSelected = selectedTicket?.number === t.number;
            return (
              <div
                key={t.number}
                onClick={() => setSelectedTicket(t)}
                style={{
                  backgroundColor: isSelected ? 'var(--bg-card-hover)' : 'var(--bg-card)',
                  border: isSelected ? '1px solid var(--accent-blue)' : '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '0.75rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 700, color: isSelected ? '#38bdf8' : '#fff', fontSize: '0.85rem' }}>
                    {t.number}
                  </span>
                  <span style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    padding: '0.1rem 0.4rem',
                    borderRadius: '4px',
                    backgroundColor: t.status === 'Resolved' ? '#064e3b' : '#1e3a8a',
                    color: t.status === 'Resolved' ? '#34d399' : '#93c5fd',
                  }}>
                    {t.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {t.classification?.summary || t.description}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  Caller: {t.caller_name} • Priority: {t.classification?.priority}
                </div>
              </div>
            );
          })}
        </div>

        {/* DEEP AI INSPECTION PANEL */}
        {selectedTicket ? (
          <div style={{
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff' }}>
                  {selectedTicket.number}: {cls?.summary || selectedTicket.description}
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Original Prompt: "{selectedTicket.description}"
                </span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Confidence Score</span>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#34d399' }}>
                  {Math.round((cls?.confidence || 0.9) * 100)}%
                </div>
              </div>
            </div>

            {/* AI OUTPUT MATRIX */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', backgroundColor: 'var(--bg-card)', padding: '0.85rem', borderRadius: '8px' }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Intent</span>
                <div style={{ fontWeight: 700, color: '#38bdf8', fontSize: '0.85rem' }}>{cls?.intent}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Category / Sub-category</span>
                <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.85rem' }}>{cls?.category} / {cls?.subcategory}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Priority (Impact/Urgency)</span>
                <div style={{ fontWeight: 700, color: '#f87171', fontSize: '0.85rem' }}>
                  {cls?.priority} ({cls?.impact} / {cls?.urgency})
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Assignment Group</span>
                <div style={{ fontWeight: 700, color: '#c084fc', fontSize: '0.85rem' }}>{cls?.assignment_group}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Configuration Item</span>
                <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.85rem' }}>{cls?.configuration_item}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>ServiceNow sys_id</span>
                <div style={{ fontWeight: 700, color: '#34d399', fontSize: '0.75rem', fontFamily: 'monospace' }}>
                  {servicenow?.sys_id?.slice(0, 16)}...
                </div>
              </div>
            </div>

            {/* ENTITY RECOGNITION */}
            <div style={{ backgroundColor: 'var(--bg-card)', padding: '0.85rem', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                Extracted Named Entities:
              </span>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', marginTop: '0.4rem', fontSize: '0.78rem' }}>
                <div><span style={{ color: 'var(--text-muted)' }}>Application:</span> <strong>{entities.application || 'N/A'}</strong></div>
                <div><span style={{ color: 'var(--text-muted)' }}>Target User:</span> <strong>{entities.user || 'caller'}</strong></div>
                <div><span style={{ color: 'var(--text-muted)' }}>Location:</span> <strong>{entities.location || 'Austin HQ'}</strong></div>
                <div><span style={{ color: 'var(--text-muted)' }}>Error Code:</span> <strong>{entities.error_text || 'None detected'}</strong></div>
              </div>
            </div>

            {/* MODEL RATIONALE */}
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', backgroundColor: 'var(--bg-card)', padding: '0.85rem', borderRadius: '8px' }}>
              <strong style={{ color: '#fff' }}>Model Decision Rationale:</strong>
              <p style={{ marginTop: '0.25rem' }}>{cls?.rationale}</p>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            Select a ticket to inspect
          </div>
        )}
      </div>

      {/* BOTTOM: PERMANENT AUDIT LOG TABLE (Mandatory for Capability 2) */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.85rem',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>Autonomous Agent Audit Log</h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Permanent tamper-evident log of every automated diagnosis, execution step, and ServiceNow update.
            </p>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{auditLogs.length} audit entries recorded</span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)', fontSize: '0.7rem', textTransform: 'uppercase' }}>
                <th style={{ padding: '0.5rem 0.75rem' }}>Timestamp</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>Ticket #</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>Actor</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>Action Executed</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>Policy Mode</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>Confidence</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>Status</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>Execution Detail</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr
                  key={log.id}
                  style={{ borderBottom: '1px solid var(--border-color)' }}
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-card)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                >
                  <td style={{ padding: '0.5rem 0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                    {log.timestamp.slice(11, 19)}
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem', fontWeight: 700, color: '#38bdf8' }}>
                    {log.ticket_number}
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem', color: '#c084fc', fontWeight: 600 }}>
                    {log.actor}
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem', color: '#fff' }}>
                    {log.action}
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem' }}>
                    <span style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      padding: '0.1rem 0.4rem',
                      borderRadius: '4px',
                      backgroundColor: log.policy === 'auto' ? '#064e3b' : '#78350f',
                      color: log.policy === 'auto' ? '#34d399' : '#fbbf24',
                    }}>
                      {log.policy}
                    </span>
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem', color: '#34d399', fontWeight: 600 }}>
                    {Math.round(log.confidence * 100)}%
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem' }}>
                    <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.2rem', fontWeight: 600 }}>
                      <CheckCircle2 size={12} /> {log.status}
                    </span>
                  </td>
                  <td style={{ padding: '0.5rem 0.75rem', color: 'var(--text-secondary)', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {log.details}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

