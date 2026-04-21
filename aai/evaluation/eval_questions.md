# Core Evaluation Questions

These are the fixed cross-repository evaluation questions.
They are intentionally architecture-level so that a good high-level diagram
can answer them without requiring line-level code recall.

1. What is the overall purpose of the repository?
2. What are the main top-level subsystems or modules in this repository?
3. What are the primary runtime boundaries or execution environments represented in this system?
4. What external systems, APIs, or devices does this repository integrate with?
5. What persistent stores, streams, queues, or other major data-holding components exist in the system?
6. What are the main data or control flows between the major subsystems?
7. Which parts of the system appear to act as entrypoints, orchestrators, or coordinators?

## Repo-Specific Question Generation Guidelines

For each repository, the evaluation pipeline should generate a separate
`repo_specific_eval_questions.md` file automatically based on the scanned repo.

Target count:
- Generate 5 to 10 repo-specific questions.

Good repo-specific questions:
- test repository-specific runtime boundaries, deployment targets, or execution modes
- ask about major external integrations, data producers/consumers, or infrastructure touchpoints
- probe the most important subsystem-specific flows in the repo
- cover important artifacts such as training pipelines, batch jobs, local runtimes, message flows, or serving layers when present
- focus on architecture-level understanding rather than syntax trivia
- stay answerable from a good high-level architecture diagram, not only from low-level code details

Avoid questions that:
- duplicate the fixed core questions above
- depend on tiny implementation details, constants, or exact line-level recall
- are pure yes/no questions unless they check a meaningful architectural property
- are likely to be unanswerable even with a good repository scan
- require knowledge outside the repository evidence
- require detailed function-level reasoning that a high-level diagram is not expected to capture

Examples of acceptable repo-specific themes:
- platform-specific code paths
- model training or model serving flows
- environment-specific deployment pieces
- domain-specific data origins and destinations
- key orchestration or coordination components
