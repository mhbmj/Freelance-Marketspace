# مستند ساختار مدیریت پروژه در جیرا (Jira Project Backlog)
## پروژه: سامانه بازار کار فریلنسری (Freelance Marketplace)
**تیم:** مهتاب (Mahtab) | **درس:** آزمایشگاه مهندسی نرم‌افزار  

---

## ۱. اپیک‌ها (Epics)

### Epic 1: مدیریت کاربران، احراز هویت و پروفایل
* **Summary:** `User Management, Authentication & Profiles`
* **Description:** شامل کلیه نیازمندی‌ها و فرآیندهای ثبت‌نام، ورود با متدهای مختلف، تفکیک نقش کارفرما/فریلنسر و مدیریت پروفایل و پورتفولیو.

### Epic 2: چرخه حیات پروژه‌ها و مدیریت پیشنهادها
* **Summary:** `Project Lifecycle & Proposal Management`
* **Description:** شامل ثبت پروژه توسط کارفرما، دسته‌بندی و جستجوی پیشرفته توسط فریلنسرها، ارسال پروپوزال، بررسی پیشنهادها و انتخاب فریلنسر.

### Epic 3: پرداخت امن، قراردادها و ارزیابی
* **Summary:** `Escrow Payments, Contracting & Reviews`
* **Description:** ایجاد قرارداد، واریز وجه امانی در صندوق Escrow، پرداخت مرحله‌ای (Milestones)، آزادسازی وجه به فریلنسر و امتیازدهی دوطرفه.

---

## ۲. داستان‌های کاربر (User Stories)

### زیرمجموعه Epic 1:
1. **Story 1: ثبت‌نام با ایمیل یا پیامک و انتخاب نقش**
   * **Summary:** `User Registration & Role Selection`
   * **User Story:**
     > **As a** new user,  
     > **I want to** register using my email or phone number and choose whether I am a Client, Freelancer, or both,  
     > **So that** I can access the appropriate platform dashboard and tools.
   * **Acceptance Criteria:**
     - کاربر بتواند شماره موبایل یا ایمیل خود را وارد کند و کد تأیید دریافت نماید.
     - در فرم ثبت‌نام گزینه انتخاب نقش (Client / Freelancer) اجباری باشد.
     - رمز عبور باید حداقل ۸ کاراکتر و دارای پیچیدگی لازم باشد.
   * **Story Points:** 5

2. **Story 2: ساخت و ویرایش پروفایل و پورتفولیوی فریلنسر**
   * **Summary:** `Freelancer Profile & Portfolio Setup`
   * **User Story:**
     > **As a** freelancer,  
     > **I want to** add my title, bio, hourly rate, skills, and portfolio items,  
     > **So that** potential clients can evaluate my qualifications and past work.
   * **Acceptance Criteria:**
     - امکان افزودن حداقل ۵ مهارت از لیست پیش‌فرض یا تگ جدید.
     - امکان بارگذاری تصویر نمونه‌کار همراه با عنوان و توضیحات.
     - نمایش پیش‌نمایش عمومی پروفایل فریلنسر.
   * **Story Points:** 5

---

### زیرمجموعه Epic 2:
3. **Story 3: ثبت آگهی پروژه توسط کارفرما**
   * **Summary:** `Project Posting by Client`
   * **User Story:**
     > **As a** client,  
     > **I want to** create a new project post with title, description, skills, budget, and deadline,  
     > **So that** qualified freelancers can discover it and send proposals.
   * **Acceptance Criteria:**
     - فیلدهای عنوان، مهارت‌های مورد نیاز و محدوده بودجه اجباری باشند.
     - امکان ضمیمه کردن فایل راهنما (PDF/Word/ZIP تا سقف ۲۵ مگابایت).
     - ذخیره پیش‌نویس (Draft) قبل از انتشار نهایی.
   * **Story Points:** 5

