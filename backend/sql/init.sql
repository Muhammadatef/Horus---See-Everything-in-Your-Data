-- Database initialization script for Local AI-BI Platform

-- Create database schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Data sources table (uploaded files metadata)
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'pending',
    schema_info JSONB,
    row_count INTEGER,
    column_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Datasets table (processed data tables)
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    data_source_id UUID REFERENCES data_sources(id) ON DELETE CASCADE,
    table_name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    schema_definition JSONB NOT NULL,
    sample_questions TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query history table
CREATE TABLE queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    generated_sql TEXT,
    results JSONB,
    visualization_config JSONB,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dashboard configurations
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    layout_config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dashboard widgets
CREATE TABLE dashboard_widgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    query_id UUID REFERENCES queries(id) ON DELETE CASCADE,
    position_x INTEGER NOT NULL,
    position_y INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    widget_config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_data_sources_upload_date ON data_sources(upload_date);
CREATE INDEX idx_datasets_data_source_id ON datasets(data_source_id);
CREATE INDEX idx_queries_dataset_id ON queries(dataset_id);
CREATE INDEX idx_queries_created_at ON queries(created_at);
CREATE INDEX idx_dashboard_widgets_dashboard_id ON dashboard_widgets(dashboard_id);

-- Insert sample data for development
INSERT INTO data_sources (
    name, 
    original_filename, 
    file_type, 
    file_size, 
    processing_status,
    row_count,
    column_count,
    schema_info
) VALUES (
    'Sample User Analytics',
    'user_analytics.csv',
    'csv',
    2048,
    'completed',
    20,
    10,
    '{"columns": ["user_id", "name", "email", "status", "signup_date", "last_login", "plan_type", "monthly_spending", "region", "age", "gender"]}'::jsonb
);

-- Create a sample dataset entry
INSERT INTO datasets (
    data_source_id,
    table_name,
    display_name,
    description,
    schema_definition,
    sample_questions
) SELECT 
    id,
    'user_analytics',
    'User Analytics Data',
    'Customer user data with activity status and demographics',
    '{
        "user_id": {"type": "string", "description": "Unique user identifier"},
        "name": {"type": "string", "description": "User full name"},
        "email": {"type": "string", "description": "User email address"},
        "status": {"type": "string", "description": "User status: active or inactive"},
        "signup_date": {"type": "date", "description": "Date when user signed up"},
        "last_login": {"type": "date", "description": "Date of last login"},
        "plan_type": {"type": "string", "description": "Subscription plan: basic or premium"},
        "monthly_spending": {"type": "number", "description": "Monthly spending amount in USD"},
        "region": {"type": "string", "description": "Geographic region"},
        "age": {"type": "number", "description": "User age in years"},
        "gender": {"type": "string", "description": "User gender"}
    }'::jsonb,
    ARRAY[
        'How many active users do we have?',
        'Show me user distribution by region',
        'What is our average monthly spending?',
        'How many premium users are there?',
        'Which users haven''t logged in recently?'
    ]
FROM data_sources 
WHERE original_filename = 'user_analytics.csv'
LIMIT 1;