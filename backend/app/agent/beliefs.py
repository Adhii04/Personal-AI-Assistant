# app/agent/beliefs.py
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime, date

@dataclass
class TimeConstraint:
    """A constraint on when events can be scheduled"""
    type: str  # "preference" | "hard_constraint" | "availability"
    scope: str  # "global" | "date_specific"
    scope_date: Optional[date]
    rule: str  # "after", "before", "not_after", "not_before"
    time: str  # "18:00"
    original_text: str
    priority: int  # hard_constraint=100, date_specific=50, global=10
    
    def applies_to(self, target_date: date) -> bool:
        """Check if this constraint applies to a given date"""
        if self.scope == "global":
            return True
        if self.scope == "date_specific":
            return self.scope_date == target_date
        return False
    
    def conflicts_with(self, other: 'TimeConstraint', target_date: date) -> bool:
        """Check if two constraints conflict for a date"""
        if not (self.applies_to(target_date) and other.applies_to(target_date)):
            return False
        
        # Example: "after 6pm" + "not after 2pm" = conflict
        if self.rule == "after" and other.rule == "not_after":
            return self.time >= other.time
        if self.rule == "not_after" and other.rule == "after":
            return other.time >= self.time
        
        return False

@dataclass
class BeliefState:
    """The agent's understanding of user preferences and constraints"""
    constraints: List[TimeConstraint]
    
    def get_active_constraints(self, target_date: date) -> List[TimeConstraint]:
        """Get all constraints that apply to a specific date, sorted by priority"""
        active = [c for c in self.constraints if c.applies_to(target_date)]
        return sorted(active, key=lambda c: c.priority, reverse=True)
    
    def detect_conflicts(self, target_date: date) -> List[tuple[TimeConstraint, TimeConstraint]]:
        """Find all conflicting constraints for a date"""
        active = self.get_active_constraints(target_date)
        conflicts = []
        for i, c1 in enumerate(active):
            for c2 in active[i+1:]:
                if c1.conflicts_with(c2, target_date):
                    conflicts.append((c1, c2))
        return conflicts
    
    def propose_time(self, target_date: date) -> Optional[str]:
        """Propose a time that satisfies all constraints, or None if impossible"""
        constraints = self.get_active_constraints(target_date)
        
        if not constraints:
            return None  # No preference, ask user
        
        # Check for conflicts first
        conflicts = self.detect_conflicts(target_date)
        if conflicts:
            return None  # Can't resolve, need clarification
        
        # Apply constraints in priority order
        proposed_time = None
        for c in constraints:
            if c.rule == "after":
                proposed_time = c.time
            elif c.rule == "not_after":
                # Schedule 1 hour before the limit
                hour = int(c.time.split(':')[0])
                proposed_time = f"{max(9, hour-1):02d}:00"
        
        return proposed_time