4. **Story 4: جستجو و فیلتر پیشرفته پروژه‌ها**
   * **Summary:** `Advanced Project Search & Filtering`
   * **User Story:**
     > **As a** freelancer,  
     > **I want to** search projects by keywords and filter by skill, budget range, and recency,  
     > **So that** I can quickly find opportunities matching my expertise.
   * **Acceptance Criteria:**
     - فیلتر بر اساس تگ مهارت‌ها به صورت چندانتخابی.
     - فیلتر بر اساس بازه حداقل و حداکثر بودجه.
     - مرتب‌سازی بر اساس جدیدترین، بیشترین بودجه و کمترین تعداد پیشنهاد.
   * **Story Points:** 3

5. **Story 5: ارسال پیشنهاد همکاری (Proposal) توسط فریلنسر**
   * **Summary:** `Proposal Submission with Cover Letter`
   * **User Story:**
     > **As a** freelancer,  
     > **I want to** submit a proposal with my bid amount, delivery time, and cover letter,  
     > **So that** the client can consider me for the project.
   * **Acceptance Criteria:**
     - فریلنسر نتواند برای یک پروژه بیش از یک پیشنهاد فعال ارسال کند.
     - مبلغ پیشنهادی و زمان تخمینی باید اعتبارسنجی شوند (اعداد مثبت).
     - امکان الصاق نمونه‌کارهای مرتبط از پروفایل به پروپوزال.
   * **Story Points:** 5

6. **Story 6: بررسی، مقایسه و پذیرش پیشنهاد توسط کارفرما**
   * **Summary:** `Proposal Review and Freelancer Hiring`
   * **User Story:**
     > **As a** client,  
     > **I want to** view a list of received proposals, compare bids, and accept the best one,  
     > **So that** a formal contract is generated with the selected freelancer.
   * **Acceptance Criteria:**
     - نمایش لیست کامل فریلنسرهای متقاضی همراه با رتبه و قیمت پیشنهادی.
     - امکان رد پیشنهاد (Decline) با ارسال پیام خودکار مؤدبانه.
     - پذیرش پیشنهاد منجر به تغییر وضعیت پروژه به مرحله ایجاد قرارداد شود.
   * **Story Points:** 5

---

### زیرمجموعه Epic 3:
7. **Story 7: پرداخت امن و قفل وجه در صندوق Escrow**
   * **Summary:** `Escrow Milestone Funding`
   * **User Story:**
     > **As a** client,  
     > **I want to** deposit the milestone payment into a secure platform escrow account,  
     > **So that** the freelancer can start working with financial peace of mind.
   * **Acceptance Criteria:**
     - اتصال به درگاه پرداخت اینترنتی و شارژ حساب امانی پروژه.
     - ثبت رکورد مالی با شناسه رهگیری یکتا و تغییر وضعیت مایلستون به «تأمین مالی‌شده (Funded)».
     - ارسال نوتیفیکیشن فوری به فریلنسر مبنی بر مجاز بودن شروع کار.
   * **Story Points:** 8

8. **Story 8: آزادسازی وجه مایلستون و ثبت بازخورد دوطرفه**
   * **Summary:** `Milestone Release & Double-Blind Review`
   * **User Story:**
     > **As a** user (client or freelancer),  
     > **I want to** release completed milestone payments and exchange ratings/reviews,  
     > **So that** the financial cycle closes and our public reputation updates.
   * **Acceptance Criteria:**
     - کارفرما بتواند پس از بازبینی خروجی، دکمه «تأیید و آزادسازی وجه» را کلیک کند.
     - سیستم کارمزد پلتفرم را کسر کرده و خالص مبلغ را به کیف پول فریلنسر اضافه کند.
     - فرم امتیازدهی ۱ تا ۵ ستاره همراه با متن نظر فعال شود.
   * **Story Points:** 8

---

## ۳. وظایف فنی (Tasks)

