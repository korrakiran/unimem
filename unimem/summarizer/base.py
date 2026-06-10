"""Abstract base class for all summarization engines."""

from abc import ABC, abstractmethod
from typing import List
from unimem.memory.schemas import ProjectState, Event

class BaseSummarizer(ABC):
    """Abstract class for converting event stream logs into high-level project status."""

    @abstractmethod
    def summarize(self, current_state: ProjectState, events: List[Event]) -> ProjectState:
        """Process events and update the project state summary.
        
        Args:
            current_state: The current ProjectState object.
            events: A list of Event objects since last update.
            
        Returns:
            ProjectState: The updated ProjectState object.
        """
        pass
