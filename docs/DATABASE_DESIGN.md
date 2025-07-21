# Database Design for Reconstruction Estimation System

## Overview

This document details the complete database design for the reconstruction estimation system, optimized for single-user operation with SQLite while maintaining scalability for future multi-user scenarios.

## Database Architecture

### Technology Stack
- **Database**: SQLite 3.40+
- **ORM**: SQLAlchemy 2.0
- **Migration Tool**: Alembic
- **Backup Strategy**: Automated daily backups with 30-day retention

### Design Principles
1. **Normalized Structure**: 3NF normalization to prevent data anomalies
2. **Referential Integrity**: Foreign key constraints enforced
3. **Audit Trail**: Created/updated timestamps on all tables
4. **Soft Deletes**: Logical deletion with `deleted_at` timestamps
5. **JSON Support**: Flexible metadata storage for extensibility

## Core Schema Design

### Projects Domain

```sql
-- Projects table: Core project information
CREATE TABLE projects (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL,
    description TEXT,
    location TEXT NOT NULL,
    address TEXT,
    customer_name TEXT,
    customer_email TEXT,
    customer_phone TEXT,
    status TEXT NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'IN_PROGRESS', 'COMPLETED', 'APPROVED', 'CANCELLED')),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    CONSTRAINT chk_valid_email CHECK (customer_email IS NULL OR customer_email LIKE '%@%.%')
);

-- Project images: Store uploaded images
CREATE TABLE project_images (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT 0,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT chk_mime_type CHECK (mime_type IN ('image/jpeg', 'image/png', 'image/bmp', 'image/tiff'))
);

-- Project notes: Track project history and communications
CREATE TABLE project_notes (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    note_type TEXT NOT NULL CHECK (note_type IN ('GENERAL', 'CHANGE', 'ISSUE', 'CUSTOMER')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
```

### Quantification Domain

```sql
-- Work scopes: Master list of available work scopes
CREATE TABLE work_scopes (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('DEMOLITION', 'INSTALLATION', 'FINISHING', 'MECHANICAL', 'ELECTRICAL', 'PLUMBING')),
    measurement_type TEXT NOT NULL CHECK (measurement_type IN ('LINEAR', 'AREA', 'VOLUME', 'COUNT')),
    unit_of_measure TEXT NOT NULL,
    description TEXT,
    keywords TEXT, -- Comma-separated keywords for mapping
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Measurements: Extracted measurements from images
CREATE TABLE measurements (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    image_id TEXT NOT NULL,
    measurement_type TEXT NOT NULL CHECK (measurement_type IN ('LINEAR', 'AREA', 'VOLUME', 'COUNT')),
    value DECIMAL(10,3) NOT NULL,
    unit TEXT NOT NULL,
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    location TEXT, -- Room or area identifier
    extracted_text TEXT, -- Original OCR text
    bounding_box JSON, -- Coordinates in image
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (image_id) REFERENCES project_images(id) ON DELETE CASCADE
);

-- Quantification items: Mapped work scope quantities
CREATE TABLE quantification_items (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    work_scope_id TEXT NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit TEXT NOT NULL,
    location TEXT,
    debris_weight DECIMAL(10,2), -- in pounds
    notes TEXT,
    manual_override BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (work_scope_id) REFERENCES work_scopes(id)
);

-- Quantification measurements: Link measurements to quantification items
CREATE TABLE quantification_measurements (
    quantification_item_id TEXT NOT NULL,
    measurement_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (quantification_item_id, measurement_id),
    FOREIGN KEY (quantification_item_id) REFERENCES quantification_items(id) ON DELETE CASCADE,
    FOREIGN KEY (measurement_id) REFERENCES measurements(id) ON DELETE CASCADE
);

-- Conflicts: Detected conflicts between work scope items
CREATE TABLE conflicts (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    item1_id TEXT NOT NULL,
    item2_id TEXT NOT NULL,
    conflict_type TEXT NOT NULL CHECK (conflict_type IN ('MATERIAL', 'SCOPE', 'SEQUENCE', 'DUPLICATE')),
    severity TEXT NOT NULL CHECK (severity IN ('ERROR', 'WARNING', 'INFO')),
    message TEXT NOT NULL,
    resolved BOOLEAN DEFAULT 0,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (item1_id) REFERENCES quantification_items(id) ON DELETE CASCADE,
    FOREIGN KEY (item2_id) REFERENCES quantification_items(id) ON DELETE CASCADE
);
```

### Costing Domain

