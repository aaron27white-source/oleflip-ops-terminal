-- Generic machine profiles (synthetic). Two priced profiles + one "Tier-C" stub
-- with no pricing mapped, to exercise the UI's amber "needs pricing" path.
INSERT OR IGNORE INTO machines
    (model, brand, generation, standard_ram, standard_ssd, standard_cpu, standard_wifi,
     standard_psu, has_cooler, estimated_total_value, safe_max_bid, notes) VALUES
('OptiPlex 7080',    'Dell', '10th gen (2020)', '16GB DDR4', '256GB NVMe', 'i5-10500', NULL, '200W SFF', 1, 136.00, 74.80, NULL),
('EliteDesk 800 G6', 'HP',   '10th gen (2020)', '16GB DDR4', '512GB NVMe', 'i7-10700', NULL, '210W SFF', 1, 178.00, 97.90, NULL),
('OptiPlex 3020',    'Dell', '4th gen (2014)',  '8GB DDR3',  '256GB SATA', 'i5-4570',  NULL, '255W',     1, NULL,   NULL,  'Tier-C: profile only, no pricing mapped yet.');

INSERT OR IGNORE INTO machine_parts (model, part_id, qty) VALUES
('OptiPlex 7080',    'CPU-I5-10500',   1),
('OptiPlex 7080',    'RAM-D4-16GB-DT', 1),
('OptiPlex 7080',    'SSD-NVME-256',   1),
('OptiPlex 7080',    'PSU-SFF-200',    1),
('EliteDesk 800 G6', 'CPU-I7-10700',   1),
('EliteDesk 800 G6', 'RAM-D4-16GB-DT', 1),
('EliteDesk 800 G6', 'SSD-NVME-512',   1),
('OptiPlex 3020',    'RAM-D4-8GB-DT',  1),
('OptiPlex 3020',    'SSD-SATA-256',   1),
('OptiPlex 3020',    'PSU-SFF-200',    1);
