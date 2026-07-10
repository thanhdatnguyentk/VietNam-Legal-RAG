// ============================================================================
// VietLegal RAG - Frontend Logic (Material Design 3 UI)
// ============================================================================

import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";

const API_BASE = "http://localhost:8000";

// DOM Elements
const elements = {
  statusDot: document.getElementById('status-dot'),
  statusText: document.getElementById('status-text'),
  themeToggle: document.getElementById('theme-toggle'),
  welcome: document.getElementById('welcome'),
  chatArea: document.getElementById('chat-area'),
  mainContent: document.getElementById('main-content'),
  queryInput: document.getElementById('query-input'),
  sendButton: document.getElementById('send-button'),
  modeAsk: document.getElementById('mode-ask'),
  modeSearch: document.getElementById('mode-search'),
  statVectors: document.getElementById('stat-vectors'),
  suggestionBtns: document.querySelectorAll('.suggestion-btn'),
};

let isConnected = false;

// Initialize
async function init() {
  checkHealth();
  setInterval(checkHealth, 30000); // Check every 30s
  
  // Theme Toggle
  const isDark = localStorage.getItem('theme') !== 'light';
  if (!isDark) document.documentElement.classList.replace('dark', 'light');
  elements.themeToggle.addEventListener('click', () => {
    const isCurrentlyDark = document.documentElement.classList.contains('dark');
    if (isCurrentlyDark) {
      document.documentElement.classList.replace('dark', 'light');
      localStorage.setItem('theme', 'light');
    } else {
      document.documentElement.classList.replace('light', 'dark');
      localStorage.setItem('theme', 'dark');
    }
  });

  // Input Handling
  elements.queryInput.addEventListener('input', () => {
    elements.sendButton.disabled = elements.queryInput.value.trim() === '';
    // Auto-resize textarea
    elements.queryInput.style.height = 'auto';
    elements.queryInput.style.height = Math.min(elements.queryInput.scrollHeight, 150) + 'px';
  });

  elements.queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  elements.sendButton.addEventListener('click', handleSend);

  // Suggestions
  elements.suggestionBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      elements.queryInput.value = btn.dataset.query;
      handleSend();
    });
  });

  // Mode Selection (Toggle logic for chips)
  elements.modeAsk.addEventListener('click', () => {
    elements.modeAsk.selected = true;
    elements.modeSearch.selected = false;
  });
  elements.modeSearch.addEventListener('click', () => {
    elements.modeSearch.selected = true;
    elements.modeAsk.selected = false;
  });
}

// Health Check
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    if (data.status === 'ok') {
      isConnected = true;
      elements.statusDot.classList.add('online');
      elements.statusText.textContent = 'Trực tuyến';
      if (data.vector_count) elements.statVectors.textContent = data.vector_count.toLocaleString();
    }
  } catch (err) {
    isConnected = false;
    elements.statusDot.classList.remove('online');
    elements.statusText.textContent = 'Ngoại tuyến';
  }
}

// Send Message Handler
async function handleSend() {
  const query = elements.queryInput.value.trim();
  if (!query || !isConnected) return;

  // UI Updates
  elements.welcome.classList.add('hidden');
  elements.chatArea.classList.remove('hidden');
  elements.queryInput.value = '';
  elements.queryInput.style.height = 'auto';
  elements.sendButton.disabled = true;

  // Add User Message
  appendUserMessage(query);
  
  // Add AI Loading State
  const loadingId = appendLoadingMessage();
  elements.mainContent.scrollTop = elements.mainContent.scrollHeight;

  const isAskMode = elements.modeAsk.selected;

  try {
    const endpoint = isAskMode ? '/ask' : '/search';
    const body = { query, top_k: 5 };

    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    const data = await res.json();
    removeMessage(loadingId);

    if (isAskMode) {
      renderAskResponse(data);
    } else {
      renderSearchResponse(data);
    }
  } catch (err) {
    removeMessage(loadingId);
    appendErrorMessage("Không thể kết nối đến máy chủ. Vui lòng thử lại sau.");
  }
  
  elements.mainContent.scrollTop = elements.mainContent.scrollHeight;
}

// UI Rendering Functions
function appendUserMessage(text) {
  const div = document.createElement('div');
  div.className = 'chat-message user';
  div.innerHTML = `
    <div class="chat-avatar"><md-icon>person</md-icon></div>
    <div class="chat-bubble">${escapeHtml(text)}</div>
  `;
  elements.chatArea.appendChild(div);
}

function appendLoadingMessage() {
  const id = 'msg-' + Date.now();
  const div = document.createElement('div');
  div.id = id;
  div.className = 'chat-message ai';
  div.innerHTML = `
    <div class="chat-avatar"><md-icon>auto_awesome</md-icon></div>
    <div class="chat-bubble" style="width: 100%; max-width: 600px;">
      <div class="skeleton-loader">
        <div class="skeleton-line"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line"></div>
      </div>
    </div>
  `;
  elements.chatArea.appendChild(div);
  return id;
}

function removeMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function appendErrorMessage(text) {
  const div = document.createElement('div');
  div.className = 'chat-message ai';
  div.innerHTML = `
    <div class="chat-avatar" style="background: var(--md-sys-color-error);"><md-icon>error</md-icon></div>
    <div class="chat-bubble" style="color: var(--md-sys-color-error);">
      ${escapeHtml(text)}
    </div>
  `;
  elements.chatArea.appendChild(div);
}

// Parse and render /ask response
function renderAskResponse(data) {
  let answer = data.answer || "Không có câu trả lời.";
  let thinkContent = "";

  // Extract <think> tags (IRAC process)
  const thinkRegex = /<think>([\s\S]*?)<\/think>/i;
  const match = answer.match(thinkRegex);
  if (match) {
    thinkContent = match[1].trim();
    answer = answer.replace(thinkRegex, '').trim();
  }

  // Parse markdown
  const htmlContent = marked.parse(answer);
  
  let html = `
    <div class="chat-message ai">
      <div class="chat-avatar"><md-icon>auto_awesome</md-icon></div>
      <div class="chat-bubble" style="width: 100%;">
  `;

  // Render Think Block if exists
  if (thinkContent) {
    html += `
      <div class="think-block">
        <div class="think-header" onclick="this.parentElement.classList.toggle('expanded')">
          <md-icon>keyboard_arrow_down</md-icon>
          Quá trình suy luận (IRAC)
        </div>
        <div class="think-content">${escapeHtml(thinkContent)}</div>
      </div>
    `;
  }

  html += `<div class="ai-content">${htmlContent}</div>`;

  // Render Sources
  if (data.sources && data.sources.length > 0) {
    html += `
      <div class="sources-container">
        <div class="sources-title"><md-icon>menu_book</md-icon> Nguồn tài liệu tham khảo</div>
    `;
    data.sources.forEach((hit, idx) => {
      let isGraph = hit.document_number && hit.text && hit.text.includes("[Graph Expansion");
      let icon = isGraph ? "hub" : "description";
      let title = hit.title || (isGraph ? "Trích xuất từ Knowledge Graph" : "Văn bản pháp luật");
      
      html += `
        <div class="source-card">
          <div class="source-header">
            <div>
              <div class="source-doc-id"><md-icon style="font-size: 16px; vertical-align: middle;">${icon}</md-icon> ${escapeHtml(hit.document_number || "N/A")}</div>
              ${hit.article ? `<div class="source-article">Điều ${escapeHtml(hit.article)}</div>` : ''}
            </div>
            <div class="citation-chip">[${idx + 1}]</div>
          </div>
          <div class="source-text">${escapeHtml(hit.text || "").substring(0, 150)}...</div>
        </div>
      `;
    });
    html += `</div>`; // .sources-container
  }

  html += `
      <div style="font-size: 0.75rem; color: var(--md-sys-color-outline); margin-top: 16px;">
        Thời gian phản hồi: ${data.latency_ms ? data.latency_ms.toFixed(0) : 0}ms
      </div>
    </div>
  </div>`;

  const wrapper = document.createElement('div');
  wrapper.innerHTML = html;
  elements.chatArea.appendChild(wrapper.firstElementChild);
}

// Parse and render /search response
function renderSearchResponse(data) {
  let html = `
    <div class="chat-message ai">
      <div class="chat-avatar"><md-icon>search</md-icon></div>
      <div class="chat-bubble" style="width: 100%;">
        <div class="ai-content"><p>Tìm thấy <strong>${data.total_hits}</strong> kết quả phù hợp (${data.latency_ms.toFixed(0)}ms):</p></div>
        <div class="sources-container">
  `;

  if (data.hits && data.hits.length > 0) {
    data.hits.forEach((hit, idx) => {
      let isGraph = hit.text && hit.text.includes("[Graph Expansion");
      let icon = isGraph ? "hub" : "description";
      
      html += `
        <div class="source-card">
          <div class="source-header">
            <div>
              <div class="source-doc-id"><md-icon style="font-size: 16px; vertical-align: middle;">${icon}</md-icon> ${escapeHtml(hit.document_number || "N/A")}</div>
              <div class="source-article">${escapeHtml(hit.title || "")}</div>
              ${hit.article ? `<div class="source-article">Điều ${escapeHtml(hit.article)}</div>` : ''}
            </div>
            <div class="citation-chip">[${idx + 1}]</div>
          </div>
          <div class="source-text" style="-webkit-line-clamp: unset;">${escapeHtml(hit.text || "")}</div>
        </div>
      `;
    });
  } else {
    html += `<p>Không tìm thấy tài liệu phù hợp.</p>`;
  }

  html += `
        </div>
      </div>
    </div>
  `;

  const wrapper = document.createElement('div');
  wrapper.innerHTML = html;
  elements.chatArea.appendChild(wrapper.firstElementChild);
}

function escapeHtml(unsafe) {
  if (!unsafe) return "";
  return unsafe
       .replace(/&/g, "&amp;")
       .replace(/</g, "&lt;")
       .replace(/>/g, "&gt;")
       .replace(/"/g, "&quot;")
       .replace(/'/g, "&#039;");
}

document.addEventListener('DOMContentLoaded', init);