```sql
-- Materials: Master material list with pricing
CREATE TABLE materials (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    unit TEXT NOT NULL,
    base_cost DECIMAL(10,2) NOT NULL,
    east_us_multiplier DECIMAL(4,3) DEFAULT 1.000,
    supplier TEXT,
    supplier_sku TEXT,
    min_order_quantity DECIMAL(10,3),
    lead_time_days INTEGER,
    active BOOLEAN DEFAULT 1,
    last_price_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Material price history: Track price changes over time
CREATE TABLE material_price_history (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    material_id TEXT NOT NULL,
    old_price DECIMAL(10,2) NOT NULL,
    new_price DECIMAL(10,2) NOT NULL,
    change_reason TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
);

-- Labor rates: Trade-specific labor pricing
CREATE TABLE labor_rates (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    trade TEXT NOT NULL,
    skill_level TEXT NOT NULL CHECK (skill_level IN ('APPRENTICE', 'JOURNEYMAN', 'MASTER')),
    base_hourly_rate DECIMAL(6,2) NOT NULL,
    east_us_rate DECIMAL(6,2) NOT NULL,
    overtime_multiplier DECIMAL(3,2) DEFAULT 1.5,
    productivity_factor DECIMAL(4,2) DEFAULT 1.00,
    crew_size INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT 1,
    last_rate_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade, skill_level)
);

-- Equipment rates: Equipment rental pricing
CREATE TABLE equipment_rates (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    equipment_name TEXT NOT NULL,
    category TEXT NOT NULL,
    daily_rate DECIMAL(8,2) NOT NULL,
    weekly_rate DECIMAL(8,2),
    monthly_rate DECIMAL(8,2),
    delivery_fee DECIMAL(6,2),
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work scope materials: Link materials to work scopes
CREATE TABLE work_scope_materials (
    work_scope_id TEXT NOT NULL,
    material_id TEXT NOT NULL,
    quantity_per_unit DECIMAL(10,3) NOT NULL,
    waste_factor DECIMAL(3,2) DEFAULT 1.10,
    is_primary BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (work_scope_id, material_id),
    FOREIGN KEY (work_scope_id) REFERENCES work_scopes(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

-- Work scope labor: Link labor requirements to work scopes
CREATE TABLE work_scope_labor (
    work_scope_id TEXT NOT NULL,
    labor_rate_id TEXT NOT NULL,
    hours_per_unit DECIMAL(6,3) NOT NULL,
    difficulty_factor DECIMAL(3,2) DEFAULT 1.00,
    is_primary BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (work_scope_id, labor_rate_id),
    FOREIGN KEY (work_scope_id) REFERENCES work_scopes(id) ON DELETE CASCADE,
    FOREIGN KEY (labor_rate_id) REFERENCES labor_rates(id)
);

-- Cost items: Calculated costs for quantification items
CREATE TABLE cost_items (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    quantification_item_id TEXT NOT NULL,
    material_cost DECIMAL(10,2) DEFAULT 0,
    labor_cost DECIMAL(10,2) DEFAULT 0,
    equipment_cost DECIMAL(10,2) DEFAULT 0,
    subtotal DECIMAL(10,2) NOT NULL,
    markup_percentage DECIMAL(5,2) DEFAULT 0,
    total_cost DECIMAL(10,2) NOT NULL,
    cost_per_unit DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (quantification_item_id) REFERENCES quantification_items(id) ON DELETE CASCADE
);

-- Cost item details: Breakdown of materials and labor
CREATE TABLE cost_item_materials (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    cost_item_id TEXT NOT NULL,
    material_id TEXT NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit_cost DECIMAL(10,2) NOT NULL,
    waste_factor DECIMAL(3,2) DEFAULT 1.10,
    total_cost DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cost_item_id) REFERENCES cost_items(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

CREATE TABLE cost_item_labor (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    cost_item_id TEXT NOT NULL,
    labor_rate_id TEXT NOT NULL,
    hours DECIMAL(8,2) NOT NULL,
    rate DECIMAL(6,2) NOT NULL,
    difficulty_factor DECIMAL(3,2) DEFAULT 1.00,
    total_cost DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cost_item_id) REFERENCES cost_items(id) ON DELETE CASCADE,
    FOREIGN KEY (labor_rate_id) REFERENCES labor_rates(id)
);
```

### Estimation Domain

