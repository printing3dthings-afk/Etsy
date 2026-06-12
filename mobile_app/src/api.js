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

export const api = {
  health:   ()            => _get('/health'),
  metrics:  ()            => _get('/api/metrics'),
  listings: (state = 'active') => _get(`/api/listings?state=${state}`),
};
