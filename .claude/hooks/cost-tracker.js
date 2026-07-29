#!/usr/bin/env node
/**
 * Cost Tracker Stop hook — minimal reimplementation, not a vendored copy.
 *
 * The original (affaan-m/ECC, scripts/hooks/cost-tracker.js) pulls in a
 * ~950-line cross-platform dependency chain (utils.js -> agent-data-home.js
 * -> path-safety.js) built for ECC's own multi-harness distribution
 * (Cursor + Claude Code, project-config-file overrides, trusted-root
 * checks). None of that applies to a single-project use case here, so this
 * inlines just the two things worth keeping: the per-message.id token
 * dedup (the original's own comments cite a real bug -- summing every
 * transcript line inflated cost 2.5-3x) and the per-model rate table.
 * Everything else (Cursor support, project-config overrides) is dropped.
 * No child_process calls anywhere in this file.
 *
 * Stop hook stdin payload: { session_id, transcript_path, cwd, ... }
 * Writes one JSON line per session-stop to ~/.claude/metrics/costs.jsonl
 * (a cumulative snapshot -- take the last row per session_id for totals).
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const RATE_TABLE = {
  haiku:  { in: 0.80,  out: 4.0,  cacheWrite: 1.00,  cacheRead: 0.08 },
  sonnet: { in: 3.00,  out: 15.0, cacheWrite: 3.75,  cacheRead: 0.30 },
  opus:   { in: 15.00, out: 75.0, cacheWrite: 18.75, cacheRead: 1.50 }
};

function getRates(model) {
  const m = String(model || '').toLowerCase();
  if (m.includes('haiku')) return RATE_TABLE.haiku;
  if (m.includes('opus')) return RATE_TABLE.opus;
  return RATE_TABLE.sonnet;
}

function toNumber(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function sanitizeSessionId(raw) {
  if (!raw || typeof raw !== 'string') return null;
  if (/[/\\]|\.\./.test(raw)) return null;
  const safe = raw.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 128);
  return safe || null;
}

/**
 * Sum token usage across a session transcript, deduped by message.id --
 * Claude Code writes one JSONL line per content block, so a single API
 * response spans multiple lines that each repeat the same message.usage.
 */
function sumUsageFromTranscript(transcriptPath) {
  let content;
  try {
    content = fs.readFileSync(transcriptPath, 'utf8');
  } catch {
    return null;
  }

  const usageById = new Map();
  let syntheticKey = 0;
  let model = 'unknown';

  for (const line of content.split('\n')) {
    if (!line.trim()) continue;
    let entry;
    try { entry = JSON.parse(line); } catch { continue; }
    if (entry.type !== 'assistant') continue;
    const msg = entry.message;
    if (!msg || !msg.usage) continue;
    const key = (typeof msg.id === 'string' && msg.id) ? msg.id : `__line_${++syntheticKey}`;
    usageById.set(key, msg.usage);
    if (msg.model && msg.model !== 'unknown') model = msg.model;
  }

  let inputTokens = 0, outputTokens = 0, cacheWriteTokens = 0, cacheReadTokens = 0;
  for (const u of usageById.values()) {
    inputTokens += toNumber(u.input_tokens);
    outputTokens += toNumber(u.output_tokens);
    cacheWriteTokens += toNumber(u.cache_creation_input_tokens);
    cacheReadTokens += toNumber(u.cache_read_input_tokens);
  }
  return { inputTokens, outputTokens, cacheWriteTokens, cacheReadTokens, model };
}

const MAX_STDIN = 1024 * 1024;
let raw = '';
let truncated = false;

process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  if (raw.length < MAX_STDIN) {
    const remaining = MAX_STDIN - raw.length;
    raw += chunk.substring(0, remaining);
    if (chunk.length > remaining) truncated = true;
  } else {
    truncated = true;
  }
});

process.stdin.on('end', () => {
  try {
    const input = raw.trim() ? JSON.parse(raw) : {};
    const transcriptPath = typeof input.transcript_path === 'string' ? input.transcript_path : null;
    const sessionId = sanitizeSessionId(input.session_id) || 'default';

    let usageTotals = null;
    if (transcriptPath && fs.existsSync(transcriptPath)) {
      usageTotals = sumUsageFromTranscript(transcriptPath);
    }

    const {
      inputTokens = 0, outputTokens = 0,
      cacheWriteTokens = 0, cacheReadTokens = 0,
      model = 'unknown'
    } = usageTotals || {};

    const rates = getRates(model);
    const estimatedCostUsd = Math.round((
      (inputTokens / 1e6) * rates.in +
      (outputTokens / 1e6) * rates.out +
      (cacheWriteTokens / 1e6) * rates.cacheWrite +
      (cacheReadTokens / 1e6) * rates.cacheRead
    ) * 1e6) / 1e6;

    const metricsDir = path.join(os.homedir(), '.claude', 'metrics');
    if (!fs.existsSync(metricsDir)) fs.mkdirSync(metricsDir, { recursive: true });

    const row = {
      timestamp: new Date().toISOString(),
      session_id: sessionId,
      transcript_path: transcriptPath || '',
      model,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      cache_write_tokens: cacheWriteTokens,
      cache_read_tokens: cacheReadTokens,
      estimated_cost_usd: estimatedCostUsd
    };
    fs.appendFileSync(path.join(metricsDir, 'costs.jsonl'), `${JSON.stringify(row)}\n`, 'utf8');
  } catch {
    // Never fail the Stop hook on a tracking error.
  }

  if (truncated) {
    process.stderr.write('[Hook] cost-tracker: stdin exceeded 1MB; suppressing pass-through\n');
    return;
  }
  process.stdout.write(raw);
});
