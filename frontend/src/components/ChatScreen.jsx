import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Layers,
  ArrowRight,
  ShieldAlert,
  Terminal,
  Zap,
  ChevronDown,
  ChevronUp,
  Clock,
  Check,
  RotateCcw,
} from 'lucide-react';
import { sendChat, executeTicketAction, escalateTicket } from '../api';

const SCENARIOS = [
  {
    id: 1,
    label: 'Scenario 1: VPN Failure (Intelligent Ticket)',
    desc: 'Employee reports VPN failure -> AI extracts 7 ITSM fields -> ServiceNow Incident created.',
    prompt: 'I cannot connect to VPN since this morning. Authentication keeps failing.',
    color: '#3b82f6',
  },
  {
    id: 2,
    label: 'Scenario 2: Password Expired (Self-Healing)',
    desc: 'Identify -> Diagnose -> Knowledge Search -> Determine -> Execute -> Validate -> Update ServiceNow.',
    prompt: 'My password has expired.',
    color: '#10b981',
  },
  {
    id: 3,
    label: 'Scenario 3: Outlook Sync (RAG)',
    desc: 'Vector Search -> sentence-transformers -> Grounded LLM response + Sources cited.',
    prompt: 'How do I troubleshoot Outlook synchronization?',
    color: '#8b5cf6',
  },
  {
    id: 4,
    label: 'Scenario 4: Software Provisioning (VS Code)',
    desc: 'Intent Detection -> Catalog Match -> Policy Check -> ServiceNow REQ -> Mock Intune API.',
    prompt: 'I need Visual Studio Code installed on my laptop.',
    color: '#06b6d4',
  },
  {
    id: 5,
    label: 'Scenario 5: Unknown Question (AI Safety)',
    desc: 'Out of scope -> Zero Hallucination Guardrail -> Refusal + Human Escalation Offer.',
    prompt: 'How do I bake sourdough bread on company time?',
    color: '#f59e0b',
  },
];

