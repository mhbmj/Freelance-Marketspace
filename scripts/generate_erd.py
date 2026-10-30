import pygame
import os

# Initialize Pygame
pygame.init()
pygame.font.init()

WIDTH = 2200
HEIGHT = 1450
surface = pygame.Surface((WIDTH, HEIGHT))

# Color Palette (Tailwind Slate & Emerald / Modern Professional)
BG_COLOR = (248, 250, 252)        # Slate 50
HEADER_BG = (15, 23, 42)          # Slate 900
CARD_BG = (255, 255, 255)         # White
BORDER_COLOR = (203, 213, 225)    # Slate 300
TEXT_MAIN = (15, 23, 42)          # Slate 900
TEXT_MUTED = (100, 116, 139)      # Slate 500
PK_COLOR = (217, 119, 6)          # Amber 600
FK_COLOR = (37, 99, 235)          # Blue 600
PFK_COLOR = (220, 38, 38)         # Red 600 (PK, FK)
LINE_COLOR = (71, 85, 105)        # Slate 600

surface.fill(BG_COLOR)

# Fonts
font_title = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 28, bold=True)
font_subtitle = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 15)
font_tbl_header = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 15, bold=True)
font_col_name = pygame.font.SysFont("Consolas, Segoe UI, Arial", 13, bold=True)
font_col_type = pygame.font.SysFont("Consolas, Segoe UI, Arial", 12)
font_badge = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 11, bold=True)
font_line_label = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 11, bold=True)
font_legend_title = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 15, bold=True)
font_legend_text = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13)

# 1. Header Banner
banner_rect = pygame.Rect(40, 25, WIDTH - 80, 80)
pygame.draw.rect(surface, HEADER_BG, banner_rect, border_radius=10)

title_surf = font_title.render("Freelance Marketplace - Entity Relationship Diagram (ERD)", True, (255, 255, 255))
sub_surf = font_subtitle.render("DBMS: PostgreSQL 14+ | Course: Software Engineering Lab | Author: Mahtab Moravej (Team Mahtab)", True, (148, 163, 184))
surface.blit(title_surf, (65, 38))
surface.blit(sub_surf, (67, 74))

