# Staged Adoption Matrix
| Technology | Status | Trigger Condition | Fallback |
|---|---|---|---|
| Temporal | STAGED | p95 latency > 30s AND runs > 10k/mo | LangGraph in-process |
| Graphiti | STAGED | first "was this true at time T" query | lightrag-hku |
| Reranker | STAGED | retrieval recall < 0.7 in eval | Native vector search |
| Self-hosted Langfuse | STAGED | first paid customer | Managed Langfuse |
| Live SSO/SCIM | STAGED | first design-partner onboarding | Fixed test identity |
| Legacy adapters | STAGED | customer requests Selenium/Appium | fake adapter |
| Promptfoo post-acq | TRACKED | acquisition closes | portable scenario set |
