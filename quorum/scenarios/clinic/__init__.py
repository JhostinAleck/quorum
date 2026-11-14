"""Scenario: a clinic that coordinates care over clinical records.

Two exits with different authorizations: the referral to the specialist may
carry the patient's own record, the invoice to the insurer may carry none.
It is a policy file, eight tools and scripted episodes. The kernel is untouched.
"""
from .case import KINDS, PATIENT, POLICY, ROLES, VICTIM, Case, Episode, prepare, run
from .tools import TOOLS

__all__ = ["KINDS", "PATIENT", "POLICY", "ROLES", "TOOLS", "VICTIM",
           "Case", "Episode", "prepare", "run"]
