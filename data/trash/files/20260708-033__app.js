/* OnBrandCraftz Agent Hub — frontend */

const AGENT_COLORS = {
  ceo: "#f0883e", sales: "#3fb950", product: "#58a6ff",
  marketing: "#ff7b72", analytics: "#bc8cff", cs: "#39d353", social: "#e75480",
};

let currentAgent = "ceo";
let chatHistories = {};  // {agentName: [{role, content, time}]}
let isThinking = false;
let sessionCounter = 0;

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
  setupAgentButtons();
  setupInput();
  setupBriefing();
  setInterval(loadDashboard, 60000);
  selectAgent("ceo");
});

// ── Dashboard stats ───────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const r = await fetch("/api/dashboard");
    const d = await r.json();
    if (d.error) return;

    const f = (id, val, cls) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.textContent = val;
      if (cls) el.className = "stat-badge " + cls;
    };

    f("stat-listings",  d.total_listings);
    f("stat-orders",    d.pending_orders,   d.pending_orders > 0 ? "badge-warn" : "badge-ok");
    f("stat-messages",  d.unread_messages,  d.unread_messages > 0 ? "badge-warn" : "badge-ok");
    f("stat-reviews",   d.unread_reviews,   d.unread_reviews > 0 ? "badge-warn" : "badge-ok");
    f("stat-revenue",   "$" + (d.revenue_week || 0).toFixed(2));
  } catch (_) {}
}

// ── Agent switching ───────────────────────────────────────────────────────────
function setupAgentButtons() {
  document.querySelectorAll(".agent-btn").forEach(btn => {
    btn.addEventListener("click", () => selectAgent(btn.dataset.agent));
  });
}

function selectAgent(name) {
  currentAgent = name;
  document.querySelectorAll(".agent-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.agent === name);
  });

  const info = window.AGENTS[name];
  if (!info) return;

  document.getElementById("header-icon").textContent = info.icon;
  document.getElementById("header-name").textContent = info.label + " Agent";
  document.getElementById("header-desc").textContent = info.desc;

  const color = AGENT_COLORS[name] || "#58a6ff";
  document.getElementById("header-icon").style.background =
    color.replace("#", "rgba(") + ", 0.15)".replace("rgba(", "rgba(") || "";
  document.getElementById("header-icon").style.background =
    hexToRgba(color, 0.15);

  renderMessages();
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1,3),16),
        g = parseInt(hex.slice(3,5),16),
        b = parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ── Message rendering ─────────────────────────────────────────────────────────
function renderMessages() {
  const box = document.getElementById("messages");
  const welcome = document.getElementById("welcome");
  const history = chatHistories[currentAgent] || [];

  if (history.length === 0) {
    box.innerHTML = "";
    welcome.style.display = "flex";
    return;
  }
  welcome.style.display = "none";
  box.innerHTML = "";

  history.forEach(m => {
    const el = buildMessageEl(m);
    box.appendChild(el);
  });

  const thinking = document.getElementById("thinking");
  box.appendChild(thinking);
  if (isThinking) thinking.classList.add("visible");

  box.scrollTop = box.scrollHeight;
}

