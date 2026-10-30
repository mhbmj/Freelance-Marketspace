-- Test 1: Duplicate email (Expect Error)
INSERT INTO users (first_name, last_name, email, password_hash)
VALUES ('کاربر', 'تستی', 'sara@gmail.com', 'pass123');

-- Test 2: Invalid Foreign Key (Expect Error)
INSERT INTO projects (employer_id, title, description, pricing_type, budget, status)
VALUES (999, 'پروژه تستی', 'توضیحات', 'FIXED_PRICE', 5000000, 'OPEN');

-- Test 3: Negative budget (Expect Error)
INSERT INTO projects (employer_id, title, description, pricing_type, budget, status)
VALUES (2, 'پروژه بودجه منفی', 'توضیحات', 'FIXED_PRICE', -2000, 'OPEN');

-- Test 4: Zero bid amount (Expect Error)
INSERT INTO proposals (project_id, freelancer_id, bid_amount, cover_letter, status)
VALUES (2, 3, 0, 'پیشنهاد با مبلغ صفر', 'PENDING');

-- Test 5: Duplicate proposal per freelancer/project (Expect Error)
INSERT INTO proposals (project_id, freelancer_id, bid_amount, cover_letter, status)
VALUES (2, 3, 450000, 'پیشنهاد دوم', 'PENDING');

-- Test 6: Employer proposing on own project (Expect Error)
INSERT INTO proposals (project_id, freelancer_id, bid_amount, cover_letter, status)
VALUES (1, 2, 10000000, 'پیشنهاد کارفرما', 'PENDING');

-- Test 7: Multiple accepted proposals for one project (Expect Error)
INSERT INTO proposals (project_id, freelancer_id, bid_amount, cover_letter, status)
VALUES (1, 4, 18000000, 'پیشنهاد دیگر', 'PENDING');

UPDATE proposals
SET status = 'ACCEPTED'
WHERE project_id = 1 AND freelancer_id = 4;

-- Test 8: Verify project status auto-updated to IN_PROGRESS (Positive Test)
SELECT id, title, status
FROM projects
WHERE id = 1;
