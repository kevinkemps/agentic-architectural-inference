from __future__ import annotations

import json
import mimetypes
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

if __package__:
    from .evaluation.service import evaluate_diagram
    from .lib.llm import get_model
    from .pipeline import run_pipeline_with_details
else:  # pragma: no cover - supports running from inside aai/
    from evaluation.service import evaluate_diagram  # type: ignore[no-redef]
    from lib.llm import get_model  # type: ignore[no-redef]
    from pipeline import run_pipeline_with_details  # type: ignore[no-redef]


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = REPO_ROOT / "aai" / "output_analysis" / "runs"


def _safe_relative_artifact(path: Path) -> bool:
    try:
        path.resolve().relative_to(RUNS_ROOT.resolve())
        return True
    except ValueError:
        return False


def _selected_svg_path(rendered_assets: dict[str, list[str]]) -> Path | None:
    for label in ("refined", "draft"):
        for item in rendered_assets.get(label, []):
            path = Path(item)
            if path.suffix == ".svg" and path.exists():
                return path
    return None


def _run_mode(use_multi_agent: bool, use_critic: bool) -> tuple[str, int]:
    if not use_multi_agent:
        return "single_prompt", 0
    return "multi_agent", 1 if use_critic else 0


def _html_page() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AAI Diagram Workbench</title>
  <style>
    :root {
      --bg: #f5efe4;
      --panel: #fffaf2;
      --ink: #1e1c18;
      --muted: #6a6258;
      --accent: #0e6b50;
      --accent-2: #c65f37;
      --line: #d8ccbb;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #f6d8b8 0, transparent 22rem),
        linear-gradient(180deg, #f3eadc 0%, var(--bg) 55%, #efe3d2 100%);
    }
    .shell {
      max-width: 1280px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    .hero {
      display: grid;
      gap: 18px;
      margin-bottom: 22px;
    }
    .hero h1 {
      margin: 0;
      font-size: clamp(2rem, 5vw, 4rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }
    .hero p {
      margin: 0;
      max-width: 62rem;
      color: var(--muted);
      font-size: 1.05rem;
    }
    .grid {
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 18px;
    }
    .panel {
      background: rgba(255, 250, 242, 0.86);
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: 0 18px 40px rgba(60, 40, 15, 0.08);
      backdrop-filter: blur(8px);
    }
    .controls {
      padding: 20px;
      position: sticky;
      top: 20px;
      align-self: start;
    }
    label {
      display: block;
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 8px;
    }
    input[type="text"] {
      width: 100%;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: #fffdf9;
      color: var(--ink);
      font: inherit;
      margin-bottom: 18px;
    }
    .toggle {
      display: flex;
      gap: 10px;
      align-items: center;
      margin-bottom: 12px;
      font-size: 1rem;
    }
    .toggle input { accent-color: var(--accent); }
    .run {
      width: 100%;
      border: 0;
      border-radius: 999px;
      padding: 14px 18px;
      background: linear-gradient(135deg, var(--accent), #194f4a);
      color: white;
      font: inherit;
      font-weight: 600;
      cursor: pointer;
      margin-top: 12px;
    }
    .status {
      margin-top: 14px;
      min-height: 24px;
      color: var(--muted);
    }
    .workspace {
      padding: 14px;
      min-height: 70vh;
    }
    .tabs {
      display: flex;
      gap: 8px;
      padding: 8px;
    }
    .tab {
      border: 0;
      background: transparent;
      padding: 10px 14px;
      border-radius: 999px;
      cursor: pointer;
      font: inherit;
      color: var(--muted);
    }
    .tab.active {
      background: #efe2d0;
      color: var(--ink);
    }
    .tab-panel { display: none; padding: 8px; }
    .tab-panel.active { display: block; }
    .canvas, .analysis {
      padding: 14px;
      border-radius: 18px;
      background: #fffdf8;
      border: 1px solid var(--line);
      min-height: 60vh;
      overflow: auto;
    }
    .score {
      display: inline-flex;
      align-items: baseline;
      gap: 8px;
      font-size: 3rem;
      letter-spacing: -0.05em;
      color: var(--accent-2);
    }
    .meta {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
      margin: 16px 0 18px;
    }
    .card {
      padding: 12px 14px;
      border-radius: 16px;
      background: #f8efe3;
      border: 1px solid var(--line);
    }
    .q {
      padding: 14px 0;
      border-top: 1px solid var(--line);
    }
    .q:first-of-type { border-top: 0; }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #f5ede0;
      padding: 12px;
      border-radius: 14px;
      border: 1px solid var(--line);
    }
    .hidden { display: none; }
    @media (max-width: 980px) {
      .grid { grid-template-columns: 1fr; }
      .controls { position: static; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <h1>AAI Diagram Workbench</h1>
      <p>Generate a repository architecture diagram, switch between the multi-agent and single-prompt baselines, toggle the critic loop, and score the resulting diagram against repository-grounded answers.</p>
    </section>
    <section class="grid">
      <aside class="panel controls">
        <label for="repoPath">Repository Path</label>
        <input id="repoPath" type="text" placeholder="/absolute/path/to/repository">
        <label>Mode</label>
        <div class="toggle"><input id="multiAgent" type="checkbox" checked> <span>Use multi-agent pipeline</span></div>
        <div class="toggle"><input id="critic" type="checkbox" checked> <span>Enable critic loop</span></div>
        <button id="runButton" class="run">Generate Diagram + Score</button>
        <div id="status" class="status"></div>
      </aside>
      <main class="panel workspace">
        <div class="tabs">
          <button class="tab active" data-tab="diagram">Diagram</button>
          <button class="tab" data-tab="analysis">Analysis</button>
        </div>
        <section id="diagram" class="tab-panel active">
          <div id="diagramCanvas" class="canvas">No run yet.</div>
        </section>
        <section id="analysis" class="tab-panel">
          <div id="analysisCanvas" class="analysis">No evaluation yet.</div>
        </section>
      </main>
    </section>
  </div>
  <script>
    const statusEl = document.getElementById("status");
    const diagramCanvas = document.getElementById("diagramCanvas");
    const analysisCanvas = document.getElementById("analysisCanvas");
    const runButton = document.getElementById("runButton");
    const multiAgent = document.getElementById("multiAgent");
    const critic = document.getElementById("critic");
    const repoPath = document.getElementById("repoPath");

    document.querySelectorAll(".tab").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
        button.classList.add("active");
        document.getElementById(button.dataset.tab).classList.add("active");
      });
    });

    multiAgent.addEventListener("change", () => {
      critic.disabled = !multiAgent.checked;
      if (!multiAgent.checked) {
        critic.checked = false;
      }
    });

    function escapeHtml(value) {
      const div = document.createElement("div");
      div.textContent = value;
      return div.innerHTML;
    }

    function renderAnalysis(result) {
      const questions = result.evaluation.questions.map((item) => `
        <div class="q">
          <strong>${escapeHtml(item.question)}</strong>
          <div>Score: ${item.score}/5</div>
          <div>${escapeHtml(item.rationale || "")}</div>
        </div>
      `).join("");

      analysisCanvas.innerHTML = `
        <div class="score">${result.evaluation.overall_score.toFixed(1)} <span style="font-size:1rem;color:#6a6258;">/ 100</span></div>
        <p>${escapeHtml(result.evaluation.summary || "No summary returned.")}</p>
        <div class="meta">
          <div class="card"><strong>Mode</strong><br>${escapeHtml(result.pipeline.mode)}</div>
          <div class="card"><strong>Critic</strong><br>${result.pipeline.used_critic ? "On" : "Off"}</div>
          <div class="card"><strong>Latency</strong><br>${result.pipeline.total_duration_seconds.toFixed(2)}s</div>
          <div class="card"><strong>Pipeline Tokens</strong><br>${result.pipeline.total_tokens.total_tokens}</div>
          <div class="card"><strong>Evaluation Tokens</strong><br>${result.evaluation.token_stats.total_tokens}</div>
        </div>
        <h3>Question Scores</h3>
        ${questions}
      `;
    }

    function renderDiagram(result) {
      const codeBlock = `<pre>${escapeHtml(result.diagram_text)}</pre>`;
      const artifact = result.svg_text ? result.svg_text : codeBlock;
      diagramCanvas.innerHTML = `
        <div class="meta">
          <div class="card"><strong>Output</strong><br>${escapeHtml(result.pipeline.output_dir)}</div>
          <div class="card"><strong>Selected Diagram</strong><br>${escapeHtml(result.pipeline.selected_diagram_path || "n/a")}</div>
        </div>
        ${artifact}
      `;
    }

    runButton.addEventListener("click", async () => {
      const payload = {
        repo_path: repoPath.value.trim(),
        use_multi_agent: multiAgent.checked,
        use_critic: critic.checked,
      };
      if (!payload.repo_path) {
        statusEl.textContent = "Repository path is required.";
        return;
      }
      runButton.disabled = true;
      statusEl.textContent = "Running pipeline and evaluation. This can take a while.";
      diagramCanvas.textContent = "Running...";
      analysisCanvas.textContent = "Running...";
      try {
        const response = await fetch("/api/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const result = await response.json();
        if (!response.ok) {
          throw new Error(result.error || "Request failed");
        }
        statusEl.textContent = "Run complete.";
        renderDiagram(result);
        renderAnalysis(result);
      } catch (error) {
        statusEl.textContent = error.message;
        diagramCanvas.textContent = "Run failed.";
        analysisCanvas.textContent = "Run failed.";
      } finally {
        runButton.disabled = false;
      }
    });
  </script>
</body>
</html>"""


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(_html_page())
            return
        if parsed.path == "/artifact":
            self._serve_artifact(parsed.query)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/run":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body.decode("utf-8"))
            repo_path = str(payload["repo_path"]).strip()
            use_multi_agent = bool(payload.get("use_multi_agent", True))
            use_critic = bool(payload.get("use_critic", True))
            mode, critic_rounds = _run_mode(use_multi_agent, use_critic)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_dir = RUNS_ROOT / f"{timestamp}_{mode}"
            pipeline_result = run_pipeline_with_details(
                repo_path=repo_path,
                out_dir=run_dir,
                critic_rounds=critic_rounds,
                mode=mode,
                verbose=False,
            )

            if not pipeline_result.selected_mermaid_path:
                raise RuntimeError("No Mermaid output was generated.")

            diagram_text = pipeline_result.selected_mermaid_path.read_text(encoding="utf-8")
            evaluation_dir = pipeline_result.output_dir / "evaluation"
            evaluation_result = evaluate_diagram(
                repo_path=repo_path,
                diagram_text=diagram_text,
                llm=get_model(),
                output_dir=evaluation_dir,
            )

            svg_path = _selected_svg_path(pipeline_result.rendered_assets)
            svg_text = svg_path.read_text(encoding="utf-8") if svg_path else None
            response = {
                "pipeline": pipeline_result.to_dict(),
                "evaluation": evaluation_result.to_dict(),
                "diagram_text": diagram_text,
                "svg_text": svg_text,
            }
            self._send_json(response)
        except Exception as exc:  # pragma: no cover - runtime UI path
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send_html(self, payload: str) -> None:
        data = payload.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_artifact(self, query: str) -> None:
        params = parse_qs(query)
        raw_path = params.get("path", [None])[0]
        if not raw_path:
            self.send_error(HTTPStatus.BAD_REQUEST)
            return
        path = Path(raw_path)
        if not path.exists() or not _safe_relative_artifact(path):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        mime_type, _ = mimetypes.guess_type(path.name)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main(host: str = "127.0.0.1", port: int = 8787) -> None:
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"AAI web app listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
