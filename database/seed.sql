-- Truncate existing data
TRUNCATE TABLE proposals, project_skills, project_categories, projects,
               user_skills, skills, categories, certificates, portfolios,
               user_profiles, admins, users
RESTART IDENTITY CASCADE;

-- 1. Users
INSERT INTO users (first_name, last_name, email, phone_number, password_hash, status) VALUES
('امید', 'شمس', 'admin@market.ir', '09121111111', 'hash_admin_123', 'ACTIVE'),
('سارا', 'احمدی', 'sara@gmail.com', '09122222222', 'hash_sara_123', 'ACTIVE'),
('علی', 'رضایی', 'ali@gmail.com', '09123333333', 'hash_ali_123', 'ACTIVE'),
('مریم', 'حسینی', 'maryam@gmail.com', '09124444444', 'hash_maryam_123', 'ACTIVE'),
('رضا', 'محمدی', 'reza@gmail.com', '09125555555', 'hash_reza_123', 'ACTIVE');

-- 2. Admins
INSERT INTO admins (user_id, role_title) VALUES
(1, 'Admin');

-- 3. User Profiles
INSERT INTO user_profiles (user_id, professional_title, bio, location) VALUES
(2, 'برنامه‌نویس فول‌استک', 'توسعه‌دهنده وب پایتون و ری‌اکت', 'تهران'),
(3, 'متخصص بک‌اند', 'توسعه‌دهنده پایتون و پایگاه داده', 'اصفهان'),
(4, 'مدیر محصول', 'کارفرما در پروژه‌های نرم‌افزار', 'شیراز'),
(5, 'برنامه‌نویس فرانت‌اند', 'توسعه‌دهنده React و وب', 'تبریز');

-- 4. Portfolios
INSERT INTO portfolios (user_id, title, description, project_url) VALUES
(2, 'فروشگاه آنلاین', 'طراحی با جنگو و ری‌اکت', 'https://github.com/sara/shop'),
(3, 'سیستم مدیریت انبار', 'بک‌اند جنگو با PostgreSQL', 'https://github.com/ali/warehouse');

-- 5. Certificates
INSERT INTO certificates (user_id, title, issuing_organization, issue_date, credential_url) VALUES
(2, 'Python Professional Certificate', 'Coursera', '2023-05-10', 'https://coursera.org/cert/123'),
(3, 'PostgreSQL Certified Associate', 'PostgreSQL Org', '2023-09-15', 'https://pg-cert.org/cert/456');

-- 6. Categories
INSERT INTO categories (name, description) VALUES
('طراحی وب', 'پروژه‌های فرانت‌اند و بک‌اند'),
('اپلیکیشن موبایل', 'پروژه‌های اندروید و iOS'),
('هوش مصنوعی', 'پروژه‌های پردازش داده و تصویر');

-- 7. Skills
INSERT INTO skills (name, description) VALUES
('Python', 'زبان پایتون'),
('PostgreSQL', 'پایگاه داده رابطه‌ای'),
('React', 'کتابخانه فرانت‌اند'),
('Django', 'فریم‌ورک بک‌اند'),
('UI/UX', 'طراحی رابط کاربری');

-- 8. User Skills
INSERT INTO user_skills (user_id, skill_id, years_of_experience) VALUES
(2, 1, 4),
(2, 3, 3),
(3, 1, 5),
(3, 2, 4),
(3, 4, 3),
(5, 3, 3);

-- 9. Projects
INSERT INTO projects (id, employer_id, title, description, pricing_type, budget, status) VALUES
(1, 2, 'طراحی بک‌اند فریلنسری', 'پیاده‌سازی پایگاه داده و API', 'FIXED_PRICE', 20000000, 'OPEN'),
(2, 4, 'پردازش متن فارسی', 'تحلیل متن با پایتون', 'HOURLY', 400000, 'OPEN'),
(3, 4, 'اپلیکیشن موبایل', 'پروژه پیش‌نویس', 'FIXED_PRICE', 15000000, 'DRAFT');

SELECT setval('projects_id_seq', (SELECT MAX(id) FROM projects));

-- 10. Project Categories
INSERT INTO project_categories (project_id, category_id) VALUES
(1, 1),
(2, 3),
(3, 2);

-- 11. Project Skills
INSERT INTO project_skills (project_id, skill_id, is_required) VALUES
(1, 1, TRUE),
(1, 2, TRUE),
(1, 4, TRUE),
(2, 1, TRUE),
(3, 3, TRUE);

-- 12. Proposals (حداقل ۴ پیشنهاد معتبر)
INSERT INTO proposals (project_id, freelancer_id, bid_amount, estimated_duration, cover_letter, status) VALUES
(1, 3, 19000000, 20, 'تسلط کامل به جنگو و دیتابیس دارم و پروژه را سریع تحویل می‌دهم.', 'PENDING'),
(1, 5, 19500000, 25, 'آماده پیاده‌سازی و همکاری با کیفیت بالا.', 'PENDING'),
(2, 2, 380000, 50, 'سابقه تحلیل داده با پایتون دارم و آماده همکاری هستم.', 'PENDING'),
(2, 3, 400000, 40, 'تسلط به پایتون دارم و پروژه را با کیفیت انجام می‌دهم.', 'PENDING');

-- Accept proposal 1 (triggers project status to IN_PROGRESS)
UPDATE proposals
SET status = 'ACCEPTED'
WHERE id = 1;