# Table definitions
tables = {
    # Column 1 (Left): Users and User Roles
    "users": {
        "rect": (50, 130, 310, 320),
        "header_color": (30, 58, 138), # Deep Blue
        "columns": [
            ("id", "SERIAL", "PK"),
            ("first_name", "VARCHAR(100)", ""),
            ("last_name", "VARCHAR(100)", ""),
            ("email", "VARCHAR(255) UQ", ""),
            ("phone_number", "VARCHAR(20)", ""),
            ("password_hash", "VARCHAR(255)", ""),
            ("status", "VARCHAR(20)", ""),
            ("is_deleted", "BOOLEAN", ""),
            ("created_at", "TIMESTAMPTZ", ""),
            ("updated_at", "TIMESTAMPTZ", "")
        ]
    },
    "admins": {
        "rect": (50, 480, 310, 160),
        "header_color": (159, 18, 57), # Crimson
        "columns": [
            ("user_id", "INT", "PK,FK"),
            ("role_title", "VARCHAR(100)", ""),
            ("granted_at", "TIMESTAMPTZ", ""),
            ("granted_by", "INT", "FK")
        ]
    },
    "user_profiles": {
        "rect": (50, 670, 310, 190),
        "header_color": (13, 148, 136), # Teal
        "columns": [
            ("user_id", "INT", "PK,FK"),
            ("professional_title", "VARCHAR(150)", ""),
            ("bio", "TEXT", ""),
            ("location", "VARCHAR(150)", ""),
            ("created_at", "TIMESTAMPTZ", ""),
            ("updated_at", "TIMESTAMPTZ", "")
        ]
    },

    # Column 2: User Portfolios, Certificates & User Skills
    "user_skills": {
        "rect": (410, 130, 290, 160),
        "header_color": (99, 102, 241), # Indigo
        "columns": [
            ("user_id", "INT", "PK,FK"),
            ("skill_id", "INT", "PK,FK"),
            ("years_of_experience", "INT", ""),
            ("created_at", "TIMESTAMPTZ", "")
        ]
    },
    "portfolios": {
        "rect": (410, 330, 290, 190),
        "header_color": (109, 40, 217), # Purple
        "columns": [
            ("id", "SERIAL", "PK"),
            ("user_id", "INT", "FK"),
            ("title", "VARCHAR(200)", ""),
            ("description", "TEXT", ""),
            ("project_url", "VARCHAR(500)", ""),
            ("created_at", "TIMESTAMPTZ", "")
        ]
    },
    "certificates": {
        "rect": (410, 560, 290, 230),
        "header_color": (194, 65, 12), # Orange
        "columns": [
            ("id", "SERIAL", "PK"),
            ("user_id", "INT", "FK"),
            ("title", "VARCHAR(200)", ""),
            ("issuing_organization", "VARCHAR(200)", ""),
            ("issue_date", "DATE", ""),
            ("credential_url", "VARCHAR(500)", ""),
            ("credential_id", "VARCHAR(100)", ""),
            ("created_at", "TIMESTAMPTZ", "")
        ]
    },

    # Column 3: Central Core (Projects & Proposals)
    "projects": {
        "rect": (750, 280, 340, 330),
        "header_color": (30, 41, 59), # Slate Dark
        "columns": [
            ("id", "SERIAL", "PK"),
            ("employer_id", "INT", "FK"),
            ("title", "VARCHAR(255)", ""),
            ("description", "TEXT", ""),
            ("pricing_type", "VARCHAR(20)", ""),
            ("budget", "NUMERIC(12,2)", ""),
            ("deadline", "TIMESTAMPTZ", ""),
            ("status", "VARCHAR(20)", ""),
            ("is_deleted", "BOOLEAN", ""),
            ("created_at", "TIMESTAMPTZ", ""),
            ("updated_at", "TIMESTAMPTZ", "")
        ]
    },
    "proposals": {
        "rect": (750, 680, 340, 270),
        "header_color": (180, 83, 9), # Amber
        "columns": [
            ("id", "SERIAL", "PK"),
            ("project_id", "INT", "FK"),
            ("freelancer_id", "INT", "FK"),
            ("bid_amount", "NUMERIC(12,2)", ""),
            ("estimated_duration", "INT", ""),
            ("cover_letter", "TEXT", ""),
            ("status", "VARCHAR(20)", ""),
            ("created_at", "TIMESTAMPTZ", ""),
            ("updated_at", "TIMESTAMPTZ", "")
        ]
    },

    # Column 4 & 5 (Right): Skills, Categories, and Junction Tables
    "skills": {
        "rect": (1150, 130, 280, 160),
        "header_color": (2, 132, 199), # Sky
        "columns": [
            ("id", "SERIAL", "PK"),
            ("name", "VARCHAR(100) UQ", ""),
            ("description", "TEXT", ""),
            ("created_at", "TIMESTAMPTZ", "")
        ]
    },
    "categories": {
        "rect": (1480, 130, 280, 160),
        "header_color": (5, 150, 105), # Emerald
        "columns": [
            ("id", "SERIAL", "PK"),
            ("name", "VARCHAR(100) UQ", ""),
            ("description", "TEXT", ""),
            ("created_at", "TIMESTAMPTZ", "")
        ]
    },
    "project_skills": {
        "rect": (1150, 360, 280, 160),
        "header_color": (14, 165, 233), # Cyan
        "columns": [
            ("project_id", "INT", "PK,FK"),
            ("skill_id", "INT", "PK,FK"),
            ("is_required", "BOOLEAN", ""),
            ("created_at", "TIMESTAMPTZ", "")
        ]
    },
    "project_categories": {
        "rect": (1480, 360, 280, 150),
        "header_color": (16, 185, 129), # Green
        "columns": [
            ("project_id", "INT", "PK,FK"),
            ("category_id", "INT", "PK,FK"),
            ("created_at", "TIMESTAMPTZ", "")
        ]
    }
}

