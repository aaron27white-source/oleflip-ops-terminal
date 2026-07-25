-- Phase 2 migration 005 — idempotent starter seeds (INSERT OR IGNORE on UNIQUE
-- columns), matching Phase 1's seeding style. Ledgered so it runs once, but
-- INSERT OR IGNORE keeps it safe even if re-run.

INSERT OR IGNORE INTO categories (name, icon, sort_order) VALUES
 ('PC/Server Parts','cpu',10),
 ('Phones','smartphone',20),
 ('Flip Phones','phone',30),
 ('Monitors','monitor',40),
 ('Tablets','tablet',50),
 ('Laptops','laptop',60),
 ('Peripherals','keyboard',70),
 ('Desktops/Servers','server',80);

INSERT OR IGNORE INTO sources (name, type, reliability_score) VALUES
 ('GovDeals','govdeals',4),
 ('FB Marketplace','fb',3),
 ('Flea Market','flea',3),
 ('ITAD','itad',4),
 ('University Surplus','university',4);

INSERT OR IGNORE INTO products (category_id, brand, model, condition_tiers, specs_json) VALUES
 ((SELECT id FROM categories WHERE name='Phones'),'Apple','iPhone 11',
   '["Like-New","Good","Fair","For-Parts"]','{"storage":["64GB","128GB","256GB"]}'),
 ((SELECT id FROM categories WHERE name='Flip Phones'),'Kyocera','DuraXV',
   '["Good","Fair","For-Parts"]','{}'),
 ((SELECT id FROM categories WHERE name='Monitors'),'Dell','U2419H',
   '["Good","Fair","For-Parts"]','{"size":"24","panel":"IPS","res":"1080p"}');
