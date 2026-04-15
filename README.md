# Tool Retrieval Playground

This repo includes a small LangChain tool demo in `langchain_tools_demo.py`.

## What was added

- Two mocked tools implemented as Python functions with LangChain's `@tool`:
	- `mock_weather_lookup(city: str)`
	- `mock_order_status(order_id: str)`
- An Anthropic example call:
	- `anthropic_example_call(prompt: str)`
- Credentials are loaded from `.env` using `python-dotenv`.

## .env setup

Create a `.env` file with at least:

```env
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-sonnet-4-5
```

## Run the demo

```bash
python langchain_tools_demo.py
```

The script prints mocked tool outputs and attempts a real Anthropic call.

## Notebook Refactor Modules

To keep `tool_search_with_embeddings.ipynb` cleaner, reusable code has been moved into:

- `lib/tool_library.py`
	- `TOOL_LIBRARY`
	- `mock_tool_execution(...)`
- `lib/tool_search_utils.py`
	- `TOOL_SEARCH_DEFINITION`
	- `tool_to_text(...)`
	- `build_tool_embeddings(...)`
	- `search_tools(...)`
	- `handle_tool_search(...)`
- `lib/agent_utils.py`
	- `DomainAgent`
	- `build_default_agents(...)`
	- `select_agent_with_llm(...)`
	- `select_agent_with_llm_with_usage(...)`
	- `run_agent_conversation(...)`
- `lib/llm_utils.py`
	- `get_model(...)`

The notebook now imports these modules instead of redefining them inline.

### Expanded tool catalog

`TOOL_LIBRARY` now contains 18 tools total, including the original weather/finance tools plus 10 additional tools:

- `get_crypto_price`
- `get_flight_status`
- `get_hotel_availability`
- `get_restaurant_recommendations`
- `get_calorie_estimate`
- `translate_text`
- `summarize_text`
- `create_calendar_event`
- `track_package`
- `get_exchange_holidays`


Each new tool also has a corresponding mocked execution branch in `mock_tool_execution(...)`.

## OpenAI Variant

An OpenAI Responses API version of the notebook is available at:

- `tool_search_with_embeddings_openai.ipynb`

OpenAI-specific helpers are in:

- `lib/tool_search_utils_openai.py`
	- `TOOL_SEARCH_DEFINITION_OPENAI`
	- `tool_to_text_openai(...)`
	- `to_openai_function_tool_openai(...)`
	- `to_openai_tool_library_openai(...)`
	- `build_tool_embeddings_openai(...)`
	- `search_tools_openai(...)`
	- `handle_tool_search_openai(...)`
	- `build_deferred_tools_with_namespaces_openai(...)`
	- `build_namespaced_tools_by_category_openai(...)`

The hosted tool-search flow in `tool_search_with_embeddings_openai.ipynb` now reuses
`build_namespaced_tools_by_category_openai(...)` and chains calls with
`previous_response_id`, which avoids replaying non-input response fields
like `created_by`.

The OpenAI notebook also includes a third comparison example where all tools are
passed up front with no deferral, so token usage can be compared across:
client-side search, hosted deferred search, and full upfront tool loading.

## Natural Language Tools Variant

An NLT-style Anthropic notebook is available at:

- `tool_search_with_natural_language.ipynb`

This notebook follows a natural-language selection flow inspired by Natural
Language Tools (selector -> parser -> execution), while still executing the
same tool catalog from `lib/tool_library.py`.

NLT helpers live in:

- `lib/natural_utils.py`
	- `build_nlt_tool_catalog(...)`
	- `build_selector_prompt(...)`
	- `run_nlt_selector(...)`
	- `parse_selector_yes_no(...)`
	- `validate_and_coerce_parameters(...)`
	- `run_nlt_workflow(...)`

By default, the NLT flow runs on the full tool catalog. The notebook also keeps
embedding-based prefiltering as an optional toggle for larger catalogs.

## Anthropic Comparison Experiments

The Anthropic notebook at `tool_search_with_embeddings.ipynb` now includes a
three-way experiment runner with token tracking and graphing for two prompts
(weather and finance):

- No search (full toolset bound upfront)
- Minimal bind (exactly 2 tools: weather + compound interest)
- Tool search (start with `tool_search`, load tools on demand)

The notebook prints per-run metrics (input/output/total tokens, tool call
counts) and renders a grouped bar chart for total token usage by query type.

The examples section now also tracks total tokens per example query run and
renders a summary bar chart at the end of the notebook under
"Token Usage by Example":

- Example 1: Tool search flow
- Example 1B: Single needed tool (Anthropic SDK directly, no LangChain)
- Example 1C: Full tool library bound up front
- Example 2: Finance query
- Example 4: Router -> Domain Agent (weather query), with total tokens tracked
	as router call + selected-agent run

In `run_tool_search_conversation(...)`, the model starts with only
`tool_search`, then subsequent turns are constrained to only the discovered
or executed tools to keep tool scope minimal.

## Multi-Agent Router Example (Anthropic Notebook)

`tool_search_with_embeddings.ipynb` now includes an additional bottom example
that routes a user task through an LLM router before execution:

- Router chooses one domain agent:
	- `Travel & Lifestyle`
	- `Finance & Markets`
- The selected agent runs with pre-bound domain mock tools via Anthropic
	`beta_tool` and `client.beta.messages.tool_runner`.
- No `tool_search` call is needed in this routed path, and Example 3 does not
	need `TOOL_LIBRARY` or `TOOL_SEARCH_DEFINITION` inputs.
- Token usage from this routed run is stored in `example_token_usage` like the
  other examples.

The shared logic for this flow lives in `lib/agent_utils.py`, keeping notebook
cells focused on demo usage.

## ToolDreamer Notebook

A ToolDreamer-style notebook is available at:

- `tool_dreamer.ipynb`

This notebook follows a hypothetical-tool workflow inspired by the ToolDreamer
paper:

- Generate dreamed (hypothetical) tools from a query
- Use each dreamed tool as a retrieval anchor (QTND-style text)
- Rank actual tools from `lib/tool_library.py`
- Fuse per-anchor ranked lists with Reciprocal Rank Fusion (RRF)

The notebook includes built-in examples for:

- A weather query
- A finance query

Prompt template used for dreamed tool generation:

- `tooldreamer_prompt.md`

If `ANTHROPIC_API_KEY` is available in `.env`, the notebook uses live LLM
generation. Otherwise it falls back to deterministic dreamed tools so the
ranking flow still runs end to end.
