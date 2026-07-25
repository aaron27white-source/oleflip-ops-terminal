-- 015_flagged_deals_agent.sql — E-Scanner's LLM verdict/note on each flagged lot.
-- Additive columns; the deterministic scanner still writes the rest (see scanner_service).

ALTER TABLE flagged_deals ADD COLUMN agent_verdict TEXT;   -- BUY | PASS | WATCH
ALTER TABLE flagged_deals ADD COLUMN agent_note TEXT;
