const log = document.getElementById("log");
const form = document.getElementById("form");
const q = document.getElementById("q");
const emp = document.getElementById("emp");

function bubble(role, text, tools) {
  const empty = log.querySelector(".empty");
  if (empty) empty.remove();
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.innerHTML = `<div class="role">${role}</div><div>${text}</div>` +
    (tools && tools.length ? `<div class="tools">tools: ${tools.join(", ")}</div>` : "");
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

function loadingBubble() {
  const div = document.createElement("div");
  div.className = "msg agent loading";
  div.innerHTML = `<div class="role">agent</div><div>Thinking<span class="dots"><span></span><span></span><span></span></span></div>`;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

const btn = form.querySelector("button");
q.addEventListener("input", () => { btn.disabled = q.value.trim() === ""; });

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = q.value.trim();
  if (!text) return;
  bubble("user", text);
  q.value = "";
  btn.disabled = true; q.disabled = true;
  const loader = loadingBubble();
  try {
    const res = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: text, employee_id: emp.value.trim() || "EMP101" }),
    });
    const data = await res.json();
    loader.remove();
    bubble("agent", data.answer || "(no answer)", data.tools);
  } catch (err) {
    loader.remove();
    q.value = text;
    bubble("agent", "Network error: " + err.message + " — your text is restored.");
  } finally {
    btn.disabled = q.value.trim() === ""; q.disabled = false; q.focus();
  }
});

// Empty state + autofocus
window.addEventListener("DOMContentLoaded", () => {
  if (!log.children.length) {
    const e = document.createElement("div");
    e.className = "empty";
    e.textContent = "Ask a policy question or book leave to get started.";
    log.appendChild(e);
  }
  q.focus();
});