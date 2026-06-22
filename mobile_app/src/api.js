import { API_URL, APP_TOKEN } from './config';

const headers = () => ({
  Authorization: `Bearer ${APP_TOKEN}`,
  'Content-Type': 'application/json',
});

async function _get(path) {
  const res = await fetch(`${API_URL}${path}`, { headers: headers() });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function _post(path, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function _del(path) {
  const res = await fetch(`${API_URL}${path}`, { method: 'DELETE', headers: headers() });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  health:   ()            => _get('/health'),
  metrics:  ()            => _get('/api/metrics'),
  listings: (state = 'active') => _get(`/api/listings?state=${state}`),

  // Frank
  credentialsStatus: () => _get('/api/credentials/status'),
  agentsStatus:      () => _get('/api/agents/status'),

  // Knowledge
  todos:       () => _get('/api/todos'),
  addTodo:     (text, added_by = 'scott', due_date = null) => _post('/api/todos', { text, added_by, due_date }),
  toggleTodo:  (id, done) => _post(`/api/todos/${id}/toggle`, { done }),
  deleteTodo:  (id) => _del(`/api/todos/${id}`),

  queue:         (status = 'pending') => _get(`/api/queue?status=${status}`),
  approveAction: (id) => _post(`/api/queue/${id}/approve`),
  rejectAction:  (id) => _post(`/api/queue/${id}/reject`),

  cadence: () => _get('/api/cadence'),
  memory:  () => _get('/api/memory'),

  conversations:      (q = '') => _get(`/api/conversations${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  conversationDetail: (sessionId) => _get(`/api/conversations/${sessionId}`),

  kb:    (q = '') => _get(`/api/kb${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  kbDoc: (filename) => _get(`/api/kb/${filename}`),

  // Tools
  toolsList:   () => _get('/api/tools/list'),
  workflows:   () => _get('/api/workflows'),
  runWorkflow: (id, extra_args = '') => _post(`/api/workflows/${id}/run`, { extra_args }),

  // Shop
  files: () => _get('/api/files'),

  // Voice
  speakUrl:       `${API_URL}/api/voice/speak`,
  transcribeUrl:  `${API_URL}/api/voice/transcribe`,

  // Chat WS handshake — short-lived single-use ticket, since React Native's
  // WebSocket implementation can't set a custom header on the handshake.
  wsTicket: () => _post('/api/ws-ticket'),
};
