-- eBay search terms per part, used by the price scanner. Self-creating table.
CREATE TABLE IF NOT EXISTS part_queries (
    part_id TEXT PRIMARY KEY REFERENCES parts(id),
    query   TEXT NOT NULL
);

INSERT OR IGNORE INTO part_queries (part_id, query) VALUES
('RAM-D4-8GB-DT',  '8GB DDR4 DIMM desktop RAM'),
('RAM-D4-16GB-DT', '16GB DDR4 DIMM desktop RAM'),
('RAM-D4-16GB-LP', '16GB DDR4 SODIMM laptop RAM'),
('SSD-NVME-256',   '256GB NVMe M.2 SSD'),
('SSD-NVME-512',   '512GB NVMe M.2 SSD'),
('SSD-SATA-256',   '256GB SATA 2.5in SSD'),
('CPU-I5-10500',   'Intel Core i5-10500 CPU'),
('CPU-I7-10700',   'Intel Core i7-10700 CPU'),
('WIFI-AX200',     'Intel AX200 wifi card'),
('GPU-GT1030',     'NVIDIA GT 1030 low profile'),
('PSU-SFF-200',    'Dell 200W SFF power supply'),
('NIC-1G-DUAL',    'dual port 1GbE PCIe NIC');
