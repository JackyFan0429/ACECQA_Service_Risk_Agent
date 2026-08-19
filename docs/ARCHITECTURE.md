# Architecture — v0.3

```text
                         ┌──────────────────────────────┐
                         │           User               │
                         └──────────────┬───────────────┘
                                        │ natural language
                                        v
                         ┌──────────────────────────────┐
                         │     Single LLM Agent         │
                         │  intent + tool orchestration │
                         └──────────┬───────────┬───────┘
                                    │           │
                    data question   │           │ policy question
                                    v           v
                  ┌──────────────────────┐   ┌──────────────────────┐
                  │  Analytics tools     │   │    search_policy     │
                  │  deterministic       │   │ local BM25 retrieval │
                  └──────────┬───────────┘   └──────────┬───────────┘
                             │                          │
                             v                          v
                  ┌──────────────────────┐   ┌──────────────────────┐
                  │ cleaned service data │   │ ACECQA source corpus │
                  │ 17,663 service rows  │   │ official allow-list  │
                  └──────────┬───────────┘   └──────────┬───────────┘
                             │                          │
                             └────────────┬─────────────┘
                                          v
                         ┌──────────────────────────────┐
                         │    structured tool outputs   │
                         └──────────────┬───────────────┘
                                        v
                         ┌──────────────────────────────┐
                         │ GroundedAgentAnswer          │
                         │ evidence + chunk IDs         │
                         └──────────────┬───────────────┘
                                        v
                         ┌──────────────────────────────┐
                         │ grounding validator          │
                         │ - called tool exists         │
                         │ - policy chunk was retrieved │
                         └──────────────┬───────────────┘
                                        v
                         ┌──────────────────────────────┐
                         │ AgentRunReport               │
                         │ answer + sources + trace     │
                         │ tokens + latency             │
                         └──────────────────────────────┘
```

## Design boundary

The analytics layer determines *what the data says*. The policy retrieval layer determines *what official guidance says*. The LLM performs orchestration and explanation but is not the source of truth for either layer.

For combined decision-support questions, both layers must be present in the trace.