1. **Task 1: راه‌اندازی ساختار بک‌اند جنگو و اتصال به PostgreSQL**
   * **Summary:** `Setup Django Architecture & PostgreSQL Database Connection`
   * **Description:** ساخت پروژه Django، ایجاد اپلیکیشن‌های اصلی (`accounts`, `projects`, `payments`) و اتصال تنظیمات پایگاه‌داده به دیتابیس `freelance_lab`.
   * **Component:** Backend / Database
   * **Status پیشنهادی روی برد:** `Done`

2. **Task 2: راه‌اندازی اولیه اپلیکیشن React و سیستم مسیریابی**
   * **Summary:** `Initialize React.js App with TailwindCSS and Router`
   * **Description:** ساخت اسکلت کلاینت با React و Vite، نصب پکیج‌های TailwindCSS و React Router و ساخت صفحات پایه داشبورد کارفرما و فریلنسر.
   * **Component:** Frontend
   * **Status پیشنهادی روی برد:** `In Progress`

3. **Task 3: پیکربندی مخزن گیت و ایجاد ساختار مستندات نیازمندی‌ها**
   * **Summary:** `Configure Git Workflow & Document Requirements Specification`
   * **Description:** تنظیم ریپازیتوری `freelance-marketplace`، مستندسازی نیازمندی‌های عملکردی و غیرعملکردی در `docs/requirements.md` و ادغام Pull Request.
   * **Component:** DevOps / Documentation
   * **Status پیشنهادی روی برد:** `Done`

---

## ۴. اسپرینت ۲: فاز طراحی و پیاده‌سازی پایگاه داده (Sprint 2: Database Design & Implementation)

این بخش منعکس‌کننده مراحل کامل انجام تکلیف دوم درس آزمایشگاه مهندسی نرم‌افزار در سیستم مدیریت پروژه جیرا (پروژه SCRUM) است:

### Task 4: مدل‌سازی مفهومی، منطقی و تدوین نمودار ERD
* **Issue Key در جیرا:** `SCRUM-20`
* **Summary:** `Task 4: ERD Design & Relational Data Modeling`
* **Description:** تحلیل کامل نیازمندی‌های داده‌ای، موجودیت‌ها (کاربران، مدیران، پروفایل‌ها، پروژه‌ها، پیشنهادها، مهارت‌ها و دسته‌بندی‌ها)، تعیین کاردینالیتی روابط و رسم نمودار استاندارد ERD.
* **Component:** Database / Architecture
* **Linked Stories:** `SCRUM-8`, `SCRUM-9`, `SCRUM-10`, `SCRUM-12`
* **Status در جیرا:** `Done`
* **Sub-tasks:**
  - `SCRUM-21`: Analyze Entities, Attributes, and Primary/Foreign Keys
  - `SCRUM-22`: Model M:N Junction Tables (user_skills, project_skills, project_categories)
  - `SCRUM-23`: Generate High-Resolution ERD Diagram (docs/erd.png & docs/erd.puml)

### Task 5: پیاده‌سازی اسکریپت DDL و ساختار جداول پایگاه داده در PostgreSQL
* **Issue Key در جیرا:** `SCRUM-24`
* **Summary:** `Task 5: PostgreSQL DDL Schema & Table Constraints Definition`
* **Description:** نگارش اسکریپت `database/schema.sql` جهت ساخت تمیز جداول، انواع داده دقیق، محدودیت‌های کلید اصلی/خارجی، رفتار ON DELETE، محدودیت‌های CHECK و ایندکس‌ها.
* **Component:** Database / Backend
* **Linked Stories:** `SCRUM-8`, `SCRUM-10`, `SCRUM-12`
* **Status در جیرا:** `Done`
* **Sub-tasks:**
  - `SCRUM-25`: Create Users, Admins, and Profiles Tables
  - `SCRUM-26`: Create Projects and Categories/Skills Tables
  - `SCRUM-27`: Create Proposals Table with Unique Constraints

