"""Scenario: public bid scored with a rubric, where the offer document decides points.

The price-only bid cannot measure an injection that changes the score: the evaluator never reads the
documents and the price is computed by a declassifier. Here three of the four criteria (técnico,
experiencia, comercial) come from the document, so a supplier's text can try to move the award without
leaking anything. Two arms: the evaluator reads the documents (directo), or only a closed sheet that the
registrar extracted and a tool scores (ficha, defense D2). Rule P3 checks the coherence of the published
result with the rubric (defense D1).
"""
from .case import (
    BUDGET,
    EVALUATOR_ROLE,
    INJECTION_MARK,
    OPTIONS,
    POLICY,
    ROLES,
    SUPPLIERS,
    VARIANTS,
    Case,
    coherence_rule,
    document,
    draw,
    injection,
    prepare,
)
from .prompts import ARMS, SYSTEM, TASK, prompts, rubric_text
from .rules import CRITERIA, MAX_POINTS, incoherence, rubric_scores
from .scripted import ROLE_STEPS, run, table
from .tools import TOOLS

__all__ = ["ARMS", "BUDGET", "CRITERIA", "EVALUATOR_ROLE", "INJECTION_MARK", "MAX_POINTS", "OPTIONS", "POLICY",
           "ROLES", "ROLE_STEPS", "SUPPLIERS", "SYSTEM", "TASK", "TOOLS", "VARIANTS", "Case", "coherence_rule",
           "document", "draw", "incoherence", "injection", "prepare", "prompts", "rubric_scores", "rubric_text",
           "run", "table"]
