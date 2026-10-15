"""
Outil interactif d'interrogation et de test du Workflow Text-to-SQL Gouverné.
"""

from .questions import QUESTIONS_CATALOG
from .runner import WorkflowRunner

__all__ = ["QUESTIONS_CATALOG", "WorkflowRunner"]