def draw_table(info, name):
    x, y, w, h = info["rect"]
    hdr_color = info["header_color"]
    cols = info["columns"]

    # Subtle drop shadow
    shadow_rect = pygame.Rect(x + 3, y + 3, w, h)
    pygame.draw.rect(surface, (226, 232, 240), shadow_rect, border_radius=8)
    card_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, CARD_BG, card_rect, border_radius=8)
    pygame.draw.rect(surface, BORDER_COLOR, card_rect, width=1, border_radius=8)

    # Header
    hdr_rect = pygame.Rect(x, y, w, 32)
    pygame.draw.rect(surface, hdr_color, hdr_rect, border_top_left_radius=8, border_top_right_radius=8)
    tbl_name_txt = font_tbl_header.render(name, True, (255, 255, 255))
    surface.blit(tbl_name_txt, (x + 12, y + 6))

    # Rows
    cur_y = y + 40
    for cname, ctype, key in cols:
        # Key Badge
        if key == "PK,FK":
            badge = font_badge.render("PK,FK", True, PFK_COLOR)
            surface.blit(badge, (x + 8, cur_y))
        elif key == "PK":
            badge = font_badge.render("PK", True, PK_COLOR)
            surface.blit(badge, (x + 8, cur_y))
        elif key == "FK":
            badge = font_badge.render("FK", True, FK_COLOR)
            surface.blit(badge, (x + 8, cur_y))

        # Col Name
        cname_surf = font_col_name.render(cname, True, TEXT_MAIN)
        surface.blit(cname_surf, (x + 48, cur_y))

        # Col Type
        ctype_surf = font_col_type.render(ctype, True, TEXT_MUTED)
        surface.blit(ctype_surf, (x + w - ctype_surf.get_width() - 10, cur_y + 1))

        cur_y += 24