```sql
-- Project timelines: Overall project schedule
CREATE TABLE project_timelines (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_duration_days INTEGER NOT NULL,
    buffer_percentage DECIMAL(5,2) DEFAULT 15.0,
    critical_path JSON, -- Array of task IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Timeline tasks: Individual tasks in the timeline
CREATE TABLE timeline_tasks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    timeline_id TEXT NOT NULL,
    work_scope_id TEXT NOT NULL,
    name TEXT NOT NULL,
    duration_days INTEGER NOT NULL,
    start_date DATE,
    end_date DATE,
    crew_size INTEGER DEFAULT 1,
    can_parallel BOOLEAN DEFAULT 0,
    is_critical BOOLEAN DEFAULT 0,
    sequence_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (timeline_id) REFERENCES project_timelines(id) ON DELETE CASCADE,
    FOREIGN KEY (work_scope_id) REFERENCES work_scopes(id)
);

-- Task dependencies: Define task relationships
CREATE TABLE task_dependencies (
    task_id TEXT NOT NULL,
    depends_on_task_id TEXT NOT NULL,
    dependency_type TEXT DEFAULT 'FINISH_TO_START' CHECK (dependency_type IN ('FINISH_TO_START', 'START_TO_START', 'FINISH_TO_FINISH')),
    lag_days INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, depends_on_task_id),
    FOREIGN KEY (task_id) REFERENCES timeline_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES timeline_tasks(id) ON DELETE CASCADE
);

-- Disposal costs: Debris disposal calculations
CREATE TABLE disposal_costs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL UNIQUE,
    total_weight_lbs DECIMAL(10,2) NOT NULL,
    disposal_method TEXT NOT NULL CHECK (disposal_method IN ('DUMPSTER', 'PICKUP', 'RECYCLING')),
    container_size TEXT,
    container_count INTEGER DEFAULT 1,
    unit_cost DECIMAL(8,2) NOT NULL,
    disposal_cost DECIMAL(10,2) NOT NULL,
    cleanup_labor_hours DECIMAL(6,2) DEFAULT 0,
    cleanup_labor_rate DECIMAL(6,2) DEFAULT 0,
    cleanup_cost DECIMAL(10,2) DEFAULT 0,
    total_cost DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Tax configuration: Regional tax settings
CREATE TABLE tax_configurations (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    location TEXT NOT NULL UNIQUE,
    material_tax_rate DECIMAL(5,4) NOT NULL,
    labor_tax_rate DECIMAL(5,4) NOT NULL,
    tax_responsibility TEXT NOT NULL CHECK (tax_responsibility IN ('CUSTOMER', 'CONTRACTOR')),
    exemptions JSON, -- List of exempt categories
    effective_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project estimates: Final estimates
CREATE TABLE project_estimates (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    direct_costs DECIMAL(12,2) NOT NULL,
    disposal_cost DECIMAL(10,2) DEFAULT 0,
    overhead_percentage DECIMAL(5,2) NOT NULL,
    overhead_amount DECIMAL(10,2) NOT NULL,
    profit_percentage DECIMAL(5,2) NOT NULL,
    profit_amount DECIMAL(10,2) NOT NULL,
    material_tax DECIMAL(10,2) DEFAULT 0,
    labor_tax DECIMAL(10,2) DEFAULT 0,
    total_tax DECIMAL(10,2) DEFAULT 0,
    subtotal DECIMAL(12,2) NOT NULL,
    total_estimate DECIMAL(12,2) NOT NULL,
    valid_until DATE,
    status TEXT DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'FINAL', 'APPROVED', 'REJECTED', 'EXPIRED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Estimate validation: Track validation checks
CREATE TABLE estimate_validations (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    estimate_id TEXT NOT NULL,
    check_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PASSED', 'FAILED', 'WARNING')),
    severity TEXT NOT NULL CHECK (severity IN ('ERROR', 'WARNING', 'INFO')),
    message TEXT NOT NULL,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estimate_id) REFERENCES project_estimates(id) ON DELETE CASCADE
);
```

### Reporting and Analytics

```sql
-- Estimate history: Track all estimate versions
CREATE TABLE estimate_history (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    estimate_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    total_estimate DECIMAL(12,2) NOT NULL,
    change_reason TEXT,
    changed_by TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    snapshot JSON, -- Full estimate data snapshot
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (estimate_id) REFERENCES project_estimates(id) ON DELETE CASCADE
);

-- Project metrics: Aggregated metrics for reporting
CREATE TABLE project_metrics (
    project_id TEXT PRIMARY KEY,
    total_sqft DECIMAL(10,2),
    total_linear_ft DECIMAL(10,2),
    demolition_weight_lbs DECIMAL(10,2),
    material_cost_ratio DECIMAL(5,2),
    labor_cost_ratio DECIMAL(5,2),
    average_cost_per_sqft DECIMAL(8,2),
    timeline_efficiency DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
```

