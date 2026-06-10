# Unimem Internal Design Specification

This document provides a technical deep-dive into the architectural decisions and internal design of the Unimem Universal Memory Layer.

---

## 1. Domain Modeling

Unimem is divided into distinct, decoupled domains following Clean Architecture principles:

- **Storage Layer**: Raw reads and writes of file text and JSON models to disk.
- **Memory Layer**: Dictates schemas (State, Event, Session), schema migrations, manager initialization, and snapshots.
- **Collector Layer**: Integration modules that query external states (Git repository status, filesystem properties).
- **Summarization Engine**: Decodes raw event logs chronologically to extract high-level goal, task, completed features, and blocker states.
- **Watcher Service**: An active event loop running watchdog to map file creation/modification notifications directly into local events.
- **Adapter Layer**: Bridge classes matching specific AI agent shells (Claude, Gemini, Codex) with Unimem environmental states.
- **CLI Shell**: User-facing CLI application designed using Typer and styled with Rich.

---

## 2. Event Lifecycle

```text
               +----------------------+
               |  Filesystem Watcher  |
               +----------+-----------+
                          | (File changes)
                          v
+-------------+    +------+-------+    +-------------------+
|  AI Agent   |--->| MemoryManager |--->| .unimem/events/   |
| (Launch/Run)|    +------+-------+    +---------+---------+
+-------------+           |                      |
                          v                      | (Trigger compilation)
                   +------+-------+              v
                   | state.json   |<---+-------------------+
                   | memory.md    |    | LocalSummarizer   |
                   +--------------+    +-------------------+
```

---

## 3. Schema Migrations

As Unimem evolves and new fields are added to `ProjectState`, compatibility is maintained via `unimem/memory/migrations.py`. Whenever `state.json` is loaded, it is run through the migration pipeline which identifies missing keys, inserts default values, and writes the updated schema back to disk.

---

## 4. Local Summarization Heuristics

The `LocalSummarizer` runs on regex matches on recent event logs:
- `Completed Features`: Extracted from git commits or events indicating keywords like `complete`, `finish`, `implement`, `add`, `setup`.
- `In Progress Features`: Extracted from edit activities like `work on`, `building`, `fixing`, `developing`.
- `Architecture & Decisions`: Captured from specific `unimem decision` command logs.
- `Blockers`: Extracted from words like `blocked by`, `waiting for`, `error:`.