def draw_badge_label(text, center_pos, bg_color=(254, 240, 138), border_color=(202, 138, 4)):
    lbl = font_line_label.render(text, True, (30, 41, 59))
    bx, by = center_pos
    rect = pygame.Rect(bx - lbl.get_width()//2 - 5, by - 9, lbl.get_width() + 10, 18)
    pygame.draw.rect(surface, bg_color, rect, border_radius=4)
    pygame.draw.rect(surface, border_color, rect, width=1, border_radius=4)
    surface.blit(lbl, (bx - lbl.get_width()//2, by - 8))

def draw_polyline(points, label="", label_pos=None):
    for i in range(len(points) - 1):
        pygame.draw.line(surface, LINE_COLOR, points[i], points[i+1], 2)
    pygame.draw.circle(surface, FK_COLOR, points[0], 4)
    pygame.draw.circle(surface, PK_COLOR, points[-1], 4)
    if label and label_pos:
        draw_badge_label(label, label_pos)

# Draw all tables first
for tname, tinfo in tables.items():
    draw_table(tinfo, tname)

# 1. users -> admins (Vertical 1:0..1)
draw_polyline([(205, 450), (205, 480)], "1 : 0..1", (205, 465))

# 2. users -> user_profiles (Vertical 1:0..1)
draw_polyline([(70, 450), (35, 450), (35, 690), (50, 690)], "1 : 0..1", (35, 570))

# 3. users -> user_skills (1:N)
draw_polyline([(360, 180), (410, 180)], "1 : N", (385, 180))

# 4. users -> portfolios (1:N)
draw_polyline([(360, 360), (410, 360)], "1 : N", (385, 360))

# 5. users -> certificates (1:N)
draw_polyline([(360, 420), (385, 420), (385, 590), (410, 590)], "1 : N", (385, 500))

# 6. skills -> user_skills (1:N)
draw_polyline([(1150, 160), (700, 160)], "1 : N", (925, 160))

# 7. users -> projects (Employer 1:N)
draw_polyline([(360, 290), (750, 290)], "1 : N (Employer)", (555, 290))

# 8. projects -> proposals (1:N)
draw_polyline([(920, 610), (920, 680)], "1 : N", (920, 645))

# 9. users -> proposals (Freelancer 1:N)
draw_polyline([(205, 860), (205, 980), (750, 980), (750, 850)], "1 : N (Freelancer)", (477, 980))

# 10. projects -> project_skills (1:N)
draw_polyline([(1090, 420), (1150, 420)], "1 : N", (1120, 420))

# 11. skills -> project_skills (1:N)
draw_polyline([(1290, 290), (1290, 360)], "1 : N", (1290, 325))

# 12. projects -> project_categories (1:N)
draw_polyline([(1090, 470), (1120, 470), (1120, 550), (1620, 550), (1620, 510)], "1 : N", (1370, 550))

# 13. categories -> project_categories (1:N)
draw_polyline([(1620, 290), (1620, 360)], "1 : N", (1620, 325))


# Legend & Summary Box
leg_x, leg_y, leg_w, leg_h = 1150, 590, 610, 440
leg_rect = pygame.Rect(leg_x, leg_y, leg_w, leg_h)
pygame.draw.rect(surface, (226, 232, 240), pygame.Rect(leg_x+3, leg_y+3, leg_w, leg_h), border_radius=8)
pygame.draw.rect(surface, CARD_BG, leg_rect, border_radius=8)
pygame.draw.rect(surface, BORDER_COLOR, leg_rect, width=1, border_radius=8)

leg_hdr = pygame.Rect(leg_x, leg_y, leg_w, 34)
pygame.draw.rect(surface, HEADER_BG, leg_hdr, border_top_left_radius=8, border_top_right_radius=8)
leg_title = font_legend_title.render("Design Decisions & Business Integrity Rules", True, (255, 255, 255))
surface.blit(leg_title, (leg_x + 14, leg_y + 8))

rules = [
    ("[PK]", PK_COLOR, "Primary Key: Unique identifier for entity records"),
    ("[FK]", FK_COLOR, "Foreign Key: Referential integrity constraint across entities"),
    ("[PK,FK]", PFK_COLOR, "Composite Primary Key: Used in junction tables (M:N)"),
    ("Rule 6", (15, 23, 42), "Unique email, positive values: budget > 0, bid_amount > 0"),
    ("Rule 7", (15, 23, 42), "1 proposal per freelancer/project: UNIQUE(project_id, freelancer_id)"),
    ("Rule 7", (15, 23, 42), "At most 1 ACCEPTED proposal: Partial Unique Index ON (project_id)"),
    ("Rule 7", (15, 23, 42), "Employer self-bidding prohibited: Checked by BEFORE INSERT trigger"),
    ("Rule 7", (15, 23, 42), "Proposals allowed only on OPEN projects: Enforced by trigger"),
    ("Rule 7", (15, 23, 42), "On proposal acceptance: Project status auto-updates to IN_PROGRESS"),
    ("Rule 10", (15, 23, 42), "Admins restricted from bidding or creating projects (Trigger)"),
    ("Role Norm", (15, 23, 42), "Admin role isolated in admins table with granted_at timestamp")
]

cur_ry = leg_y + 46
for badge, col, text in rules:
    b_surf = font_badge.render(badge, True, col)
    surface.blit(b_surf, (leg_x + 14, cur_ry))
    t_surf = font_legend_text.render(text, True, TEXT_MAIN)
    surface.blit(t_surf, (leg_x + 85, cur_ry))
    cur_ry += 29

output_path = "docs/erd.png"
pygame.image.save(surface, output_path)
print(f"Final ERD saved successfully to {output_path} ({WIDTH}x{HEIGHT})")