function buildMessageEl(m) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${m.role}`;

  if (m.role === "agent" && m.statuses && m.statuses.length > 0) {
    m.statuses.forEach(s => {
      const st = document.createElement("div");
      st.className = "msg-status";
      st.textContent = s.replace(/\[CEO\]\s*->\s*/, "").trim();
      wrap.appendChild(st);
    });
  }

  const sender = document.createElement("div");
  sender.className = "msg-sender";
  sender.textContent = m.role === "user" ? "You" : window.AGENTS[currentAgent]?.label + " Agent";
  wrap.appendChild(sender);

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  if (m.role === "agent") {
    bubble.innerHTML = marked.parse(m.content || "");
  } else {
    bubble.textContent = m.content;
  }
  wrap.appendChild(bubble);

  const time = document.createElement("div");
  time.className = "msg-time";
  time.textContent = m.time || "";
  wrap.appendChild(time);

  return wrap;
}

function addMessage(role, content, statuses = []) {
  if (!chatHistories[currentAgent]) chatHistories[currentAgent] = [];
  const now = new Date();
  const time = now.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"});
  chatHistories[currentAgent].push({role, content, statuses, time});
  renderMessages();
}

// ── Input setup ───────────────────────────────────────────────────────────────
function setupInput() {
  const input  = document.getElementById("msg-input");
  const sendBtn = document.getElementById("send-btn");

  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 140) + "px";
    sendBtn.disabled = !input.value.trim() || isThinking;
  });

  sendBtn.addEventListener("click", sendMessage);
  document.getElementById("clear-btn").addEventListener("click", clearChat);

  // Quick prompts
  document.querySelectorAll(".quick-prompt").forEach(btn => {
    btn.addEventListener("click", () => {
      input.value = btn.dataset.prompt;
      input.dispatchEvent(new Event("input"));
      sendMessage();
    });
  });
}

async function sendMessage() {
  const input = document.getElementById("msg-input");
  const msg = input.value.trim();
  if (!msg || isThinking) return;

  // Clear and hide welcome
  input.value = "";
  input.style.height = "auto";
  document.getElementById("send-btn").disabled = true;
  document.getElementById("welcome").style.display = "none";

  addMessage("user", msg);
  setThinking(true);

  const sessionId = `s${++sessionCounter}_${Date.now()}`;

  try {
    // Start the agent
    const startRes = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({agent: currentAgent, message: msg, session_id: sessionId}),
    });
    if (!startRes.ok) throw new Error("Failed to start agent");

    // Stream the result
    await streamResult(sessionId);
  } catch (err) {
    setThinking(false);
    addMessage("agent", `Error: ${err.message}`);
  }
}

async function streamResult(sessionId) {
  return new Promise((resolve, reject) => {
    const statuses = [];
    const es = new EventSource(`/api/stream/${sessionId}`);

    es.onmessage = e => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "status") {
          statuses.push(data.text);
          updateThinkingText(data.text);
        } else if (data.type === "done") {
          es.close();
          setThinking(false);
          addMessage("agent", data.text, statuses);
          resolve();
        } else if (data.type === "error") {
          es.close();
          setThinking(false);
          addMessage("agent", `Error: ${data.text}`);
          reject(new Error(data.text));
        }
      } catch (_) {}
    };

    es.onerror = () => {
      es.close();
      setThinking(false);
      reject(new Error("Connection lost"));
    };
  });
}

function setThinking(on) {
  isThinking = on;
  const thinking = document.getElementById("thinking");
  const sendBtn = document.getElementById("send-btn");
  thinking.classList.toggle("visible", on);
  sendBtn.disabled = on;
  if (on) {
    thinking.querySelector(".thinking-text").textContent = "Thinking…";
    document.getElementById("messages").scrollTop = 999999;
  }
}

function updateThinkingText(status) {
  const t = document.getElementById("thinking");
  const cleaned = status.replace(/\[CEO\]\s*->\s*/,"").trim();
  t.querySelector(".thinking-text").textContent = cleaned || "Thinking…";
  document.getElementById("messages").scrollTop = 999999;
}

function clearChat() {
  chatHistories[currentAgent] = [];
  renderMessages();
}

// ── Daily briefing ────────────────────────────────────────────────────────────
function setupBriefing() {
  document.getElementById("briefing-btn").addEventListener("click", async () => {
    if (isThinking) return;
    selectAgent("ceo");
    document.getElementById("welcome").style.display = "none";

    const sessionId = `briefing_${Date.now()}`;
    addMessage("user", "Run daily briefing");
    setThinking(true);

    try {
      await fetch("/api/briefing", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({session_id: sessionId}),
      });
      await streamResult(sessionId);
    } catch (err) {
      setThinking(false);
      addMessage("agent", `Briefing error: ${err.message}`);
    }
  });
}
