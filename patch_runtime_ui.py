from pathlib import Path

path = Path("visual_lab/index.html")
text = path.read_text(encoding="utf-8")

api = """
// Public bridge API: Python runtime can control this visual prototype.
window.characterVisuals = {
  setExpression(value) {
    const allowed = ["friendly", "curious", "thinking", "confident", "hurt"];
    if (!allowed.includes(value)) return;
    const control = document.getElementById("expression");
    if (control) control.value = value;
    updateAppearance();
  }
};
"""

anchor = "animate();\n</script>"
if anchor not in text:
    anchor = "animate();\r\n</script>"
if anchor not in text:
    raise SystemExit("PATCH FAILED: could not find animate(); closing script anchor. Backup remains available.")

if "window.characterVisuals" not in text:
    text = text.replace(anchor, "animate();\n" + api + "</script>", 1)

script_tag = '<script type="module" src="./runtime-bridge.js"></script>'
if script_tag not in text:
    closing = "</body>"
    if closing not in text:
        raise SystemExit("PATCH FAILED: could not find </body>.")
    text = text.replace(closing, script_tag + "\n" + closing, 1)

path.write_text(text, encoding="utf-8")
print("Patched visual_lab/index.html")
print("Added window.characterVisuals and runtime-bridge.js")
