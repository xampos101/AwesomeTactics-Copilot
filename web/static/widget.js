(() => {
  const script = document.currentScript;
  const apiBase = (script?.dataset?.apiBase || "").replace(/\/$/, "") || "http://localhost:8000";
  const title = script?.dataset?.title || "Tactics Copilot";
  const subtitle = script?.dataset?.subtitle || "RAG over Awesome & Dark Tactics";
  const defaultMode = script?.dataset?.mode || "recommend";
  const defaultTopK = Number(script?.dataset?.topK || 8);

  const cssHref = `${apiBase}/widget.css`;
  const css = document.createElement("link");
  css.rel = "stylesheet";
  css.href = cssHref;
  document.head.appendChild(css);

  const elFab = document.createElement("button");
  elFab.className = "tc-fab";
  elFab.type = "button";
  elFab.setAttribute("aria-label", "Open tactics copilot");
  elFab.innerHTML = `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 2a8 8 0 0 0-8 8c0 3.3 2 6.1 4.9 7.4V22l3.1-1.8 3.1 1.8v-4.6A8 8 0 0 0 20 10a8 8 0 0 0-8-8Zm0 2a6 6 0 0 1 6 6c0 2.5-1.6 4.7-3.9 5.6l-.7.3V18l-1.4-.8-1.4.8v-2.1l-.7-.3A6 6 0 0 1 6 10a6 6 0 0 1 6-6Z"></path>
    </svg>
  `;

  const elPanel = document.createElement("div");
  elPanel.className = "tc-panel";
  elPanel.innerHTML = `
    <div class="tc-header">
      <div>
        <div class="tc-title"></div>
        <div class="tc-subtitle"></div>
      </div>
      <button class="tc-close" type="button" aria-label="Close">Close</button>
    </div>
    <div class="tc-body"></div>
    <div class="tc-meta"></div>
    <div class="tc-footer">
      <textarea class="tc-input" rows="1" placeholder="Ask for tactics (e.g., edge devices always on)…"></textarea>
      <button class="tc-send" type="button">Send</button>
    </div>
  `;

  const titleEl = elPanel.querySelector(".tc-title");
  const subtitleEl = elPanel.querySelector(".tc-subtitle");
  const closeBtn = elPanel.querySelector(".tc-close");
  const bodyEl = elPanel.querySelector(".tc-body");
  const metaEl = elPanel.querySelector(".tc-meta");
  const inputEl = elPanel.querySelector(".tc-input");
  const sendBtn = elPanel.querySelector(".tc-send");

  titleEl.textContent = title;
  subtitleEl.textContent = subtitle;

  function appendMsg(role, text) {
    const el = document.createElement("div");
    el.className = `tc-msg ${role === "user" ? "tc-user" : "tc-assistant"}`;
    el.textContent = text;
    bodyEl.appendChild(el);
    bodyEl.scrollTop = bodyEl.scrollHeight;
  }

  function setMeta(html) {
    metaEl.innerHTML = html || "";
  }

  function openPanel() {
    elPanel.classList.add("tc-open");
    setTimeout(() => inputEl.focus(), 0);
  }

  function closePanel() {
    elPanel.classList.remove("tc-open");
  }

  async function ask(query) {
    const mode = defaultMode;
    const topK = Number.isFinite(defaultTopK) ? defaultTopK : 8;

    sendBtn.disabled = true;
    inputEl.disabled = true;
    appendMsg("assistant", "Thinking…");
    const thinkingEl = bodyEl.lastElementChild;

    try {
      const resp = await fetch(`${apiBase}/api/chat?mode=${encodeURIComponent(mode)}&top_k=${topK}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err?.detail || `HTTP ${resp.status}`);
      }

      const data = await resp.json();

      // Remove "Thinking…" placeholder
      if (thinkingEl && thinkingEl.parentNode) thinkingEl.parentNode.removeChild(thinkingEl);

      const parsed = data?.parsed || {};
      const modeOut = parsed?.mode || mode;

      if (parsed?.parse_error) {
        appendMsg("assistant", data?.raw_response || "(No response)");
        setMeta(`Model: ${data?.model || ""}`);
        return;
      }

      if (modeOut === "recommend") {
        const summary = parsed?.summary || "";
        const tactics = Array.isArray(parsed?.tactics) ? parsed.tactics : [];
        const lines = [];
        if (summary) lines.push(summary.trim());
        if (tactics.length) {
          lines.push("");
          lines.push("Recommended tactics:");
          for (const t of tactics.slice(0, 5)) {
            lines.push(`- ${t.tactic_name || "Tactic"} (${t.category || ""}) — ${t.tactic_type || ""}`);
            if (t.description) lines.push(`  ${String(t.description).trim()}`);
          }
        }
        appendMsg("assistant", lines.join("\n").trim() || "(No answer)");
      } else {
        // critique / compare or other modes: show compact JSON for now
        appendMsg("assistant", JSON.stringify(parsed, null, 2));
      }

      const sources = Array.isArray(data?.retrieved_tactics) ? data.retrieved_tactics : [];
      if (sources.length) {
        const links = sources
          .slice(0, 3)
          .map((s) => {
            const url = s.url || "";
            const title = (s.title || "Source").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            return url ? `<a href="${url}" target="_blank" rel="noreferrer">${title}</a>` : title;
          })
          .join(" · ");
        setMeta(`Sources: ${links}<br/>Model: ${data?.model || ""} · ${Math.round((data?.latency_seconds || 0) * 10) / 10}s`);
      } else {
        setMeta(`Model: ${data?.model || ""}`);
      }
    } catch (e) {
      if (thinkingEl && thinkingEl.parentNode) thinkingEl.parentNode.removeChild(thinkingEl);
      appendMsg("assistant", `Error: ${e?.message || e}`);
      setMeta("");
    } finally {
      sendBtn.disabled = false;
      inputEl.disabled = false;
      inputEl.focus();
    }
  }

  function handleSend() {
    const q = (inputEl.value || "").trim();
    if (!q) return;
    inputEl.value = "";
    appendMsg("user", q);
    ask(q);
  }

  elFab.addEventListener("click", () => {
    const open = elPanel.classList.contains("tc-open");
    if (open) closePanel();
    else openPanel();
  });
  closeBtn.addEventListener("click", closePanel);
  sendBtn.addEventListener("click", handleSend);

  inputEl.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      handleSend();
    }
  });

  // Insert into page
  document.body.appendChild(elFab);
  document.body.appendChild(elPanel);

  // Initial greeting
  appendMsg("assistant", "Ask me to recommend tactics for your scenario. I’ll cite retrieved tactics from the catalog.");
})();

