# Agentic Architectural Inference

A multi-agent system for generating accurate high-level software architecture diagrams from source code using hypothesis-falsification reasoning with a dedicated Critic agent.

## Authors

- Rutuja Nikumb (RutujaRavindra.Nikumb@colorado.edu)
- Manikandan Gunaseelan (Manikandan.Gunaseelan@colorado.edu)
- Kevin Jones (Kevin.Jones-1@colorado.edu)
- Ishika Patel (ishika.patel@colorado.edu)

University of Colorado Boulder  
CSCI 7000: Building Agents (Spring 2026)

## Overview

This project addresses the challenge of generating and maintaining accurate architectural diagrams for complex software systems. Rather than treating architecture generation as a single synthesis task, we propose an iterative, multi-agent approach that frames it as a hypothesis-falsification process.

### Key Innovation

We introduce a dedicated **Critic Agent** whose explicit role is to challenge, validate, and refine synthesized architectures by:
- Searching for counter-evidence in code
- Flagging low-confidence edges and components
- Requesting re-analysis of ambiguous regions
- Enabling iterative refinement of the diagram

## Research Questions

1. **RQ1:** Can multi-agent systems generate accurate high-level architecture diagrams of complex code systems better than single-shot LLM prompts?
2. **RQ2:** Will feedback units (critic agents, human-in-the-loop) improve diagram accuracy?
3. **RQ3:** How do feedback steps impact architecture generation latency?

## Technical Challenges

- **Abstraction & Composition:** Scaling from low-level code units (functions, classes) to system-level components (modules, services)
- **Intent Inference:** Capturing architectural "why" rather than just "what" from code
- **Context Constraints:** Managing LLM context windows for large repositories
- **Evaluation:** Defining fair accuracy metrics without reliable ground-truth diagrams

## Approach

### Multi-Agent Pipeline

1. **File Summarizer Agent** — Hierarchical code summarization producing repository-level functional overview
2. **Context Manager** — Partitions codebase into coherent subsystems respecting context limits
3. **Architect Agent** — Generates structured component summaries and proposes initial system diagrams
4. **Critic Agent** — Validates components and connections, searches for counter-evidence, requests refinement

### Output

Graph-based system diagrams depicting:
- **Nodes:** Components/services/modules
- **Edges:** Calls, dependencies, data-flow
- **Evidence:** Import traces, call paths, folder structure

## Evaluation Methodology

- Technical experiments with small and large codebases
- Reference diagrams from established repositories
- LLM-based evaluation using established clarity and correctness criteria
- Comparison against fine-grained generated models (e.g., CLANG-UML)

## Related Work

This project builds upon recent advances in:
- **NOMAD:** Multi-agent UML class diagram generation from natural language
- **Hatahet et al.:** Reverse engineering + LLM approach for architecture descriptions
- **ArchAgent:** Scalable legacy software architecture recovery with adaptive segmentation
- **VisDocSketcher:** Agentic visual documentation generation with quality evaluation

Our work advances these approaches by explicitly modeling architecture generation as an iterative reasoning process with dedicated validation and falsification steps.

## Project Status

- Multi-agent system implementation: In Progress
    - TODO Impliment with C4 diagram
    - TODO impliment with mermaid diagram
- Empirical evaluation: Planned
- Results and conclusions: Planned

## Keywords

Architecture diagrams, LLM agents, Multi-agent systems, Software reverse engineering, Hypothesis falsification

