/**
 * Nyaya Pramaan (न्याय प्रमाण) - Client Application Controller
 * Handles routing, verification workflow, diff rendering, presets, upload, reports, and auth.
 */

// Application State
const state = {
  user: null,
  token: localStorage.getItem("nyaya_token") || null,
  activeView: "dashboard",
  selectedCase: null,
  presets: [],
  history: [],
  stats: null,
  currentVerification: null,
  diffViewMode: "inline" // 'inline' or 'side-by-side'
};

// DOM Content Loaded
document.addEventListener("DOMContentLoaded", async () => {
  initEventListeners();
  await loadUserSession();
  await loadPresets();
  await loadStats();
  await loadHistory();
  showView("dashboard");
});

// Event Listeners Initialization
function initEventListeners() {
  // Navigation Links
  document.querySelectorAll("[data-nav]").forEach(el => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      const targetView = el.getAttribute("data-nav");
      showView(targetView);
    });
  });

  // Demo Login Quick Button
  const demoBtn = document.getElementById("btn-quick-demo");
  if (demoBtn) demoBtn.addEventListener("click", handleDemoLogin);

  // Auth Modal Controls
  const authModalBtn = document.getElementById("btn-open-auth");
  if (authModalBtn) authModalBtn.addEventListener("click", openAuthModal);

  const modalCloseBtn = document.getElementById("modal-close-btn");
  if (modalCloseBtn) modalCloseBtn.addEventListener("click", closeAuthModal);

  // Tab switching in Auth Modal
  document.querySelectorAll(".auth-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".auth-tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".auth-tab-pane").forEach(p => p.style.display = "none");
      btn.classList.add("active");
      const target = btn.getAttribute("data-tab");
      const pane = document.getElementById(target);
      if (pane) pane.style.display = "block";
    });
  });

  // Auth Forms
  const loginForm = document.getElementById("form-login");
  if (loginForm) loginForm.addEventListener("submit", handleLoginSubmit);

  const registerForm = document.getElementById("form-register");
  if (registerForm) registerForm.addEventListener("submit", handleRegisterSubmit);

  const forgotForm = document.getElementById("form-forgot");
  if (forgotForm) forgotForm.addEventListener("submit", handleForgotSubmit);

  // Verification Form
  const verifyForm = document.getElementById("form-verify-quote");
  if (verifyForm) verifyForm.addEventListener("submit", handleVerifySubmit);

  // Quote input counter
  const quoteInput = document.getElementById("input-quote-text");
  if (quoteInput) {
    quoteInput.addEventListener("input", () => {
      const txt = quoteInput.value.trim();
      const wordCount = txt ? txt.split(/\s+/).length : 0;
      const charCount = txt.length;
      const countDisplay = document.getElementById("quote-counter");
      if (countDisplay) {
        countDisplay.textContent = `${wordCount} words (${charCount} characters)`;
      }
    });
  }

  // Case Search Autocomplete
  const caseSearchInput = document.getElementById("input-case-search");
  if (caseSearchInput) {
    let debounceTimer;
    caseSearchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        handleCaseSearch(e.target.value);
      }, 250);
    });

    caseSearchInput.addEventListener("focus", () => {
      if (caseSearchInput.value.length >= 2) {
        handleCaseSearch(caseSearchInput.value);
      }
    });
  }

  // Support Form
  const supportForm = document.getElementById("form-support-ticket");
  if (supportForm) supportForm.addEventListener("submit", handleSupportSubmit);

  // PDF Upload Dropzone
  const dropzone = document.getElementById("pdf-dropzone");
  const fileInput = document.getElementById("file-pdf-upload");
  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelected(e.dataTransfer.files[0]);
      }
    });
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length > 0) {
        handleFileSelected(fileInput.files[0]);
      }
    });
  }

  // Upload Form Submit
  const uploadForm = document.getElementById("form-upload-verify");
  if (uploadForm) uploadForm.addEventListener("submit", handleUploadVerifySubmit);

  // Diff toggle buttons
  const btnInlineDiff = document.getElementById("btn-diff-inline");
  const btnSideDiff = document.getElementById("btn-diff-side");
  if (btnInlineDiff) {
    btnInlineDiff.addEventListener("click", () => setDiffViewMode("inline"));
  }
  if (btnSideDiff) {
    btnSideDiff.addEventListener("click", () => setDiffViewMode("side-by-side"));
  }
}

