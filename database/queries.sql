-- Query 1: Open projects with employer and category
SELECT
    p.id AS project_id,
    p.title AS project_title,
    p.budget,
    p.pricing_type,
    p.status AS project_status,
    u.first_name || ' ' || u.last_name AS employer_name,
    u.email AS employer_email,
    c.name AS category_name
FROM projects p
JOIN users u ON p.employer_id = u.id
JOIN project_categories pc ON p.id = pc.project_id
JOIN categories c ON pc.category_id = c.id
WHERE p.status = 'OPEN';

-- Query 2: Proposals for a specific project (Project ID: 2)
SELECT
    pr.id AS proposal_id,
    p.title AS project_title,
    u.first_name || ' ' || u.last_name AS freelancer_name,
    u.email AS freelancer_email,
    pr.bid_amount,
    pr.estimated_duration,
    pr.status AS proposal_status,
    pr.cover_letter
FROM proposals pr
JOIN projects p ON pr.project_id = p.id
JOIN users u ON pr.freelancer_id = u.id
WHERE pr.project_id = 2;

-- Query 3: Projects count and proposals received per employer
SELECT
    u.first_name || ' ' || u.last_name AS employer_name,
    p.id AS project_id,
    p.title AS project_title,
    p.status AS project_status,
    COUNT(pr.id) AS total_proposals
FROM users u
JOIN projects p ON u.id = p.employer_id
LEFT JOIN proposals pr ON p.id = pr.project_id
GROUP BY u.first_name, u.last_name, p.id, p.title, p.status;

-- Query 4: Required skills for each project
SELECT
    p.id AS project_id,
    p.title AS project_title,
    s.name AS skill_name,
    ps.is_required
FROM projects p
JOIN project_skills ps ON p.id = ps.project_id
JOIN skills s ON ps.skill_id = s.id
ORDER BY p.id, ps.is_required DESC;
