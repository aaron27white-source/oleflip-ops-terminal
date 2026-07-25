-- Phase 2 migration 006 — quantity-aware scanner fields on flagged_deals.
-- current_bid/max_bid remain the whole-lot totals; these add the per-unit view.
-- ALTER (not CREATE) because 003 already made the table; ledgered so it runs once.

ALTER TABLE flagged_deals ADD COLUMN quantity INTEGER DEFAULT 1;
ALTER TABLE flagged_deals ADD COLUMN per_unit_cost REAL;
ALTER TABLE flagged_deals ADD COLUMN max_bid_per_unit REAL;
