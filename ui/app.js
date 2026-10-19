const log = document.getElementById("log");
const form = document.getElementById("form");
const q = document.getElementById("q");
const emp = document.getElementById("emp");

function bubble(role, text, tools) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.innerHTML = `<div class="role">${role}</div><div>${text}</div>` +
    (tools && tools.length ? `<div class="tools">tools: ${tools.join(", ")}</div>` : "");
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = q.value.trim();
  if (!text) return;
  bubble("user", text);
  q.value = "";
  try {
    const res = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: text, employee_id: emp.value.trim() || "EMP101" }),
    });
    const data = await res.json();
    bubble("agent", data.answer || "(no answer)", data.tools);
  } catch (err) {
    bubble("agent", "Network error: " + err.message);
  }
});