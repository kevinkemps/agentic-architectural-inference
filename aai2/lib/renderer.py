"""Stage 6 – Mermaid diagram rendering helpers.

Requires the ``mmdc`` package:
    pip install mmdc
"""

from __future__ import annotations

import re
from pathlib import Path


def extract_mermaid(md_content: str) -> str:
    """Strip markdown fences and return raw Mermaid syntax.

    If no fenced block is found the entire content is returned stripped.
    """
    match = re.search(r"```mermaid\s*(.*?)```", md_content, re.DOTALL)
    return match.group(1).strip() if match else md_content.strip()


def render_to_png(md_path: str | Path, out_png: str | Path) -> Path:
    """Read a Mermaid ``.md`` file and save it as a PNG using ``mermaid-py``.

    Parameters
    ----------
    md_path:
        Path to a Markdown file containing a ``\`\`\`mermaid`` fenced block.
    out_png:
        Destination path for the rendered PNG image.

    Returns
    -------
    Path
        The resolved path of the written PNG file.
    """
    from mmdc import MermaidConverter  # type: ignore[import]

    content = Path(md_path).read_text(encoding="utf-8")
    mermaid_src = extract_mermaid(content)
    print(f"  extracted mermaid ({len(mermaid_src)} chars)")
    out_png = Path(out_png)
    converter = MermaidConverter()
    converter.to_png(mermaid_src, str(out_png))
    print(f"✅ Saved: {out_png}")
    return out_png


def render_stage_diagrams(output_dir: Path, stages: list[str], visual_stage: str) -> None:
    """Render draft and refined Mermaid diagrams to PNG.

    Looks for ``mermaid.md`` in ``stages[2]`` (03_draft) and ``stages[4]``
    (05_refined) and writes PNGs to ``output_dir / visual_stage /``.

    Parameters
    ----------
    output_dir:
        Root output directory (e.g. ``Path("output_analysis")``).
    stages:
        The ordered list of stage directory names (must have at least 6 entries).
    visual_stage:
        The name of the visual output stage directory (e.g. ``"06_visual"``).
    """
    visual_dir = output_dir / visual_stage
    visual_dir.mkdir(parents=True, exist_ok=True)

    for stage_idx, label in [(2, "draft"), (4, "refined")]:
        src = output_dir / stages[stage_idx] / "mermaid.md"
        if src.exists():
            render_to_png(src, visual_dir / f"mermaid_{label}.png")
        else:
            print(f"⚠️  Not found: {src}")
