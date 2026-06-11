# Unimem Agent Instructions

Unimem is active in this project. You are resuming work from a previous session.

CRITICAL STARTUP RULE:
Do NOT scan, list, or search the entire project repository or folder tree on startup. This wastes token context and is inefficient. Instead, follow these steps immediately:
1. Run `unimem summary` to compile all recent events and file modifications into the memory layer.
2. Read the structured project state at `.unimem/state.json` first to get the exact roadmap, goals, tasks, and file listings.
3. Read the human-readable project memory at `.unimem/memory.md` next to get the narrative context, recent decisions, and details.
4. Trust `.unimem/state.json` and `.unimem/memory.md` as the absolute sources of truth for the project state. Do NOT attempt to reconstruct them or scan the repository.

- When you finish or pause work:
- Always edit and update `.unimem/state.json` first to document completed features, goals, or tasks.
- Next, run `unimem summary` in the terminal to compile and synchronize these changes into `.unimem/memory.md` and update agent rules files so the next agent can take over with full context.
- When you complete the current task, run: unimem task done --next "describe the next task"
- If you are interrupted or about to stop, always run: unimem task done --next "describe next task" before exiting so context is preserved for the next agent.
