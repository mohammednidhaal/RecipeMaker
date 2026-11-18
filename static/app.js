// RecipeMate AI Live Assistant Client
const userId = "default_user";
const sessionId = "session_" + Math.random().toString(36).substring(2, 9);

const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const confirmationBanner = document.getElementById("confirmation-banner");
const confirmText = document.getElementById("confirm-text");
const confirmYesBtn = document.getElementById("confirm-yes-btn");
const confirmNoBtn = document.getElementById("confirm-no-btn");
const resetChatBtn = document.getElementById("reset-chat-btn");
const clearMemoryBtn = document.getElementById("clear-memory-btn");
const quickChips = document.querySelectorAll(".quick-chip");
const liveIndicator = document.getElementById("live-indicator");

// Modal Elements
const openKeyModalBtn = document.getElementById("open-key-modal-btn");
const closeKeyModalBtn = document.getElementById("close-key-modal-btn");
const cancelKeyBtn = document.getElementById("cancel-key-btn");
const saveKeyBtn = document.getElementById("save-key-btn");
const apiKeyModal = document.getElementById("api-key-modal");
const apiKeyInput = document.getElementById("api-key-input");
const providerSelect = document.getElementById("provider-select");

// Sidebar elements
const agentStepBadge = document.getElementById("agent-step-badge");
const planBox = document.getElementById("plan-box");
const actionLogsList = document.getElementById("action-logs-list");
const activeRecipeBody = document.getElementById("active-recipe-body");
const servingStepper = document.getElementById("serving-stepper");
const servingsDisplay = document.getElementById("servings-display");
const servingsDecBtn = document.getElementById("servings-dec-btn");
const servingsIncBtn = document.getElementById("servings-inc-btn");
const preferencesBody = document.getElementById("preferences-body");

let currentServings = 2;

// Check connection settings on start
async function checkSettings() {
  try {
    const res = await fetch("/api/settings");
    if (res.ok) {
      const data = await res.json();
      if (data.live_llm_active) {
        liveIndicator.innerHTML = `<span class="pulse-dot"></span> Live AI (${data.default_provider.toUpperCase()})`;
      } else {
        liveIndicator.innerHTML = `<span class="pulse-dot"></span> Live Assistant (Universal Synthesizer)`;
      }
    }
  } catch (e) {}
}
checkSettings();

// Markdown formatter
function formatMarkdown(text) {
  if (!text) return "";
  let html = text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 style="color: #E25822; margin-top: 12px; margin-bottom: 6px;">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/^- (.*$)/gim, '<li>$1</li>')
    .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
    .replace(/\n\n/g, '<br><br>');

  html = html.replace(/(<li>[\s\S]*?<\/li>)/gm, '<ul>$1</ul>');
  html = html.replace(/<\/ul>\s*<ul>/g, '');
  return html;
}

function appendMessage(sender, text) {
  const row = document.createElement("div");
  row.className = `message-row ${sender === "user" ? "user-row" : "ai-row"}`;

  const avatar = document.createElement("div");
  avatar.className = `avatar ${sender === "user" ? "user-avatar" : "ai-avatar"}`;
  avatar.textContent = sender === "user" ? "👤" : "🍳";

  const content = document.createElement("div");
  content.className = "message-content";

  const bubble = document.createElement("div");
  bubble.className = `bubble ${sender === "user" ? "user-bubble" : "ai-bubble"}`;
  bubble.innerHTML = formatMarkdown(text);

  content.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(content);

  chatMessages.appendChild(row);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage(message) {
  if (!message || !message.trim()) return;

  appendMessage("user", message);
  userInput.value = "";
  userInput.focus();

  agentStepBadge.textContent = "Cooking up response...";
  agentStepBadge.className = "badge info";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        user_id: userId,
        session_id: sessionId
      })
    });

    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }

    const data = await res.json();
    appendMessage("ai", data.response);
    updateAgentStateUI(data);

  } catch (err) {
    appendMessage("ai", `⚠️ Error: Could not connect to assistant. (${err.message})`);
    agentStepBadge.textContent = "Error";
  }
}

