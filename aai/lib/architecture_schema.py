"""Canonical architecture schema and deterministic Mermaid rendering."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

CATEGORY_ORDER = [
    "Frontend",
    "Backend",
    "Data",
    "External",
    "Infrastructure",
    "Operations",
    "Workspace",
]

ALLOWED_KINDS = {
    "ui",
    "client",
    "api",
    "service",
    "worker",
    "job",
    "data",
    "database",
    "cache",
    "queue",
    "stream",
    "storage",
    "model",
    "external",
    "external_api",
    "device",
    "infrastructure",
    "deployment",
    "config",
}

KIND_TO_CATEGORY = {
    "ui": "Frontend",
    "client": "Frontend",
    "api": "Backend",
    "service": "Backend",
    "worker": "Backend",
    "job": "Operations",
    "data": "Data",
    "database": "Data",
    "cache": "Data",
    "queue": "Data",
    "stream": "Data",
    "storage": "Data",
    "model": "Backend",
    "external": "External",
    "external_api": "External",
    "device": "External",
    "infrastructure": "Infrastructure",
    "deployment": "Infrastructure",
    "config": "Infrastructure",
}

LEGACY_BOUNDARY_TO_CATEGORY = {
    "Client": "Frontend",
    "API": "Backend",
    "Services": "Backend",
    "Data": "Data",
    "External": "External",
    "Infrastructure": "Infrastructure",
}

RELATION_ALIASES = {
    "calls": "calls",
    "uses": "calls",
    "invokes": "calls",
    "requests": "calls",
    "authenticates with": "authenticates with",
    "reads from": "reads from",
    "loads from": "reads from",
    "fetches from": "reads from",
    "writes to": "writes to",
    "stores in": "writes to",
    "persists to": "writes to",
    "publishes to": "publishes to",
    "sends to": "publishes to",
    "emits to": "publishes to",
    "consumes from": "consumes from",
    "subscribes to": "consumes from",
    "receives from": "consumes from",
    "streams to": "streams to",
    "ingests from": "ingests from",
    "depends on": "depends on",
    "connects to": "depends on",
}

CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}


@dataclass
class CanonicalComponent:
    id: str
    label: str
    kind: str
    category: str
    module: str
    description: str
    confidence: str
    evidence: list[str]


@dataclass
class CanonicalEdge:
    source: str
    target: str
    relation: str
    confidence: str
    evidence: list[str]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "component"


def _clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _clean_evidence(values: object) -> list[str]:
    if isinstance(values, list):
        cleaned = [_clean_text(item) for item in values]
    elif values:
        cleaned = [_clean_text(values)]
    else:
        cleaned = []
    return [item for item in cleaned if item]


def _normalize_kind(value: object) -> str:
    kind = _slugify(_clean_text(value)).replace("_", "")
    if kind in {"datasource", "dataset"}:
        kind = "data"
    if kind == "backend":
        kind = "service"
    if kind == "db":
        kind = "database"
    if kind == "mq":
        kind = "queue"
    return kind if kind in ALLOWED_KINDS else "service"


def _normalize_category(value: object, kind: str) -> str:
    cleaned = _clean_text(value)
    if cleaned in CATEGORY_ORDER:
        return cleaned
    if cleaned in LEGACY_BOUNDARY_TO_CATEGORY:
        return LEGACY_BOUNDARY_TO_CATEGORY[cleaned]
    return KIND_TO_CATEGORY.get(kind, "Backend")


def _normalize_module(value: object) -> str:
    cleaned = _clean_text(value)
    return cleaned or "General"


def _normalize_relation(value: object) -> str:
    relation = _clean_text(value).lower()
    return RELATION_ALIASES.get(relation, relation or "depends on")


def _normalize_confidence(value: object) -> str:
    confidence = _clean_text(value).lower()
    return confidence if confidence in CONFIDENCE_ORDER else "medium"


def _highest_confidence(left: str, right: str) -> str:
    return left if CONFIDENCE_ORDER[left] >= CONFIDENCE_ORDER[right] else right


def extract_architecture_payload(text: str) -> dict:
    """Extract the architecture JSON object from an LLM response."""
    fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced_match:
        return json.loads(fenced_match.group(1))

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        return json.loads(brace_match.group(0))

    raise RuntimeError("Architect response did not contain a valid architecture JSON object.")


def canonicalize_architecture(payload: dict) -> dict:
    """Normalize an architecture payload into a stable component/edge graph."""
    raw_components = payload.get("components", [])
    raw_edges = payload.get("edges", [])

    if not isinstance(raw_components, list) or not raw_components:
        raise RuntimeError("Architecture payload did not contain any components.")

    components_by_id: dict[str, CanonicalComponent] = {}
    alias_to_id: dict[str, str] = {}

    for raw_component in raw_components:
        if not isinstance(raw_component, dict):
            continue

        label = _clean_text(raw_component.get("label") or raw_component.get("name"))
        if not label:
            continue

        kind = _normalize_kind(raw_component.get("kind"))
        component_id = _slugify(raw_component.get("id") or label)
        category = _normalize_category(
            raw_component.get("category") or raw_component.get("boundary"),
            kind,
        )
        module = _normalize_module(raw_component.get("module"))
        description = _clean_text(raw_component.get("description"))
        confidence = _normalize_confidence(raw_component.get("confidence"))
        evidence = _clean_evidence(raw_component.get("evidence"))

        existing = components_by_id.get(component_id)
        if existing:
            if len(label) > len(existing.label):
                existing.label = label
            if description and not existing.description:
                existing.description = description
            existing.evidence = sorted(set(existing.evidence + evidence))
            existing.category = category
            existing.module = module
            existing.kind = kind
            existing.confidence = _highest_confidence(existing.confidence, confidence)
            component = existing
        else:
            component = CanonicalComponent(
                id=component_id,
                label=label,
                kind=kind,
                category=category,
                module=module,
                description=description,
                confidence=confidence,
                evidence=sorted(set(evidence)),
            )
            components_by_id[component_id] = component

        alias_to_id[_slugify(label)] = component.id
        alias_to_id[_slugify(component_id)] = component.id

    if not components_by_id:
        raise RuntimeError("Architecture payload did not contain any usable components.")

    edges_by_key: dict[tuple[str, str, str], CanonicalEdge] = {}
    for raw_edge in raw_edges:
        if not isinstance(raw_edge, dict):
            continue

        raw_source = _clean_text(raw_edge.get("source"))
        raw_target = _clean_text(raw_edge.get("target"))
        if not raw_source or not raw_target:
            continue

        source = alias_to_id.get(_slugify(raw_source))
        target = alias_to_id.get(_slugify(raw_target))
        if not source or not target or source == target:
            continue

        relation = _normalize_relation(raw_edge.get("relation") or raw_edge.get("label"))
        confidence = _normalize_confidence(raw_edge.get("confidence"))
        evidence = _clean_evidence(raw_edge.get("evidence"))
        key = (source, target, relation)

        existing_edge = edges_by_key.get(key)
        if existing_edge:
            existing_edge.confidence = _highest_confidence(existing_edge.confidence, confidence)
            existing_edge.evidence = sorted(set(existing_edge.evidence + evidence))
            continue

        edges_by_key[key] = CanonicalEdge(
            source=source,
            target=target,
            relation=relation,
            confidence=confidence,
            evidence=sorted(set(evidence)),
        )

    components = sorted(
        components_by_id.values(),
        key=lambda item: (
            CATEGORY_ORDER.index(item.category),
            item.module.lower(),
            item.label.lower(),
            item.id,
        ),
    )
    edges = sorted(
        edges_by_key.values(),
        key=lambda item: (item.source, item.target, item.relation),
    )

    return {
        "title": _clean_text(payload.get("title")) or "Standardized Architecture",
        "direction": "LR",
        "categories": CATEGORY_ORDER,
        "components": [
            {
                "id": component.id,
                "label": component.label,
                "kind": component.kind,
                "category": component.category,
                "module": component.module,
                "description": component.description,
                "confidence": component.confidence,
                "evidence": component.evidence,
            }
            for component in components
        ],
        "edges": [
            {
                "source": edge.source,
                "target": edge.target,
                "relation": edge.relation,
                "confidence": edge.confidence,
                "evidence": edge.evidence,
            }
            for edge in edges
        ],
    }


def render_mermaid_from_architecture(payload: dict) -> str:
    """Render a canonical architecture payload as Mermaid."""
    grouped_components: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for component in payload["components"]:
        grouped_components[component["category"]][component["module"]].append(component)

    lines = ["flowchart LR"]
    for category in CATEGORY_ORDER:
        modules = grouped_components.get(category, {})
        if not modules:
            continue
        category_id = _slugify(category)
        lines.append(f"    subgraph {category_id}[{category}]")
        for module_name in sorted(modules):
            module_id = f"{category_id}_{_slugify(module_name)}"
            lines.append(f"        subgraph {module_id}[{module_name}]")
            for component in sorted(modules[module_name], key=lambda item: item["label"].lower()):
                lines.append(f'            {component["id"]}["{component["label"]}"]')
            lines.append("        end")
        lines.append("    end")

    if payload["edges"]:
        lines.append("")
    for edge in payload["edges"]:
        lines.append(
            f'    {edge["source"]} -->|{edge["relation"]}| {edge["target"]}'
        )
    return "\n".join(lines)


def render_architecture_markdown(payload: dict) -> str:
    """Render canonical architecture metadata plus Mermaid into markdown."""
    mermaid = render_mermaid_from_architecture(payload)
    component_count = len(payload["components"])
    edge_count = len(payload["edges"])
    return (
        "# Standardized Architecture Diagram\n\n"
        f"- Title: {payload['title']}\n"
        f"- Components: {component_count}\n"
        f"- Edges: {edge_count}\n"
        f"- Categories: {', '.join(CATEGORY_ORDER)}\n\n"
        "```mermaid\n"
        f"{mermaid}\n"
        "```\n"
    )


def save_architecture_json(path: str | Path, payload: dict) -> None:
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
