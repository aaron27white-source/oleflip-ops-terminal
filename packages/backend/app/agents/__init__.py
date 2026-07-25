"""Agent system — LLM reasoning layers on top of the existing services.

Deterministic Python does the data work (scanner_service, inventory, price DB);
the LLM does judgment and writing. Agents communicate through tables
(intel_board, inventory_kpis), never by importing each other. See
Agent-System-Build-Spec.md.
"""
