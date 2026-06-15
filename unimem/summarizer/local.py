"""Local heuristic summarizer that parses event logs without relying on external LLM calls."""

import re
from typing import List, Set
from unimem.summarizer.base import BaseSummarizer
from unimem.memory.schemas import ProjectState, Event, FileOperation
from unimem.utils.logger import logger

class LocalSummarizer(BaseSummarizer):
    """Local, rule-based summarizer analyzing event structures and logs to compile ProjectState."""

    def summarize(self, current_state: ProjectState, events: List[Event]) -> ProjectState:
        """Run heuristic parsing on events list to update the ProjectState."""
        logger.debug(f"Running local summarizer on {len(events)} events.")
        
        # Clone lists to avoid direct mutation issues
        completed = list(current_state.completed_features)
        in_progress = list(current_state.in_progress_features)
        important_files = set(current_state.important_files)
        decisions = list(current_state.recent_decisions)
        blocked_by = list(current_state.blocked_by)
        tools = set(current_state.tool_history)
        
        # Heuristics patterns
        feat_pattern = re.compile(r"(?:complete|finish|implement|add|create|setup)\s+([\w\s\-]{3,40})", re.IGNORECASE)
        ip_pattern = re.compile(r"(?:work\s+on|building|implementing|developing|fixing)\s+([\w\s\-]{3,40})", re.IGNORECASE)
        decision_pattern = re.compile(r"(?:decided\s+to|decision:)\s+([\w\s\-]{3,60})", re.IGNORECASE)
        blocker_pattern = re.compile(r"(?:blocked\s+by|waiting\s+for|error:)\s+([\w\s\-]{3,60})", re.IGNORECASE)
        
        for event in events:
            # 1. Update Tool History
            if event.tool and event.tool != "watcher":
                tools.add(event.tool)
                
            # 2. Update Important Files
            for f in event.files_changed:
                if f and not f.startswith(".") and not f.startswith("tests"):
                    important_files.add(f)
                    
            # 3. Analyze Event Type and Summaries
            text_to_scan = f"{event.prompt} {event.response_summary}"
            
            # Git commit messages often tell us about completed features
            if event.event_type == "git_commit" or event.git_commit:
                text_to_scan += f" {event.response_summary}"
                
            # Parse completed features
            for match in feat_pattern.finditer(text_to_scan):
                feature = match.group(1).strip()
                if feature and feature not in completed:
                    # Clean feature name
                    feature = feature.capitalize()
                    completed.append(feature)
                    # If it was in progress, remove it
                    if feature in in_progress:
                        in_progress.remove(feature)
                        
            # Parse in progress features
            for match in ip_pattern.finditer(text_to_scan):
                feature = match.group(1).strip().capitalize()
                if feature and feature not in completed and feature not in in_progress:
                    in_progress.append(feature)
                    
            # Parse decisions
            for match in decision_pattern.finditer(text_to_scan):
                dec = f"{match.group(1).strip().capitalize()} ({event.timestamp[:10]})"
                if dec not in decisions:
                    decisions.append(dec)
                    
            # Parse blockers
            for match in blocker_pattern.finditer(text_to_scan):
                blocker = match.group(1).strip().capitalize()
                if blocker and blocker not in blocked_by:
                    blocked_by.append(blocker)

        # Update lists back into state
        current_state.completed_features = completed
        current_state.in_progress_features = in_progress
        current_state.important_files = sorted(list(important_files))[:20] # Cap at 20 important files
        current_state.recent_decisions = decisions[-10:] # Keep latest 10
        current_state.blocked_by = blocked_by[-5:] # Keep latest 5
        current_state.tool_history = sorted(list(tools))
        
        # Task promotion logic
        if current_state.current_task:
            task_lower = current_state.current_task.lower()
            # Standard promotion: current_task appears in completed features
            promoted = any(task_lower in feat.lower() for feat in completed)
            # Orphan-recovery promotion: current_task appears in in_progress_features
            # and there were file changes, indicating work was done but session was lost
            if not promoted and in_progress and any(
                task_lower in feat.lower() for feat in in_progress
            ) and bool(important_files):
                promoted = True
            if promoted:
                current_state.current_task = current_state.next_task
                current_state.next_task = ""

        # Update file history from events using delta tracking (latest op per path)
        file_history_map = {}
        for event in events:
            task_str = getattr(event, "task", "")
            
            def add_or_update_op(path: str, op_type: str):
                file_history_map[path] = FileOperation(
                    file_path=path,
                    operation_type=op_type,
                    timestamp=event.timestamp,
                    task=task_str
                )

            if event.event_type == "file_created":
                for f in event.files_changed:
                    add_or_update_op(f, "created")
            elif event.event_type == "file_modified":
                for f in event.files_changed:
                    add_or_update_op(f, "modified")
            elif event.event_type == "file_deleted":
                for f in event.files_changed:
                    add_or_update_op(f, "deleted")
            elif event.event_type == "file_moved":
                if len(event.files_changed) >= 2:
                    add_or_update_op(event.files_changed[0], "deleted")
                    add_or_update_op(event.files_changed[1], "created")
                elif len(event.files_changed) == 1:
                    add_or_update_op(event.files_changed[0], "modified")
            elif event.files_changed and event.event_type not in ["session_start", "session_end"]:
                for f in event.files_changed:
                    add_or_update_op(f, "modified")

        current_state.file_history = list(file_history_map.values())

        return current_state
