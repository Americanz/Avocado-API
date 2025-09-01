-- PostgreSQL initialization script for Avocado project
-- This script runs once when the database container is first created

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create additional databases if needed
-- CREATE DATABASE avocado_test;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE avocado_db TO avocado_user;

-- Helpful functions for development
CREATE OR REPLACE FUNCTION now_utc() RETURNS timestamp AS $$
    SELECT now() AT TIME ZONE 'UTC';
$$ LANGUAGE sql;

-- Log initialization completion
SELECT 'PostgreSQL database initialized successfully' as status;