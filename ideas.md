- Dump the initial (or intermediate) architecture diagrams before the critic revision
    to see how they change based on the feedback

- How to evaluate? 
    Complex LLMs as judges
    - give mermaid diagram to an LLM as a judge. And then ask the LLM questions about the codebase. See how many get answered correctly
        - Analogous to "understanding the codebase" as a new employee getting onboarded
    - compare with existing repos which have mermaid diagrams

- LangGraph / CrewAI
    - LangGraph could be a nice grounds up approach
    - What about forking something like SWE-agent and going from there?

- Prompt vs Agent? - whichever works better
    - Prompt : Like a template which is filled and sent to an LLM
    - Agent : Like a loop - high level goal, fill in context, and it figures out its done