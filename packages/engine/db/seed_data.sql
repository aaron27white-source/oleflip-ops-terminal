-- Generic reference parts catalog (synthetic — not real market data).
INSERT OR IGNORE INTO parts (id, name, category, subcategory, form_factor, source_models, notes) VALUES
('RAM-D4-8GB-DT',  '8GB DDR4 Desktop RAM',   'RAM', 'DDR4', 'DIMM',   'OptiPlex 7080, EliteDesk 800 G6', NULL),
('RAM-D4-16GB-DT', '16GB DDR4 Desktop RAM',  'RAM', 'DDR4', 'DIMM',   'OptiPlex 7080, EliteDesk 800 G6', NULL),
('RAM-D4-16GB-LP', '16GB DDR4 Laptop RAM',   'RAM', 'DDR4', 'SODIMM', 'Latitude 5410', NULL),
('SSD-NVME-256',   '256GB NVMe SSD',         'SSD', 'NVMe', 'M.2',    'OptiPlex 7080', NULL),
('SSD-NVME-512',   '512GB NVMe SSD',         'SSD', 'NVMe', 'M.2',    'EliteDesk 800 G6', NULL),
('SSD-SATA-256',   '256GB SATA SSD',         'SSD', 'SATA', '2.5"',   'Latitude 5410', NULL),
('CPU-I5-10500',   'Intel Core i5-10500',    'CPU', 'LGA1200', 'CPU', 'OptiPlex 7080', NULL),
('CPU-I7-10700',   'Intel Core i7-10700',    'CPU', 'LGA1200', 'CPU', 'EliteDesk 800 G6', NULL),
('WIFI-AX200',     'Intel AX200 WiFi Card',  'WIFI', 'M.2', 'M.2',    'Latitude 5410', NULL),
('GPU-GT1030',     'NVIDIA GT 1030 (low-profile)', 'GPU', 'PCIe', 'PCIe', 'OptiPlex 7080', NULL),
('PSU-SFF-200',    '200W SFF Power Supply',  'PSU', 'SFF', 'SFF',     'OptiPlex 7080', NULL),
('NIC-1G-DUAL',    'Dual-port 1GbE NIC',     'NIC', 'PCIe', 'PCIe',   'PowerEdge R640', NULL);