function updateAgentStateUI(data) {
  agentStepBadge.textContent = "Ready";

  // 1. Update Plan
  if (data.plan && data.plan.steps && data.plan.steps.length > 0) {
    let planHtml = `<p><strong>Goal:</strong> ${data.plan.goal}</p><ul class="plan-steps">`;
    data.plan.steps.forEach((step, idx) => {
      const isDone = idx < data.plan.current_step_index;
      planHtml += `<li>${isDone ? "✅" : "⏳"} ${step}</li>`;
    });
    planHtml += `</ul>`;
    planBox.innerHTML = planHtml;
  }

  // 2. Update Action Logs
  if (data.action_logs && data.action_logs.length > 0) {
    actionLogsList.innerHTML = "";
    data.action_logs.forEach(log => {
      const li = document.createElement("li");
      li.className = "log-item";
      li.textContent = `[${log.timestamp.slice(11, 19)}] ${log.event_type}`;
      actionLogsList.appendChild(li);
    });
    actionLogsList.scrollTop = actionLogsList.scrollHeight;
  }

  // 3. Update Active Recipe
  const rec = data.state.current_recipe;
  if (rec) {
    servingStepper.style.display = "flex";
    currentServings = rec.servings;
    servingsDisplay.textContent = `${rec.servings} serving(s)`;

    let recHtml = `
      <h4 style="color: #E25822; margin-bottom: 4px;">${rec.name}</h4>
      <p style="font-size: 0.8rem; color: #64748B; margin-bottom: 8px;">
        ⏱️ Prep: ${rec.prep_time}m | Cook: ${rec.cook_time}m | ${rec.difficulty}
      </p>
      <div style="font-size: 0.85rem;">
        <strong>Ingredients:</strong>
        <ul style="margin-left: 16px; margin-top: 4px;">
    `;
    rec.ingredients.forEach(i => {
      recHtml += `<li>${i.quantity} ${i.unit} ${i.name}</li>`;
    });
    recHtml += `</ul></div>`;
    activeRecipeBody.innerHTML = recHtml;
  }

  // 4. Update Memory / Preferences
  const prefs = data.state.preferences;
  if (prefs && prefs.length > 0) {
    preferencesBody.innerHTML = `<ul>${prefs.map(p => `<li>${p}</li>`).join("")}</ul>`;
  } else {
    preferencesBody.innerHTML = `<p class="empty-hint">No preferences saved in memory yet.</p>`;
  }

  // 5. Update Safety Confirmation Banner
  if (data.state.pending_confirmation) {
    confirmText.textContent = data.state.pending_confirmation.prompt;
    confirmationBanner.style.display = "flex";
  } else {
    confirmationBanner.style.display = "none";
  }
}

// Modal handling
openKeyModalBtn.addEventListener("click", () => {
  apiKeyModal.style.display = "flex";
  apiKeyInput.focus();
});

function closeModal() {
  apiKeyModal.style.display = "none";
}
closeKeyModalBtn.addEventListener("click", closeModal);
cancelKeyBtn.addEventListener("click", closeModal);

saveKeyBtn.addEventListener("click", async () => {
  const key = apiKeyInput.value.trim();
  const provider = providerSelect.value;
  if (!key) {
    alert("Please enter a valid API key.");
    return;
  }

  saveKeyBtn.textContent = "Connecting...";
  try {
    const res = await fetch("/api/settings/api-key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: key, provider: provider })
    });

    if (res.ok) {
      alert(`Success! Live ${provider.toUpperCase()} integration is now active.`);
      closeModal();
      checkSettings();
    } else {
      const err = await res.json();
      alert(`Error: ${err.detail || "Failed to save key"}`);
    }
  } catch (e) {
    alert(`Connection error: ${e.message}`);
  } finally {
    saveKeyBtn.textContent = "Save & Activate";
  }
});

// Event Listeners
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = userInput.value.trim();
  if (text) sendMessage(text);
});

quickChips.forEach(chip => {
  chip.addEventListener("click", () => {
    const prompt = chip.getAttribute("data-prompt");
    if (prompt) sendMessage(prompt);
  });
});

confirmYesBtn.addEventListener("click", () => {
  confirmationBanner.style.display = "none";
  sendMessage("Yes");
});

confirmNoBtn.addEventListener("click", () => {
  confirmationBanner.style.display = "none";
  sendMessage("No");
});

servingsIncBtn.addEventListener("click", () => {
  const next = currentServings + 1;
  sendMessage(`Make it for ${next} people.`);
});

servingsDecBtn.addEventListener("click", () => {
  if (currentServings > 1) {
    const prev = currentServings - 1;
    sendMessage(`Make it for ${prev} people.`);
  }
});

resetChatBtn.addEventListener("click", async () => {
  if (confirm("Reset conversation context and start fresh?")) {
    await fetch("/api/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, user_id: userId })
    });
    chatMessages.innerHTML = `
      <div class="message-row ai-row">
        <div class="avatar ai-avatar">🍳</div>
        <div class="message-content">
          <div class="bubble ai-bubble">
            <p>Session reset! What would you like to cook?</p>
          </div>
        </div>
      </div>
    `;
    planBox.innerHTML = `<p class="empty-hint">Observing user request.</p>`;
    activeRecipeBody.innerHTML = `<p class="empty-hint">No recipe selected yet.</p>`;
    servingStepper.style.display = "none";
  }
});

clearMemoryBtn.addEventListener("click", () => {
  sendMessage("Forget my preferences");
});
