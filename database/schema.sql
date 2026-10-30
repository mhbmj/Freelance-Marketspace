-- Drop existing tables
DROP TABLE IF EXISTS proposals CASCADE;
DROP TABLE IF EXISTS project_skills CASCADE;
DROP TABLE IF EXISTS project_categories CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS user_skills CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS certificates CASCADE;
DROP TABLE IF EXISTS portfolios CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Admins
CREATE TABLE admins (
    user_id INT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    role_title VARCHAR(50) DEFAULT 'Admin',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. User Profiles
CREATE TABLE user_profiles (
    user_id INT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    professional_title VARCHAR(100),
    bio TEXT,
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Portfolios
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    project_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Certificates
CREATE TABLE certificates (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    issuing_organization VARCHAR(150) NOT NULL,
    issue_date DATE NOT NULL,
    credential_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Skills
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. User Skills (Many-to-Many)
CREATE TABLE user_skills (
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id INT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    years_of_experience INT DEFAULT 0 CHECK (years_of_experience >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, skill_id)
);

-- 9. Projects
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    employer_id INT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    pricing_type VARCHAR(20) NOT NULL CHECK (pricing_type IN ('FIXED_PRICE', 'HOURLY')),
    budget NUMERIC(12, 2) NOT NULL CHECK (budget > 0),
    deadline TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Project Categories (Many-to-Many)
CREATE TABLE project_categories (
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category_id INT NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, category_id)
);

-- 11. Project Skills (Many-to-Many)
CREATE TABLE project_skills (
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    skill_id INT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    is_required BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (project_id, skill_id)
);

-- 12. Proposals
CREATE TABLE proposals (
    id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    freelancer_id INT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    bid_amount NUMERIC(12, 2) NOT NULL CHECK (bid_amount > 0),
    estimated_duration INT CHECK (estimated_duration IS NULL OR estimated_duration > 0),
    cover_letter TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'ACCEPTED', 'REJECTED', 'WITHDRAWN')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, freelancer_id)
);

-- At most one accepted proposal per project
CREATE UNIQUE INDEX idx_one_accepted_proposal
ON proposals (project_id)
WHERE status = 'ACCEPTED';

-- Business Rule: Check proposal validity
CREATE OR REPLACE FUNCTION check_proposal_before_insert()
RETURNS TRIGGER AS $$
DECLARE
    p_employer_id INT;
    p_status VARCHAR(20);
BEGIN
    SELECT employer_id, status INTO p_employer_id, p_status
    FROM projects WHERE id = NEW.project_id;

    IF NEW.freelancer_id = p_employer_id THEN
        RAISE EXCEPTION 'Employer cannot submit a proposal for their own project';
    END IF;

    IF p_status != 'OPEN' THEN
        RAISE EXCEPTION 'Proposals can only be submitted for OPEN projects';
    END IF;

    IF EXISTS (SELECT 1 FROM admins WHERE user_id = NEW.freelancer_id) THEN
        RAISE EXCEPTION 'Admins cannot submit proposals';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_proposal
BEFORE INSERT ON proposals
FOR EACH ROW
EXECUTE FUNCTION check_proposal_before_insert();

-- Business Rule: Update project status when proposal is accepted
CREATE OR REPLACE FUNCTION update_project_status_on_accept()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'ACCEPTED' THEN
        UPDATE projects
        SET status = 'IN_PROGRESS', updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.project_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_project_status
AFTER UPDATE OF status ON proposals
FOR EACH ROW
EXECUTE FUNCTION update_project_status_on_accept();
