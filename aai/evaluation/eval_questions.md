# Core Evaluation Questions

These are the fixed cross-repository evaluation questions.

1. What is the overall purpose of the repository?
2. What is the entry point for this repository?
3. What is the execution flow?
4. What data sources and sinks exist in this program?
5. Based on the complexity of the functions and the number of dependencies, which parts of this codebase are likely the most fragile or difficult to test?
6. What architectural design patterns are most prevalent in this project?
7. Is there an independently deployable backend service in this project?

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

Avoid questions that:
- duplicate the fixed core questions above
- depend on tiny implementation details, constants, or exact line-level recall
- are pure yes/no questions unless they check a meaningful architectural property
- are likely to be unanswerable even with a good repository scan
- require knowledge outside the repository evidence

Examples of acceptable repo-specific themes:
- platform-specific code paths
- model training or model serving flows
- environment-specific deployment pieces
- domain-specific data origins and destinations
- key orchestration or coordination components