// Routing & View Switcher
function showView(viewId) {
  state.activeView = viewId;
  document.querySelectorAll(".view-panel").forEach(panel => {
    panel.style.display = "none";
  });
  const activePanel = document.getElementById(`view-${viewId}`);
  if (activePanel) {
    activePanel.style.display = "block";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Update navbar links
  document.querySelectorAll("[data-nav]").forEach(link => {
    if (link.getAttribute("data-nav") === viewId) {
      link.classList.add("active");
    } else {
      link.classList.remove("active");
    }
  });

  if (viewId === "history") {
    loadHistory();
  } else if (viewId === "dashboard") {
    loadStats();
  }
}

// Session & Authentication
async function loadUserSession() {
  const token = state.token;
  if (!token) {
    // Auto-login to Demo mode for seamless trial
    await handleDemoLogin();
    return;
  }
  try {
    const res = await fetch("/api/auth/me", {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (res.ok) {
      const data = await res.json();
      state.user = data.user;
      renderUserHeader();
    } else {
      await handleDemoLogin();
    }
  } catch (err) {
    console.error("Auth session check failed:", err);
    await handleDemoLogin();
  }
}

function renderUserHeader() {
  const userContainer = document.getElementById("nav-user-container");
  if (!userContainer) return;
  if (state.user) {
    userContainer.innerHTML = `
      <div class="user-badge">
        <span class="avatar">${state.user.full_name.charAt(0)}</span>
        <span>${escapeHtml(state.user.full_name)}</span>
        <button class="btn btn-outline btn-sm" onclick="handleLogout()" style="margin-left:6px; color:#fff; border-color:rgba(255,255,255,0.25);">Logout</button>
      </div>
    `;
  } else {
    userContainer.innerHTML = `
      <button class="btn btn-primary btn-sm" id="btn-open-auth">Sign In / Demo</button>
    `;
    const btn = document.getElementById("btn-open-auth");
    if (btn) btn.addEventListener("click", openAuthModal);
  }
}

async function handleDemoLogin() {
  try {
    const res = await fetch("/api/auth/demo", { method: "POST" });
    const data = await res.json();
    state.user = data.user;
    state.token = data.token;
    localStorage.setItem("nyaya_token", data.token);
    renderUserHeader();
    closeAuthModal();
    showToast("Logged in as Senior Advocate (Supreme Court Demo)", "success");
    await loadHistory();
  } catch (err) {
    showToast("Failed to initialize Demo Mode", "error");
  }
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");
    state.user = data.user;
    state.token = data.token;
    localStorage.setItem("nyaya_token", data.token);
    renderUserHeader();
    closeAuthModal();
    showToast(`Welcome back, ${data.user.full_name}`, "success");
    await loadHistory();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleRegisterSubmit(e) {
  e.preventDefault();
  const email = document.getElementById("reg-email").value;
  const full_name = document.getElementById("reg-name").value;
  const password = document.getElementById("reg-password").value;
  const role = document.getElementById("reg-role").value;
  try {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, full_name, password, role })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Registration failed");
    state.user = data.user;
    state.token = data.token;
    localStorage.setItem("nyaya_token", data.token);
    renderUserHeader();
    closeAuthModal();
    showToast("Registration successful! Account active.", "success");
    await loadHistory();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleForgotSubmit(e) {
  e.preventDefault();
  const email = document.getElementById("forgot-email").value;
  try {
    const res = await fetch("/api/auth/forgot-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");
    const infoBox = document.getElementById("forgot-info-box");
    if (infoBox) {
      infoBox.style.display = "block";
      infoBox.innerHTML = `
        <strong>Reset Token Generated:</strong> <code>${data.reset_token}</code><br>
        <span style="font-size:0.8rem">Copy this token to reset your password.</span>
      `;
    }
    showToast("Password reset token generated.", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

function handleLogout() {
  if (state.token) {
    fetch("/api/auth/logout", {
      method: "POST",
      headers: { "Authorization": `Bearer ${state.token}` }
    }).catch(() => {});
  }
  state.user = null;
  state.token = null;
  localStorage.removeItem("nyaya_token");
  renderUserHeader();
  showToast("Logged out successfully.", "info");
  handleDemoLogin();
}

function openAuthModal() {
  const modal = document.getElementById("auth-modal");
  if (modal) modal.classList.add("open");
}

function closeAuthModal() {
  const modal = document.getElementById("auth-modal");
  if (modal) modal.classList.remove("open");
}

// Case Search & Selection
async function handleCaseSearch(query) {
  const dropdown = document.getElementById("case-search-dropdown");
  if (!dropdown) return;

  if (!query || query.length < 2) {
    dropdown.classList.remove("show");
    dropdown.innerHTML = "";
    return;
  }

  try {
    const res = await fetch(`/api/cases?q=${encodeURIComponent(query)}&limit=10`);
    const data = await res.json();
    if (data.cases && data.cases.length > 0) {
      dropdown.innerHTML = data.cases.map(c => `
        <div class="search-result-item" onclick="selectCaseById('${c.id}')">
          <div class="search-result-title">${escapeHtml(c.title)}</div>
          <div class="search-result-meta">
            <span><strong>Citation:</strong> ${escapeHtml(c.citation || 'N/A')}</span>
            <span><strong>Year:</strong> ${c.year || 'N/A'}</span>
            <span><strong>Court:</strong> ${escapeHtml(c.court || 'Supreme Court')}</span>
          </div>
        </div>
      `).join("");
      dropdown.classList.add("show");
    } else {
      dropdown.innerHTML = `
        <div class="search-result-item" style="color:var(--slate-500); cursor:default;">
          No matching case found locally. <a href="#" onclick="showView('missing-cases'); return false;" style="color:var(--gold-500); font-weight:600;">Report Missing Case or Upload PDF &rarr;</a>
        </div>
      `;
      dropdown.classList.add("show");
    }
  } catch (err) {
    console.error("Search failed:", err);
  }
}

async function selectCaseById(caseId) {
  try {
    const res = await fetch(`/api/cases/${caseId}`);
    if (!res.ok) throw new Error("Could not load case details");
    const caseData = await res.json();
    setCaseSelection(caseData);
  } catch (err) {
    showToast(err.message, "error");
  }
}

function setCaseSelection(caseData) {
  state.selectedCase = caseData;
  const searchInput = document.getElementById("input-case-search");
  const caseIdInput = document.getElementById("input-selected-case-id");
  const caseBadge = document.getElementById("selected-case-badge");
  const dropdown = document.getElementById("case-search-dropdown");

  if (searchInput) searchInput.value = caseData.title;
  if (caseIdInput) caseIdInput.value = caseData.id;
  if (dropdown) dropdown.classList.remove("show");

  if (caseBadge) {
    caseBadge.style.display = "block";
    caseBadge.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <strong style="color:var(--navy-900); font-size:0.95rem;">${escapeHtml(caseData.title)}</strong><br>
          <span style="font-size:0.82rem; color:var(--slate-600);">
            <strong>Citation:</strong> ${escapeHtml(caseData.citation || 'N/A')} | 
            <strong>Bench:</strong> ${escapeHtml(caseData.judge || 'Supreme Court')} | 
            <strong>Date:</strong> ${escapeHtml(caseData.decision_date || 'N/A')}
          </span>
        </div>
        <button type="button" class="btn btn-outline btn-sm" onclick="clearSelectedCase()">Change</button>
      </div>
    `;
  }
}

function clearSelectedCase() {
  state.selectedCase = null;
  const searchInput = document.getElementById("input-case-search");
  const caseIdInput = document.getElementById("input-selected-case-id");
  const caseBadge = document.getElementById("selected-case-badge");

  if (searchInput) searchInput.value = "";
  if (caseIdInput) caseIdInput.value = "";
  if (caseBadge) caseBadge.style.display = "none";
}

// 1-Click Preset Scenario Loader
async function loadPresets() {
  try {
    const res = await fetch("/api/cases/presets/samples");
    const data = await res.json();
    state.presets = data.presets || [];
    renderPresetCards();
  } catch (err) {
    console.error("Presets loading error:", err);
  }
}

function renderPresetCards() {
  const container = document.getElementById("preset-cards-container");
  if (!container) return;
  container.innerHTML = state.presets.map((p, idx) => {
    let badgeClass = "exact";
    if (p.expected_status.includes("Modified")) badgeClass = "modified";
    if (p.expected_status.includes("Not Found")) badgeClass = "notfound";
    if (p.expected_status.includes("Inconclusive")) badgeClass = "inconclusive";
    if (p.expected_status.includes("Missing")) badgeClass = "notfound";

    return `
      <div class="preset-card" onclick="applyPreset(${idx})">
        <span class="preset-badge status-badge ${badgeClass}">${escapeHtml(p.expected_status)}</span>
        <div class="preset-title">${escapeHtml(p.label)}</div>
        <div class="preset-desc">${escapeHtml(p.description)}</div>
      </div>
    `;
  }).join("");
}

function applyPreset(index) {
  const p = state.presets[index];
  if (!p) return;

  if (p.id === "sample-missing-case") {
    // Show missing case guidance view
    showView("missing-cases");
    const caseNameInput = document.getElementById("ticket-case-name");
    const citInput = document.getElementById("ticket-citation");
    if (caseNameInput) caseNameInput.value = p.case_title;
    if (citInput) citInput.value = p.citation;
    showToast("Opened Missing Cases Guide with sample fictitious citation", "info");
    return;
  }

  showView("verify");
  selectCaseById(p.judgment_id);
  const quoteInput = document.getElementById("input-quote-text");
  if (quoteInput) {
    quoteInput.value = p.quote;
    quoteInput.dispatchEvent(new Event("input"));
  }
  showToast(`Loaded test preset: ${p.label}`, "info");
}

// Verification Execution
async function handleVerifySubmit(e) {
  e.preventDefault();
  const caseId = document.getElementById("input-selected-case-id").value;
  const quoteText = document.getElementById("input-quote-text").value.trim();

  if (!caseId) {
    showToast("Please search and select a court judgment first.", "warning");
    return;
  }
  if (!quoteText) {
    showToast("Please paste the AI quotation to be verified.", "warning");
    return;
  }

  setVerificationLoading(true);

  try {
    const res = await fetch("/api/verify", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.token}`
      },
      body: JSON.stringify({
        judgment_id: caseId,
        submitted_quote: quoteText
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Verification failed");

    state.currentVerification = data;
    renderVerificationResult(data);
    await loadHistory();
    await loadStats();
    showToast(`Verification complete: ${data.status}`, "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    setVerificationLoading(false);
  }
}

function setVerificationLoading(isLoading) {
  const btn = document.getElementById("btn-run-verify");
  const loadingBanner = document.getElementById("verification-loading-state");
  if (btn) {
    btn.disabled = isLoading;
    btn.innerHTML = isLoading ? `<span class="spinner"></span> Verifying Judgment Record...` : `⚖️ Verify Quotation Now`;
  }
  if (loadingBanner) {
    loadingBanner.style.display = isLoading ? "block" : "none";
  }
}

// Result Card Rendering
function renderVerificationResult(data) {
  const resultContainer = document.getElementById("verification-result-wrapper");
  if (!resultContainer) return;

  let badgeClass = "inconclusive";
  let statusIcon = "⚖️";
  if (data.status === "Exact Match") {
    badgeClass = "exact";
    statusIcon = "✅";
  } else if (data.status === "Modified Quote") {
    badgeClass = "modified";
    statusIcon = "⚠️";
  } else if (data.status === "Quote Not Found") {
    badgeClass = "notfound";
    statusIcon = "❌";
  } else if (data.status === "Inconclusive") {
    badgeClass = "inconclusive";
    statusIcon = "📄";
  }

  const diff = data.diff || {};
  const diffTokens = diff.diff_tokens || [];

  // Generate word diff HTML
  let diffHtml = "";
  if (diffTokens.length > 0) {
    diffHtml = diffTokens.map(tok => {
      if (tok.type === "match") {
        return `<span class="token-match">${escapeHtml(tok.text)}</span>`;
      } else if (tok.type === "modified") {
        return `<span class="token-modified" title="Original: ${escapeHtml(tok.orig_text)}">${escapeHtml(tok.text)}</span>`;
      } else if (tok.type === "inserted") {
        return `<span class="token-inserted" title="Added by AI">${escapeHtml(tok.text)}</span>`;
      } else if (tok.type === "deleted") {
        return `<span class="token-deleted" title="Omitted from judgment">${escapeHtml(tok.orig_text)}</span>`;
      }
      return escapeHtml(tok.text);
    }).join(" ");
  } else {
    diffHtml = escapeHtml(data.submitted_quote || "");
  }

  const caseDet = data.case_details || {};
  const pageDisp = data.page_number ? `Page ${data.page_number}` : (data.total_pages ? `Document (${data.total_pages} pages)` : "Full Judgment Record");

  resultContainer.innerHTML = `
    <div class="result-card">
      <div class="result-header">
        <div class="result-badge-group">
          <span class="status-badge ${badgeClass}">${statusIcon} ${escapeHtml(data.status)}</span>
          <span style="font-size:0.88rem; color:var(--slate-500);">Verified on ${pageDisp}</span>
        </div>
        <div class="score-meter">
          <span class="score-number">${data.similarity_score}%</span>
          <span class="score-label">Match Similarity</span>
        </div>
      </div>

      <div class="diff-container">
        <div style="margin-bottom:1rem; font-weight:700; color:var(--navy-900);">
          ${escapeHtml(caseDet.title || data.case_title || "Court Judgment")}
          <span style="font-size:0.82rem; font-weight:400; color:var(--slate-500); margin-left:8px;">
            [Citation: ${escapeHtml(caseDet.citation || 'Official Record')}]
          </span>
        </div>

        <div class="diff-legend">
          <div class="legend-item"><span class="legend-dot" style="background:#10B981;"></span> Identical Words (${diff.matches_count || 0})</div>
          <div class="legend-item"><span class="legend-dot" style="background:#F59E0B;"></span> Changed / Substituted (${diff.modified_count || 0})</div>
          <div class="legend-item"><span class="legend-dot" style="background:#EF4444;"></span> Omitted Text (${diff.deleted_count || 0})</div>
          <div class="legend-item"><span class="legend-dot" style="background:#8B5CF6;"></span> Hallucinated / Added (${diff.inserted_count || 0})</div>
        </div>

        <!-- Inline Diff Box -->
        <div id="diff-inline-view">
          <div class="form-label">Quotation Comparison Analysis:</div>
          <div class="diff-box">${diffHtml}</div>
        </div>

        <!-- Side-by-side view -->
        <div class="comparison-grid">
          <div class="passage-card">
            <div class="passage-title">
              <span>Submitted AI Quotation</span>
              <span class="badge" style="background:#F1F5F9; color:#475569; padding:2px 6px; border-radius:4px; font-size:0.75rem;">Source Text</span>
            </div>
            <div class="passage-text">"${escapeHtml(state.currentVerification.submitted_quote || '')}"</div>
          </div>
          <div class="passage-card">
            <div class="passage-title">
              <span>Original Verified Court Record</span>
              <span class="badge" style="background:#ECFDF5; color:#065F46; padding:2px 6px; border-radius:4px; font-size:0.75rem;">${pageDisp}</span>
            </div>
            <div class="passage-text">
              ${data.matched_text ? `"${escapeHtml(data.matched_text)}"` : `<em>No authentic matching paragraph located in this judgment.</em>`}
            </div>
          </div>
        </div>

        ${data.explanation ? `
          <div class="banner-notice ${data.status === 'Quote Not Found' ? 'warning' : 'info'}" style="margin-top:1.25rem;">
            <div>
              <div class="banner-title">Judicial Analysis Note:</div>
              <div class="banner-desc">${escapeHtml(data.explanation)}</div>
            </div>
          </div>
        ` : ''}
      </div>

      <div class="result-footer">
        <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
          <a href="/api/verifications/${data.verification_id}/report.pdf" class="btn btn-navy btn-sm" download>
            📄 Download Official PDF Report
          </a>
          <a href="/api/verifications/${data.verification_id}/report.json" class="btn btn-outline btn-sm" download>
            💾 Download JSON Audit
          </a>
        </div>
        <div>
          ${caseDet.source_url ? `
            <a href="${caseDet.source_url}" target="_blank" class="btn btn-outline btn-sm">
              🌐 View Original Court Record &rarr;
            </a>
          ` : ''}
          <button type="button" class="btn btn-primary btn-sm" onclick="resetVerificationForm()">Verify Another</button>
        </div>
      </div>
    </div>
  `;

  resultContainer.scrollIntoView({ behavior: "smooth", block: "start" });
}

function resetVerificationForm() {
  clearSelectedCase();
  const quoteInput = document.getElementById("input-quote-text");
  if (quoteInput) quoteInput.value = "";
  const resultContainer = document.getElementById("verification-result-wrapper");
  if (resultContainer) resultContainer.innerHTML = "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Uploaded PDF Verification
function handleFileSelected(file) {
  const filenameDisplay = document.getElementById("uploaded-filename-badge");
  if (filenameDisplay) {
    filenameDisplay.style.display = "block";
    filenameDisplay.innerHTML = `<strong>Selected Document:</strong> ${escapeHtml(file.name)} (${(file.size / (1024*1024)).toFixed(2)} MB)`;
  }
}

async function handleUploadVerifySubmit(e) {
  e.preventDefault();
  const fileInput = document.getElementById("file-pdf-upload");
  const quoteInput = document.getElementById("upload-quote-text");
  const titleInput = document.getElementById("upload-case-title");

  if (!fileInput.files || fileInput.files.length === 0) {
    showToast("Please select a PDF document to upload.", "warning");
    return;
  }
  const quote = quoteInput.value.trim();
  if (!quote) {
    showToast("Please paste the quotation to verify against the PDF.", "warning");
    return;
  }

  const btn = document.getElementById("btn-run-upload-verify");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Extracting & Verifying Document...`;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("submitted_quote", quote);
  formData.append("case_title", titleInput.value.trim() || "Uploaded Court Record");

  try {
    const res = await fetch("/api/verify/upload-pdf", {
      method: "POST",
      headers: { "Authorization": `Bearer ${state.token}` },
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload verification failed");

    state.currentVerification = data;
    renderVerificationResult(data);
    await loadHistory();
    await loadStats();
    showToast(`Verification complete: ${data.status}`, "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `Verify Against Uploaded PDF`;
    }
  }
}

// Verification History
async function loadHistory() {
  if (!state.token) return;
  try {
    const res = await fetch("/api/verifications", {
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    const data = await res.json();
    state.history = data.verifications || [];
    renderHistoryTable();
  } catch (err) {
    console.error("Failed to load history:", err);
  }
}

function renderHistoryTable() {
  const container = document.getElementById("history-table-body");
  if (!container) return;

  if (state.history.length === 0) {
    container.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; padding:2rem; color:var(--slate-500);">
          No verification records found in your account. Perform a verification to view history.
        </td>
      </tr>
    `;
    return;
  }

  container.innerHTML = state.history.map(h => {
    let badgeClass = "inconclusive";
    if (h.verification_status === "Exact Match") badgeClass = "exact";
    if (h.verification_status === "Modified Quote") badgeClass = "modified";
    if (h.verification_status === "Quote Not Found") badgeClass = "notfound";

    const dateStr = h.created_at ? h.created_at.replace("T", " ").substring(0, 16) : "Recent";
    const quoteSnippet = h.submitted_quote ? h.submitted_quote.substring(0, 75) + "..." : "";

    return `
      <tr>
        <td><strong>${escapeHtml(h.case_title)}</strong><br><span style="font-size:0.75rem; color:var(--slate-500);">${escapeHtml(h.citation || 'N/A')}</span></td>
        <td><span style="font-size:0.82rem; color:var(--slate-700);">"${escapeHtml(quoteSnippet)}"</span></td>
        <td><span class="status-badge ${badgeClass}" style="font-size:0.75rem; padding:0.25rem 0.65rem;">${escapeHtml(h.verification_status)}</span></td>
        <td><strong>${h.similarity_score}%</strong></td>
        <td><span style="font-size:0.78rem; color:var(--slate-500);">${dateStr}</span></td>
        <td>
          <div style="display:flex; gap:0.35rem;">
            <a href="/api/verifications/${h.id}/report.pdf" class="btn btn-outline btn-sm" download title="PDF Report">PDF</a>
            <a href="/api/verifications/${h.id}/report.json" class="btn btn-outline btn-sm" download title="JSON Report">JSON</a>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

// Support Request Submission
async function handleSupportSubmit(e) {
  e.preventDefault();
  const caseName = document.getElementById("ticket-case-name").value;
  const citation = document.getElementById("ticket-citation").value;
  const court = document.getElementById("ticket-court").value;
  const category = document.getElementById("ticket-category").value;
  const desc = document.getElementById("ticket-desc").value;
  const email = document.getElementById("ticket-email").value;

  const btn = document.getElementById("btn-submit-ticket");
  if (btn) btn.disabled = true;

  try {
    const res = await fetch("/api/support/tickets", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.token}`
      },
      body: JSON.stringify({
        case_name: caseName,
        citation,
        court,
        issue_category: category,
        description: desc,
        contact_email: email
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Submission failed");

    const confBox = document.getElementById("support-confirmation-box");
    if (confBox) {
      confBox.style.display = "block";
      confBox.innerHTML = `
        <div class="banner-notice info">
          <div>
            <div class="banner-title">Help Request Registered Successfully!</div>
            <div class="banner-desc">
              Your inquiry has been assigned Tracking ID: <strong>${data.ticket_id}</strong>.<br>
              The judicial dataset curation desk will review the citation and document availability.
            </div>
          </div>
        </div>
      `;
    }
    showToast("Help request submitted successfully!", "success");
    e.target.reset();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

// System Stats
async function loadStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    state.stats = data;

    const elJudgments = document.getElementById("stat-total-judgments");
    const elVerifications = document.getElementById("stat-total-verifications");
    const elExact = document.getElementById("stat-exact-matches");
    const elModified = document.getElementById("stat-modified-matches");

    if (elJudgments) elJudgments.textContent = data.total_judgments_indexed || "0";
    if (elVerifications) elVerifications.textContent = data.total_verifications_performed || "0";
    if (elExact) elExact.textContent = data.status_distribution["Exact Match"] || "0";
    if (elModified) elModified.textContent = data.status_distribution["Modified Quote"] || "0";
  } catch (err) {
    console.error("Failed to load statistics:", err);
  }
}

// Toast Notifications
function showToast(message, type = "info") {
  let toastContainer = document.getElementById("toast-container");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toast-container";
    toastContainer.style.cssText = "position:fixed; bottom:20px; right:20px; z-index:9999; display:flex; flex-direction:column; gap:8px;";
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement("div");
  let bg = "#1E293B";
  let border = "#C5A059";
  if (type === "success") { bg = "#065F46"; border = "#10B981"; }
  if (type === "error") { bg = "#991B1B"; border = "#F43F5E"; }
  if (type === "warning") { bg = "#92400E"; border = "#F59E0B"; }

  toast.style.cssText = `
    background: ${bg};
    color: #fff;
    border-left: 4px solid ${border};
    padding: 12px 18px;
    border-radius: 6px;
    font-size: 0.88rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    min-width: 260px;
    max-width: 400px;
    animation: slideIn 0.25s ease-out;
  `;
  toast.textContent = message;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Utility: HTML Escaping
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