### Task 6: اتوماسیون قواعد کسب‌وکار و یکپارچگی داده با Triggerها
* **Issue Key در جیرا:** `SCRUM-28`
* **Summary:** `Task 6: Database Business Rules Enforcement & Trigger Automation`
* **Description:** پیاده‌سازی قواعد کسب‌وکار پلتفرم (یکتایی پیشنهاد پذیرفته‌شده با ایندکس شرطی، تریگر بررسی وضعیت OPEN و منع پیشنهاد کارفرما روی پروژه خود، و تریگر تغییر وضعیت پروژه).
* **Component:** Database / Business Logic
* **Linked Stories:** `SCRUM-12`, `SCRUM-13`
* **Status در جیرا:** `Done`
* **Sub-tasks:**
  - `SCRUM-29`: Enforce Single Accepted Proposal via Partial Unique Index
  - `SCRUM-30`: Implement Proposal Validation Trigger (Open status & Self-bid check)
  - `SCRUM-31`: Implement Project Status Update Trigger on Proposal Acceptance

### Task 7: تولید داده‌های اولیه غنی و آزمایشی (Seed Data)
* **Issue Key در جیرا:** `SCRUM-32`
* **Summary:** `Task 7: Seed Data Generation for Development & Simulation`
* **Description:** تدوین فایل `database/seed.sql` منطبق با شرایط سناریوی عملیاتی پلتفرم شامل ۴ کاربر، دسته‌بندی‌ها، مهارت‌ها، پروژه‌ها و پیشنهادها.
* **Component:** Database / QA
* **Linked Stories:** `SCRUM-8`, `SCRUM-10`, `SCRUM-12`
* **Status در جیرا:** `Done`
* **Sub-tasks:**
  - `SCRUM-33`: Insert Users, Admin, Profiles, Portfolios, and Certificates
  - `SCRUM-34`: Insert Categories, Skills, and Projects in Various Statuses
  - `SCRUM-35`: Insert Proposals and Simulate Proposal Acceptance

### Task 8: پیاده‌سازی کوئری‌های تحلیلی و عملیاتی پایگاه داده
* **Issue Key در جیرا:** `SCRUM-36`
* **Summary:** `Task 8: Core Operational and Reporting SQL Queries Development`
* **Description:** نگارش و بهینه‌سازی ۴ کوئری اصلی خواسته شده در صورت تمرین در فایل `database/queries.sql`.
* **Component:** Database / Query Optimization
* **Linked Stories:** `SCRUM-10`, `SCRUM-11`, `SCRUM-12`, `SCRUM-13`
* **Status در جیرا:** `Done`
* **Sub-tasks:**
  - `SCRUM-37`: Implement Open Projects Query with Employer and Category
  - `SCRUM-38`: Implement Project Proposals Query with Freelancer Details
  - `SCRUM-39`: Implement Employer Projects & Proposals Aggregation Query
  - `SCRUM-40`: Implement Required Skills per Project Query

### Task 9: طراحی اسکریپت آزمون اعتبارسنجی محدودیت‌ها (Constraints Test Suite)
* **Issue Key در جیرا:** `SCRUM-41`
* **Summary:** `Task 9: Automated Database Constraints and Rules Verification Script`
* **Description:** تدوین سناریوهای آزمون اعتبارسنجی محدودیت‌ها (رد مقادیر منفی، ایمیل تکراری، پیشنهاد دوم، و ...) در فایل `database/tests.sql`.
* **Component:** Database / QA & Verification
* **Linked Stories:** `SCRUM-8`, `SCRUM-10`, `SCRUM-12`, `SCRUM-13`
* **Status در جیرا:** `Done`
* **Sub-tasks:**
  - `SCRUM-42`: Formulate Negative Constraint Test Cases (Email, Budget, Foreign Key)
  - `SCRUM-43`: Formulate Business Rule Test Cases (Self-bid, Duplicate Proposal)
  - `SCRUM-44`: Formulate Positive Test Case for Project Status Lifecycle

