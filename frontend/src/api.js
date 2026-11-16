const API_BASE = 'http://localhost:8000/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function sendChat(message, user = null) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      user: user || {
        id: 'emma.walsh',
        name: 'Emma Walsh',
        email: 'emma.walsh@northline.com',
        title: 'Product Engineer',
        department: 'Engineering',
        location: 'Austin HQ',
        employee_type: 'Employee',
      },
    }),
  });
  return res.json();
}

export async function fetchTickets(status = null) {
  const url = status && status !== 'All' ? `${API_BASE}/tickets?status=${encodeURIComponent(status)}` : `${API_BASE}/tickets`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchTicket(number) {
  const res = await fetch(`${API_BASE}/tickets/${number}`);
  return res.json();
}

export async function executeTicketAction(number, actionId) {
  const res = await fetch(`${API_BASE}/tickets/${number}/actions/${actionId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  return res.json();
}

export async function escalateTicket(number, reason = 'Employee requested tier-2 support') {
  const res = await fetch(`${API_BASE}/tickets/${number}/escalate?reason=${encodeURIComponent(reason)}`, {
    method: 'POST',
  });
  return res.json();
}

export async function fetchRequests() {
  const res = await fetch(`${API_BASE}/requests`);
  return res.json();
}

export async function createSoftwareRequest(itemId, justification, user = null) {
  const res = await fetch(`${API_BASE}/requests`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      item_id: itemId,
      justification,
      user: user || {
        id: 'emma.walsh',
        name: 'Emma Walsh',
        email: 'emma.walsh@northline.com',
        title: 'Product Engineer',
        department: 'Engineering',
        location: 'Austin HQ',
        employee_type: 'Employee',
      },
    }),
  });
  return res.json();
}

export async function decideSoftwareRequest(number, decision, note = '') {
  const res = await fetch(`${API_BASE}/requests/${number}/decide`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, note, actor: 'Jordan Hale (IT Manager)' }),
  });
  return res.json();
}

export async function fetchCatalog() {
  const res = await fetch(`${API_BASE}/catalog`);
  return res.json();
}

export async function fetchKnowledge() {
  const res = await fetch(`${API_BASE}/knowledge`);
  return res.json();
}

export async function searchKnowledge(query, topK = 3) {
  const res = await fetch(`${API_BASE}/knowledge/search?query=${encodeURIComponent(query)}&top_k=${topK}`, {
    method: 'POST',
  });
  return res.json();
}

export async function fetchDashboardStats() {
  const res = await fetch(`${API_BASE}/dashboard/stats`);
  return res.json();
}

export async function fetchAuditLogs() {
  const res = await fetch(`${API_BASE}/audit`);
  return res.json();
}

export async function resetStoreSeed() {
  const res = await fetch(`${API_BASE}/seed`, { method: 'POST' });
  return res.json();
}

