from typing import Optional, List
from dataclasses import dataclass
from datetime import date
import re


@dataclass
class TimeConstraint:
    """A structured belief about when meetings can/should be scheduled"""
    
    type: str  # "preference" | "hard_constraint"
    scope: str  # "global" | "date_specific"
    scope_date: Optional[date]
    rule: str  # "after", "before", "not_after", "not_before"
    time: str  # "18:00" (24-hour format)
    original_text: str
    priority: int  # Higher = more important
    
    def applies_to(self, target_date: date) -> bool:
        """Check if this constraint applies to a given date"""
        if self.scope == "global":
            return True
        if self.scope == "date_specific":
            return self.scope_date == target_date
        return False
    
    def conflicts_with(self, other: 'TimeConstraint', target_date: date) -> bool:
        """
        Check if two constraints conflict for a specific date.
        
        Examples of conflicts:
        - "after 6pm" + "not after 2pm" = conflict
        - "after 6pm" + "not after 11pm" = no conflict (6pm < 11pm)
        """
        if not (self.applies_to(target_date) and other.applies_to(target_date)):
            return False
        
        # Parse times for comparison
        self_hour = int(self.time.split(':')[0])
        other_hour = int(other.time.split(':')[0])
        
        # Check various conflict patterns
        if self.rule == "after" and other.rule == "not_after":
            # "after X" conflicts with "not after Y" if X >= Y
            return self_hour >= other_hour
        
        if self.rule == "not_after" and other.rule == "after":
            # Mirror of above
            return other_hour >= self_hour
        
        if self.rule == "before" and other.rule == "not_before":
            return self_hour <= other_hour
        
        if self.rule == "not_before" and other.rule == "before":
            return other_hour <= self_hour
        
        return False
    
    def satisfies(self, proposed_time: str) -> bool:
        """Check if a proposed time satisfies this constraint"""
        proposed_hour = int(proposed_time.split(':')[0])
        constraint_hour = int(self.time.split(':')[0])
        
        if self.rule == "after":
            return proposed_hour >= constraint_hour
        elif self.rule == "not_after":
            return proposed_hour < constraint_hour
        elif self.rule == "before":
            return proposed_hour <= constraint_hour
        elif self.rule == "not_before":
            return proposed_hour > constraint_hour
        
        return True


@dataclass
class BeliefState:
    """The agent's structured understanding of user preferences"""
    
    constraints: List[TimeConstraint]
    
    def get_active_constraints(self, target_date: date) -> List[TimeConstraint]:
        """
        Get all constraints that apply to a specific date,
        sorted by priority (highest first).
        """
        active = [c for c in self.constraints if c.applies_to(target_date)]
        return sorted(active, key=lambda c: c.priority, reverse=True)
    
    def detect_conflicts(self, target_date: date) -> List[tuple[TimeConstraint, TimeConstraint]]:
        """Find all conflicting constraints for a specific date"""
        active = self.get_active_constraints(target_date)
        conflicts = []
        
        for i, c1 in enumerate(active):
            for c2 in active[i+1:]:
                if c1.conflicts_with(c2, target_date):
                    conflicts.append((c1, c2))
        
        return conflicts
    
    def propose_time(self, target_date: date) -> Optional[str]:
        """
        Propose a time that satisfies all constraints.
        Returns None if:
        - No preferences exist (should ask user)
        - Conflicts exist (should ask for clarification)
        - No valid time can satisfy all constraints
        """
        constraints = self.get_active_constraints(target_date)
        
        if not constraints:
            return None  # No preferences
        
        # Check for conflicts
        if self.detect_conflicts(target_date):
            return None  # Can't resolve automatically
        
        # Try to find a time that satisfies all constraints
        # Start with the highest priority constraint's time
        proposed_time = None
        
        for constraint in constraints:
            if constraint.rule == "after":
                # Use this time as the proposal
                proposed_time = constraint.time
            elif constraint.rule == "not_after":
                # Schedule 1 hour before the limit
                hour = int(constraint.time.split(':')[0])
                proposed_time = f"{max(9, hour - 1):02d}:00"
        
        # Verify the proposed time satisfies ALL constraints
        if proposed_time:
            for constraint in constraints:
                if not constraint.satisfies(proposed_time):
                    return None  # Conflict detected
        
        return proposed_time
    
    def explain_reasoning(self, target_date: date, proposed_time: Optional[str]) -> str:
        """Generate a human-readable explanation of the decision"""
        constraints = self.get_active_constraints(target_date)
        
        if not constraints:
            return "I don't have any scheduling preferences for this date."
        
        if not proposed_time:
            conflicts = self.detect_conflicts(target_date)
            if conflicts:
                c1, c2 = conflicts[0]
                return (
                    f"I found conflicting preferences:\n"
                    f"• '{c1.original_text}'\n"
                    f"• '{c2.original_text}'\n\n"
                    f"Which should I prioritize?"
                )
            return "I couldn't find a time that satisfies all your preferences."
        
        # Explain why this time was chosen
        reasons = []
        for c in constraints[:2]:  # Show top 2 reasons
            reasons.append(f"• {c.original_text}")
        
        explanation = f"I chose {proposed_time} because:\n" + "\n".join(reasons)
        return explanation