## Indexes for Performance

```sql
-- Project indexes
CREATE INDEX idx_projects_status ON projects(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_created ON projects(created_at DESC);
CREATE INDEX idx_projects_location ON projects(location);

-- Quantification indexes
CREATE INDEX idx_measurements_project ON measurements(project_id);
CREATE INDEX idx_measurements_type ON measurements(measurement_type);
CREATE INDEX idx_quant_items_project ON quantification_items(project_id);
CREATE INDEX idx_quant_items_scope ON quantification_items(work_scope_id);
CREATE INDEX idx_conflicts_project ON conflicts(project_id) WHERE resolved = 0;

-- Costing indexes
CREATE INDEX idx_materials_category ON materials(category) WHERE active = 1;
CREATE INDEX idx_materials_code ON materials(code);
CREATE INDEX idx_labor_trade_skill ON labor_rates(trade, skill_level) WHERE active = 1;
CREATE INDEX idx_cost_items_project ON cost_items(project_id);

-- Estimation indexes
CREATE INDEX idx_estimates_project ON project_estimates(project_id);
CREATE INDEX idx_estimates_status ON project_estimates(status);
CREATE INDEX idx_validations_estimate ON estimate_validations(estimate_id);
CREATE INDEX idx_validations_status ON estimate_validations(status, severity);

-- Full-text search indexes
CREATE VIRTUAL TABLE work_scopes_fts USING fts5(
    name, description, keywords, content=work_scopes
);

CREATE VIRTUAL TABLE materials_fts USING fts5(
    name, category, supplier, content=materials
);
```

## Views for Common Queries

```sql
-- Active project summary view
CREATE VIEW v_project_summary AS
SELECT 
    p.id,
    p.name,
    p.location,
    p.status,
    p.created_at,
    COUNT(DISTINCT pi.id) as image_count,
    COUNT(DISTINCT qi.id) as item_count,
    pe.total_estimate as latest_estimate,
    pe.created_at as estimate_date
FROM projects p
LEFT JOIN project_images pi ON p.id = pi.project_id
LEFT JOIN quantification_items qi ON p.id = qi.project_id
LEFT JOIN project_estimates pe ON p.id = pe.project_id 
    AND pe.version = (SELECT MAX(version) FROM project_estimates WHERE project_id = p.id)
WHERE p.deleted_at IS NULL
GROUP BY p.id;

-- Cost breakdown view
CREATE VIEW v_cost_breakdown AS
SELECT 
    ci.project_id,
    ws.category,
    SUM(ci.material_cost) as total_material_cost,
    SUM(ci.labor_cost) as total_labor_cost,
    SUM(ci.equipment_cost) as total_equipment_cost,
    SUM(ci.total_cost) as total_cost,
    COUNT(*) as item_count
FROM cost_items ci
JOIN quantification_items qi ON ci.quantification_item_id = qi.id
JOIN work_scopes ws ON qi.work_scope_id = ws.id
GROUP BY ci.project_id, ws.category;

-- Material usage view
CREATE VIEW v_material_usage AS
SELECT 
    m.name as material_name,
    m.category,
    m.unit,
    SUM(cim.quantity) as total_quantity,
    COUNT(DISTINCT ci.project_id) as project_count,
    AVG(cim.unit_cost) as avg_unit_cost,
    MAX(cim.created_at) as last_used
FROM cost_item_materials cim
JOIN materials m ON cim.material_id = m.id
JOIN cost_items ci ON cim.cost_item_id = ci.id
GROUP BY m.id;
```

## Triggers for Data Integrity

```sql
-- Update timestamp triggers
CREATE TRIGGER update_projects_timestamp 
AFTER UPDATE ON projects
BEGIN
    UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_quantification_items_timestamp 
AFTER UPDATE ON quantification_items
BEGIN
    UPDATE quantification_items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Maintain estimate version numbering
CREATE TRIGGER increment_estimate_version
BEFORE INSERT ON project_estimates
BEGIN
    UPDATE project_estimates 
    SET version = (
        SELECT COALESCE(MAX(version), 0) + 1 
        FROM project_estimates 
        WHERE project_id = NEW.project_id
    )
    WHERE id = NEW.id;
END;

-- Archive price changes
CREATE TRIGGER archive_material_price_change
AFTER UPDATE OF base_cost ON materials
WHEN OLD.base_cost != NEW.base_cost
BEGIN
    INSERT INTO material_price_history (material_id, old_price, new_price)
    VALUES (NEW.id, OLD.base_cost, NEW.base_cost);
END;
```

