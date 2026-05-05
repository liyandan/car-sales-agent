# API Structure

`api` is organized into three layers:

- `models`: LLM initialization and primary/backup model routing configuration.
- `routers`: external service routes (FastAPI endpoints).
- `services`: theme/domain service implementations used by routers.
