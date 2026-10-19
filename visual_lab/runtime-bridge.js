(() => {
  "use strict";

  const EVENTS = [
    ["UNCLEAR", "Unclear situation / ask context"],
    ["SUPPORTIVE_ADVICE", "Supportive advice"],
    ["REASONABLE_REQUEST", "Reasonable request"],
    ["UNJUSTIFIED_RESTRICTION", "Unjustified restriction"],
    ["DISRESPECT", "Disrespect"],
    ["HONEST_MISTAKE", "Honest mistake"],
    ["REPEATED_HARM", "Repeated harmful pattern"],
    ["GENUINE_APOLOGY", "Genuine apology"],
    ["ACCOUNTABILITY_WITH_CHANGE", "Accountability with change"],
    ["BOUNDARY_RESPECTED", "Boundary respected"]
  ];

  const panel = document.createElement("section");
  panel.id = "runtime-bridge-panel";
  panel.style.cssText = [
    "margin-top:18px;padding:14px;border:1px solid #65744a",
    "border-radius:8px;background:#20271b;color:#f4f2e9"
  ].join(";");

  panel.innerHTML = `
    <h2 style="margin:0 0 10px;font-size:17px">Live Behaviour Runtime</h2>
    <div id="runtime-status" role="status" style="font-size:12px;color:#c9e58a">
      Connecting to Python…
    </div>
    <div style="margin-top:12px;font-size:11px;color:#aeb6a3">CURRENT RESPONSE</div>
    <div id="runtime-dialogue" aria-live="polite" style="margin-top:5px;line-height:1.5">
      Waiting for the behaviour engine…
    </div>
    <details style="margin-top:10px">
      <summary style="cursor:pointer;color:#c9e58a">Why did the character respond this way?</summary>
      <p id="runtime-explanation" style="font-size:12px;line-height:1.5"></p>
      <pre id="runtime-state" style="white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;color:#d6ddc9"></pre>
    </details>
    <label for="runtime-event" style="display:block;margin-top:14px;font-size:12px">
      Test a structured interaction
    </label>
    <select id="runtime-event" style="margin-top:6px;width:100%;padding:9px"></select>
    <input id="runtime-description" maxlength="500"
      placeholder="Optional context (e.g. a boundary was ignored again)"
      style="margin-top:8px;width:100%;padding:9px;box-sizing:border-box">
    <button id="runtime-send" type="button"
      style="margin-top:8px;width:100%;padding:10px;cursor:pointer">
      Send to behaviour engine
    </button>
    <div style="font-size:10px;color:#9ea695;margin-top:7px">
      Structured-event prototype. This does not yet interpret free text with an LLM.
    </div>
  `;

  const host = document.querySelector(".panel") || document.querySelector("main") || document.body;
  host.appendChild(panel);

  const $ = id => document.getElementById(id);
  for (const [value, label] of EVENTS) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    $("runtime-event").appendChild(option);
  }

  let lastSequence = -1;
  let requestInProgress = false;

  async function readState() {
    try {
      const response = await fetch("/api/state", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      $("runtime-status").textContent =
        `● CONNECTED · ${data.action} · interaction ${data.sequence}`;
      $("runtime-status").style.color = "#c9e58a";

      if (data.sequence !== lastSequence) {
        lastSequence = data.sequence;
        $("runtime-dialogue").textContent = data.dialogue || "No dialogue returned.";
        $("runtime-explanation").textContent = data.explanation || "";
        $("runtime-state").textContent = JSON.stringify(data.state || {}, null, 2);

        if (window.characterVisuals && data.expression) {
          window.characterVisuals.setExpression(data.expression);
        }

        document.dispatchEvent(new CustomEvent("character-runtime-update", {
          detail: data
        }));
      }
    } catch (error) {
      $("runtime-status").textContent = "● OFFLINE · Start runtime_server.py";
      $("runtime-status").style.color = "#ff9a85";
    }
  }

  $("runtime-send").addEventListener("click", async () => {
    if (requestInProgress) return;
    requestInProgress = true;
    const button = $("runtime-send");
    button.disabled = true;
    button.textContent = "Processing…";

    try {
      const response = await fetch("/api/event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_type: $("runtime-event").value,
          description: $("runtime-description").value.trim(),
          evidence_strength: 0.7,
          context_known: $("runtime-event").value !== "UNCLEAR"
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      await readState();
      $("runtime-description").value = "";
    } catch (error) {
      $("runtime-status").textContent = `ERROR · ${error.message}`;
      $("runtime-status").style.color = "#ff9a85";
    } finally {
      requestInProgress = false;
      button.disabled = false;
      button.textContent = "Send to behaviour engine";
    }
  });

  readState();
  window.setInterval(readState, 300);
})();