## Data Migration Strategy

### Initial Data Load

```sql
-- Load default work scopes
INSERT INTO work_scopes (code, name, category, measurement_type, unit_of_measure, keywords) VALUES
('DEMO_DW', 'Drywall Demolition', 'DEMOLITION', 'AREA', 'sqft', 'drywall,sheetrock,gypsum,wall,ceiling'),
('DEMO_FL', 'Flooring Demolition', 'DEMOLITION', 'AREA', 'sqft', 'floor,carpet,tile,hardwood,vinyl'),
('INST_DW', 'Drywall Installation', 'INSTALLATION', 'AREA', 'sqft', 'drywall,sheetrock,gypsum,wall,ceiling,new'),
('INST_FL_TILE', 'Tile Flooring Installation', 'INSTALLATION', 'AREA', 'sqft', 'tile,floor,ceramic,porcelain'),
('INST_PAINT', 'Interior Painting', 'FINISHING', 'AREA', 'sqft', 'paint,wall,ceiling,primer,finish'),
('INST_TRIM', 'Trim Installation', 'FINISHING', 'LINEAR', 'ft', 'trim,baseboard,crown,molding,casing');

-- Load East US material pricing
INSERT INTO materials (code, name, category, unit, base_cost, east_us_multiplier) VALUES
('DW_58', '5/8" Drywall Sheet', 'DRYWALL', 'sheet', 12.50, 1.05),
('DW_COMP', 'Joint Compound', 'DRYWALL', 'bucket', 15.00, 1.03),
('PAINT_PRIM', 'Primer Paint', 'PAINT', 'gallon', 25.00, 1.08),
('PAINT_INT', 'Interior Paint', 'PAINT', 'gallon', 35.00, 1.08),
('TILE_CER12', '12x12 Ceramic Tile', 'FLOORING', 'sqft', 2.50, 1.10),
('TRIM_BASE', 'Baseboard Trim', 'TRIM', 'ft', 2.25, 1.12);

-- Load East US labor rates
INSERT INTO labor_rates (trade, skill_level, base_hourly_rate, east_us_rate) VALUES
('DRYWALL', 'JOURNEYMAN', 35.00, 42.00),
('DRYWALL', 'MASTER', 45.00, 54.00),
('PAINTER', 'JOURNEYMAN', 30.00, 38.00),
('PAINTER', 'MASTER', 40.00, 48.00),
('TILE_SETTER', 'JOURNEYMAN', 40.00, 48.00),
('TILE_SETTER', 'MASTER', 50.00, 60.00),
('CARPENTER', 'JOURNEYMAN', 35.00, 42.00),
('CARPENTER', 'MASTER', 45.00, 54.00);
```

## Backup and Recovery

```sql
-- Backup script (to be run via cron/scheduler)
.backup 'backups/reconstruction_estimate_backup_' || strftime('%Y%m%d_%H%M%S', 'now') || '.db'

-- Integrity check
PRAGMA integrity_check;

-- Vacuum and analyze for optimization
VACUUM;
ANALYZE;
```

## Security Considerations

1. **Row-Level Security**: Implement application-level checks since SQLite doesn't support RLS
2. **Encryption**: Use SQLCipher for database encryption at rest
3. **Access Control**: Restrict database file permissions to application user only
4. **SQL Injection Prevention**: Use parameterized queries exclusively
5. **Audit Logging**: Log all data modifications with user context

## Performance Optimization

1. **Connection Pooling**: Use SQLAlchemy connection pool with size=5, overflow=10
2. **Write-Ahead Logging**: Enable WAL mode for better concurrency
3. **Page Size**: Set to 4096 bytes for optimal performance
4. **Cache Size**: Set to 10000 pages (40MB) for frequently accessed data
5. **Prepared Statements**: Use for all repeated queries

```sql
-- Enable optimizations
PRAGMA journal_mode = WAL;
PRAGMA page_size = 4096;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456; -- 256MB memory-mapped I/O
```

This database design provides a robust foundation for the reconstruction estimation system with proper normalization, referential integrity, and performance optimization.