export default function ChatScreen({ onTicketCreated }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'bot',
      text: "👋 Welcome to the **Northline AI IT Service Portal**!\n\nI can automatically resolve common IT issues (self-healing), fulfill software requests, search our verified knowledge base (RAG), or open an incident in ServiceNow with intelligent field categorization.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState({});
  const [expandedCitations, setExpandedCitations] = useState({});
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend = null) => {
    const text = textToSend || input.trim();
    if (!text || loading) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const data = await sendChat(text);
      const botMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: data.reply,
        data: data,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsg]);
      if (data.ticket && onTicketCreated) {
        onTicketCreated(data.ticket);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: '⚠️ An error occurred while communicating with the backend API. Please ensure the backend is running.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteAction = async (ticketNumber, actionId) => {
    try {
      const updated = await executeTicketAction(ticketNumber, actionId);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender: 'bot',
          text: `✅ **Action Approved & Executed**\n\nPlaybook executed successfully. ServiceNow Incident **${ticketNumber}** has been updated to **Resolved**.`,
          data: { ticket: updated },
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      if (onTicketCreated) onTicketCreated(updated);
    } catch (err) {
      alert('Failed to execute action: ' + err.message);
    }
  };

  const handleEscalate = async (ticketNumber) => {
    try {
      const updated = await escalateTicket(ticketNumber, 'Employee requested human support');
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender: 'bot',
          text: `🚨 **Incident Escalated to Tier-2 Support**\n\nServiceNow Incident **${ticketNumber}** priority increased to Urgency High. A human support engineer will contact you shortly.`,
          data: { ticket: updated },
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      if (onTicketCreated) onTicketCreated(updated);
    } catch (err) {
      alert('Failed to escalate: ' + err.message);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 75px)', maxWidth: '1400px', margin: '0 auto', padding: '1rem', gap: '1rem' }}>
      {/* Scenario Pills Header */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '0.875rem 1.25rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', fontWeight: 700, color: '#38bdf8' }}>
            <Sparkles size={16} />
            <span>MANDATORY LIVE DEMONSTRATION SCENARIOS (CLICK TO TEST):</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Auto-populates and tests live backend pipeline</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '0.6rem' }}>
          {SCENARIOS.map((sc) => (
            <button
              key={sc.id}
              onClick={() => handleSend(sc.prompt)}
              disabled={loading}
              style={{
                backgroundColor: 'var(--bg-card)',
                border: `1px solid ${sc.color}40`,
                borderRadius: '8px',
                padding: '0.55rem 0.75rem',
                textAlign: 'left',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1,
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-card)'; }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 700, fontSize: '0.8rem', color: sc.color }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: sc.color }} />
                {sc.label}
              </div>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '0.2rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                "{sc.prompt}"
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Log */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
      }}>
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          const data = msg.data;
          const cls = data?.classification;
          const ticket = data?.ticket;
          const sw = data?.software_request;
          const actions = data?.proposed_actions || [];
          const citations = data?.citations || [];

          return (
            <div
              key={msg.id}
              className="animate-fade-in"
              style={{
                display: 'flex',
                gap: '0.875rem',
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                maxWidth: isUser ? '75%' : '88%',
              }}
            >
              {/* Avatar */}
              {!isUser && (
                <div style={{
                  width: 36,
                  height: 36,
                  borderRadius: '10px',
                  backgroundColor: '#1e3a5f',
                  border: '1px solid #38bdf840',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#38bdf8',
                  flexShrink: 0,
                }}>
                  <Bot size={20} />
                </div>
              )}

              {/* Message Body */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', width: '100%' }}>
                <div style={{
                  backgroundColor: isUser ? 'var(--accent-blue)' : 'var(--bg-card)',
                  color: isUser ? '#fff' : 'var(--text-primary)',
                  border: isUser ? 'none' : '1px solid var(--border-color)',
                  borderRadius: '12px',
                  padding: '1rem 1.15rem',
                  fontSize: '0.9rem',
                  lineHeight: '1.55',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                }}>
                  {/* Markdown formatted text output */}
                  <div style={{ whiteSpace: 'pre-wrap' }}>
                    {msg.text}
                  </div>

                  {/* STRUCTURED CARD: Intelligent Ticket Intake (Scenario 1) */}
                  {cls && !data?.auto_resolved && ticket && (
                    <div style={{
                      marginTop: '0.875rem',
                      padding: '0.875rem',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(30, 41, 59, 0.7)',
                      border: '1px solid #3b82f640',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          📋 AI Intelligent Intake Classification
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#34d399', fontWeight: 600 }}>
                          Confidence: {Math.round((cls.confidence || 0.9) * 100)}%
                        </span>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', fontSize: '0.8rem' }}>
                        <div><strong style={{ color: 'var(--text-secondary)' }}>Intent:</strong> <span style={{ color: '#fff' }}>{cls.intent}</span></div>
                        <div><strong style={{ color: 'var(--text-secondary)' }}>Category / Sub:</strong> <span style={{ color: '#38bdf8' }}>{cls.category} / {cls.subcategory}</span></div>
                        <div><strong style={{ color: 'var(--text-secondary)' }}>Priority:</strong> <span style={{ color: '#f87171', fontWeight: 700 }}>{cls.priority}</span></div>
                        <div><strong style={{ color: 'var(--text-secondary)' }}>Impact / Urgency:</strong> <span style={{ color: '#fbbf24' }}>{cls.impact} / {cls.urgency}</span></div>
                        <div><strong style={{ color: 'var(--text-secondary)' }}>Assignment Group:</strong> <span style={{ color: '#c084fc' }}>{cls.assignment_group}</span></div>
                        <div><strong style={{ color: 'var(--text-secondary)' }}>CI:</strong> <span style={{ color: '#fff' }}>{cls.configuration_item}</span></div>
                      </div>

                      <div style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        <strong>Summary:</strong> {cls.summary}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#34d399', marginTop: '0.2rem' }}>
                        <strong>Suggested Resolution:</strong> {cls.suggested_resolution}
                      </div>

                      {/* ServiceNow Banner */}
                      {ticket?.servicenow && (
                        <div style={{
                          marginTop: '0.75rem',
                          padding: '0.5rem 0.75rem',
                          backgroundColor: '#172554',
                          border: '1px solid #1d4ed8',
                          borderRadius: '6px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          fontSize: '0.8rem',
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ fontWeight: 700, color: '#93c5fd' }}>ServiceNow Table API:</span>
                            <span style={{ color: '#fff', fontWeight: 600 }}>{ticket.servicenow.number}</span>
                            <span style={{ fontSize: '0.7rem', backgroundColor: '#2563eb', color: '#fff', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                              State: {ticket.servicenow.state}
                            </span>
                          </div>
                          <span style={{ fontSize: '0.72rem', color: '#60a5fa', fontFamily: 'monospace' }}>
                            sys_id: {ticket.servicenow.sys_id.slice(0, 10)}...
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* STRUCTURED CARD: 7-Stage Self-Healing Execution (Scenario 2) */}
                  {data?.auto_resolved && actions.length > 0 && (
                    <div style={{
                      marginTop: '0.875rem',
                      padding: '0.875rem',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(6, 78, 59, 0.25)',
                      border: '1px solid #10b98160',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#34d399', fontWeight: 700, fontSize: '0.82rem' }}>
                          <CheckCircle2 size={16} />
                          <span>AUTONOMOUS 7-STAGE SELF-HEALING LIFECYCLE</span>
                        </div>
                        <span style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 700, backgroundColor: '#064e3b', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
                          Policy: Unattended Auto-Resolve
                        </span>
                      </div>

                      {/* 7 Stepper Progress */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.6rem' }}>
                        {actions[0].steps.map((st, i) => (
                          <div
                            key={i}
                            style={{
                              display: 'flex',
                              alignItems: 'flex-start',
                              gap: '0.5rem',
                              fontSize: '0.78rem',
                              backgroundColor: 'rgba(15, 23, 42, 0.6)',
                              padding: '0.4rem 0.6rem',
                              borderRadius: '6px',
                              borderLeft: '3px solid #10b981',
                            }}
                          >
                            <span style={{ fontWeight: 700, color: '#34d399', minWidth: '18px' }}>{i + 1}.</span>
                            <div style={{ flex: 1 }}>
                              <span style={{ fontWeight: 600, color: '#fff' }}>{st.name}:</span>{' '}
                              <span style={{ color: 'var(--text-secondary)' }}>{st.result}</span>
                            </div>
                            <Check size={14} style={{ color: '#10b981', marginTop: '2px', flexShrink: 0 }} />
                          </div>
                        ))}
                      </div>

                      {ticket?.servicenow && (
                        <div style={{
                          marginTop: '0.6rem',
                          fontSize: '0.78rem',
                          color: '#34d399',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          borderTop: '1px dashed #05966950',
                          paddingTop: '0.4rem',
                        }}>
                          <span>ServiceNow Incident: <strong>{ticket.servicenow.number}</strong> (State: Resolved)</span>
                          <span style={{ fontSize: '0.72rem', color: '#a7f3d0' }}>Audit Log ID: Recorded</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* PROPOSED ACTION (e.g., VPN Credential Clear requiring approval) */}
                  {!data?.auto_resolved && actions.length > 0 && actions[0].status === 'proposed' && (
                    <div style={{
                      marginTop: '0.75rem',
                      padding: '0.75rem',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(245, 158, 11, 0.1)',
                      border: '1px solid #f59e0b50',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#fbbf24', fontWeight: 700, fontSize: '0.8rem' }}>
                          <Zap size={15} />
                          <span>Remediation Playbook Available: {actions[0].title}</span>
                        </div>
                        <span style={{ fontSize: '0.7rem', color: '#fbbf24', backgroundColor: '#78350f', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                          Requires Approval
                        </span>
                      </div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '0.35rem 0 0.5rem 0' }}>
                        {actions[0].risk}
                      </p>
                      <button
                        onClick={() => handleExecuteAction(ticket.number, actions[0].id)}
                        style={{
                          backgroundColor: '#d97706',
                          color: '#fff',
                          border: 'none',
                          padding: '0.4rem 0.8rem',
                          borderRadius: '6px',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                        }}
                      >
                        <Zap size={13} />
                        Approve & Execute Self-Healing Playbook
                      </button>
                    </div>
                  )}

                  {/* STRUCTURED CARD: Software Provisioning (Scenario 4) */}
                  {sw && (
                    <div style={{
                      marginTop: '0.875rem',
                      padding: '0.875rem',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(6, 182, 212, 0.15)',
                      border: '1px solid #06b6d450',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                          📦 Software Request & Provisioning Workflow
                        </span>
                        <span style={{
                          fontSize: '0.72rem',
                          backgroundColor: sw.status === 'Completed' ? '#065f46' : '#1e3a8a',
                          color: sw.status === 'Completed' ? '#34d399' : '#93c5fd',
                          padding: '0.15rem 0.5rem',
                          borderRadius: '4px',
                          fontWeight: 700,
                        }}>
                          {sw.status}
                        </span>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.4rem', fontSize: '0.8rem' }}>
                        <div><strong style={{ color: 'var(--text-secondary)' }}>Request ID:</strong> <span style={{ color: '#fff' }}>{sw.number}</span></div>
                        <div><strong style={{ color: 'var(--text-secondary)' }}>Software:</strong> <span style={{ color: '#38bdf8' }}>{sw.software}</span></div>
                        <div><strong style={{ color: 'var(--text-secondary)' }}>Requester:</strong> <span style={{ color: '#fff' }}>{sw.requester_name} ({sw.department})</span></div>
                        <div><strong style={{ color: 'var(--text-secondary)' }}>ServiceNow:</strong> <span style={{ color: '#34d399' }}>Request created successfully</span></div>
                      </div>

                      {/* Intune Mock Provisioning Progress */}
                      <div style={{ marginTop: '0.6rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
                          <span>Endpoint Dispatch (Microsoft Intune)</span>
                          <span style={{ color: '#38bdf8' }}>100% Deployed</span>
                        </div>
                        <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--bg-secondary)', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{ width: '100%', height: '100%', backgroundColor: '#06b6d4', borderRadius: '3px' }} />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* CITATIONS & RAG SOURCES */}
                  {citations.length > 0 && (
                    <div style={{ marginTop: '0.75rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.5rem' }}>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '0.35rem' }}>
                        📚 GROUNDED KNOWLEDGE BASE SOURCES:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                        {citations.map((c, i) => (
                          <div key={i} style={{ fontSize: '0.75rem', backgroundColor: 'var(--bg-secondary)', padding: '0.4rem 0.6rem', borderRadius: '6px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontWeight: 600, color: '#38bdf8' }}>[{c.id}] {c.title}</span>
                              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Cosine: {c.score}</span>
                            </div>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.72rem', marginTop: '0.2rem' }}>
                              {c.excerpt}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* HUMAN ESCALATION OFFER (Scenario 5 or low confidence) */}
                  {data?.offer_ticket && !ticket && (
                    <div style={{
                      marginTop: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.5rem 0.75rem',
                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid #ef444440',
                      borderRadius: '6px',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem', color: '#fca5a5' }}>
                        <ShieldAlert size={14} />
                        <span>Need further assistance from a human support specialist?</span>
                      </div>
                      <button
                        onClick={() => handleSend(`Open support ticket: ${msg.text.slice(0, 50)}`)}
                        style={{
                          backgroundColor: '#ef4444',
                          color: '#fff',
                          border: 'none',
                          padding: '0.3rem 0.65rem',
                          borderRadius: '4px',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        Create ServiceNow Ticket
                      </button>
                    </div>
                  )}
                </div>

                <span style={{
                  fontSize: '0.7rem',
                  color: 'var(--text-muted)',
                  alignSelf: isUser ? 'flex-end' : 'flex-start',
                  padding: '0 0.25rem',
                }}>
                  {msg.timestamp}
                </span>
              </div>

              {/* User Avatar */}
              {isUser && (
                <div style={{
                  width: 36,
                  height: 36,
                  borderRadius: '10px',
                  backgroundColor: 'var(--accent-blue)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff',
                  flexShrink: 0,
                }}>
                  <User size={20} />
                </div>
              )}
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            <div style={{
              width: 36,
              height: 36,
              borderRadius: '10px',
              backgroundColor: '#1e3a5f',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38bdf8',
            }}>
              <Bot size={20} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <div className="pulse-glow" style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#38bdf8' }} />
              <span>AI Agent reasoning over Knowledge Base & ServiceNow...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div style={{
        display: 'flex',
        gap: '0.75rem',
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '0.75rem',
      }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a technical question, report an incident, or request software (e.g. 'My password has expired')..."
          disabled={loading}
          style={{
            flex: 1,
            backgroundColor: 'transparent',
            border: 'none',
            outline: 'none',
            color: '#fff',
            fontSize: '0.9rem',
          }}
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          style={{
            backgroundColor: 'var(--accent-blue)',
            color: '#fff',
            border: 'none',
            padding: '0.6rem 1.25rem',
            borderRadius: '8px',
            fontWeight: 600,
            fontSize: '0.85rem',
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !input.trim() ? 0.5 : 1,
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'background 0.15s ease',
          }}
        >
          <Send size={15} />
          Submit
        </button>
      </div>
    </div>
  );
}

