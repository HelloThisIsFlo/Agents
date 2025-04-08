# Agents

This repo is a place to build and experiment with agents.

## How to run?

1. Install `uv`, see [official repo](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)
1. Run `uv sync`
1. Create a `.env` file in the root directory and add the following:
   ```bash
   # Required
   OPENAI_API_KEY=...

   # Optional
   TAVILY_API_KEY=...
   EXA_API_KEY=...

   # Optional - Agno Debug
   AGNO_DEBUG=false # Set to 'true' for debug output

   # Optional - Agno Tracing
   AGNO_API_KEY=...
   AGNO_MONITOR=true
   ```
1. Run each example, they are self-contained