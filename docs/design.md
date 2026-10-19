# Design and trade-offs

## Why local inference

The data is HR records. Sending it to a hosted API is a non-starter for most companies. Running the model in-house keeps it on the machine. The cost is weaker models and slower answers.

## Why RAG instead of fine-tuning

Policies change. Re-training a model for every policy update is expensive and slow. Storing policies in ChromaDB and retrieving the relevant one at query time means an update is a CSV edit and a re-index.

## Why tool calling instead of free-form SQL

The model never writes SQL. It picks a function with typed arguments. That removes a class of injection and hallucination risks. The downside is that every new action needs a new function and schema.

## Trade-offs accepted

- Single-turn context. Multi-turn memory would need a session store; skipped to keep scope small.
- No authentication. The API assumes a trusted network. Add auth before any real deployment.
- SQLite. Fine for a demo and a few hundred employees. Move to Postgres at scale.
- Local model quality. The eval harness exists to measure it. Current score: 9/9 tool selection, 9/9 answer match on the golden set.

## What I would do next

- Hybrid search (BM25 + vector) and a reranker.
- Prompt-injection tests and a read-only database role.
- A real load test with 1000+ synthetic employees.