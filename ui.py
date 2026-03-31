import pygame
from settings import *
from hex_map import get_hex_center, TERRAIN_TYPES, campaign_levels

# ==========================================
# تهيئة خطوط الواجهة (UI Fonts)
# ==========================================
pygame.init()
font_large = pygame.font.Font(None, 48)
font_medium = pygame.font.Font(None, 32)
font_small = pygame.font.Font(None, 24)
font_mini = pygame.font.Font(None, 20)

# ==========================================
# 1. شاشة اختيار المرحلة (Level Selection)
# ==========================================
def draw_level_selection(surface, current_selection):
    """رسم شاشة اختيار المهمة قبل بدء اللعب"""
    surface.fill(BLACK)
    
    title = font_large.render("CAMPAIGN: SELECT MISSION", True, WHITE)
    surface.blit(title, (WIDTH//2 - title.get_width()//2, 100))
    
    level_data = campaign_levels[current_selection]
    
    lvl_text = font_medium.render(f"< Mission {current_selection} / 100 >", True, HIGHLIGHT)
    surface.blit(lvl_text, (WIDTH//2 - lvl_text.get_width()//2, 300))
    
    name_text = font_large.render(level_data["name"], True, BORDER_COLOR)
    surface.blit(name_text, (WIDTH//2 - name_text.get_width()//2, 350))
    
    info_text = font_medium.render(f"Map Size: {level_data['cols']}x{level_data['rows']}", True, WHITE)
    surface.blit(info_text, (WIDTH//2 - info_text.get_width()//2, 420))
    
    hint_text = font_medium.render("Press [LEFT]/[RIGHT] to select | [ENTER] to Deploy", True, (150, 150, 150))
    surface.blit(hint_text, (WIDTH//2 - hint_text.get_width()//2, 600))

# ==========================================
# 2. قائمة الأوامر التكتيكية (Command Menu)
# ==========================================
def draw_command_menu(surface, mecha, cam_x, cam_y):
    """رسم القائمة المنبثقة بجوار الآلي عند النقر عليه"""
    cx, cy = get_hex_center(mecha.row, mecha.col, cam_x, cam_y)
    menu_x = cx + 25
    menu_y = cy - 60
    
    # تحديد الخيارات المتاحة بناءً على ما فعله الآلي في هذا الدور
    options = []
    if not mecha.moved_this_turn:
        options.append("MOVE")
    if not mecha.attacked_this_turn:
        options.append("ATTACK")
    options.append("WAIT")
    options.append("CANCEL")

    # رسم خلفية وإطار القائمة
    menu_rect = pygame.Rect(menu_x, menu_y, 110, len(options) * 30 + 10)
    pygame.draw.rect(surface, MENU_BG, menu_rect)
    pygame.draw.rect(surface, BORDER_COLOR, menu_rect, 2)
    
    # رسم الأزرار
    buttons = {}
    for i, opt in enumerate(options):
        btn_rect = pygame.Rect(menu_x + 5, menu_y + 5 + (i * 30), 100, 25)
        pygame.draw.rect(surface, HIGHLIGHT, btn_rect, 1)
        
        text = font_small.render(opt, True, HIGHLIGHT)
        surface.blit(text, (btn_rect.x + 5, btn_rect.y + 5))
        
        buttons[opt] = btn_rect
        
    return buttons

# ==========================================
# 3. الشريط السفلي للمعلومات (Bottom HUD)
# ==========================================
def draw_bottom_hud(surface, mecha):
    """رسم الشريط الذي يظهر بيانات الآلي المحدد أو المفحوص"""
    if not mecha:
        return
        
    hud_height = 120
    hud_rect = pygame.Rect(0, HEIGHT - hud_height, WIDTH, hud_height)
    
    # الخلفية والخط الفاصل
    pygame.draw.rect(surface, HUD_BG, hud_rect)
    pygame.draw.line(surface, BORDER_COLOR, (0, HEIGHT - hud_height), (WIDTH, HEIGHT - hud_height), 3)
    
    color = PLAYER_COLOR if mecha.faction == "Player" else ENEMY_COLOR
    
    # الاسم ونقاط الصحة وشريط الصحة الكبير
    name_txt = font_medium.render(mecha.name, True, color)
    surface.blit(name_txt, (30, HEIGHT - 100))
    
    hp_txt = font_small.render(f"HP: {mecha.hp} / {mecha.max_hp}", True, WHITE)
    surface.blit(hp_txt, (30, HEIGHT - 65))
    
    health_ratio = max(0, mecha.hp / mecha.max_hp)
    pygame.draw.rect(surface, (100, 0, 0), (30, HEIGHT - 40, 200, 15))
    pygame.draw.rect(surface, (0, 200, 0), (30, HEIGHT - 40, 200 * health_ratio, 15))
    pygame.draw.rect(surface, WHITE, (30, HEIGHT - 40, 200, 15), 1)

    # الإحصائيات (الهجوم، الدفاع، الحركة، النطاق)
    stats_x = 300
    surface.blit(font_small.render(f"ATK: {mecha.attack_power}", True, HIGHLIGHT), (stats_x, HEIGHT - 90))
    surface.blit(font_small.render(f"DEF: {mecha.defense}", True, HIGHLIGHT), (stats_x, HEIGHT - 60))
    surface.blit(font_small.render(f"MOVE: {mecha.max_move}", True, WHITE), (stats_x + 100, HEIGHT - 90))
    surface.blit(font_small.render(f"RANGE: {mecha.attack_range}", True, WHITE), (stats_x + 100, HEIGHT - 60))

    # معلومات تكتيكية متقدمة (النوع، الضعف، الحصانة)
    type_x = 600
    surface.blit(font_small.render(f"Type: {mecha.attack_type}", True, WHITE), (type_x, HEIGHT - 90))
    surface.blit(font_small.render(f"Weakness: {mecha.weakness}", True, (255, 100, 100)), (type_x, HEIGHT - 60))
    
    immune_str = mecha.immunity if mecha.immunity else "None"
    surface.blit(font_small.render(f"Immune to: {immune_str}", True, (100, 255, 100)), (type_x, HEIGHT - 30))

    # تلميح للدليل
    hint_txt = font_mini.render("Right-Click on unit for Tactical Guide", True, (150, 150, 150))
    surface.blit(hint_txt, (WIDTH - 250, HEIGHT - 30))

# ==========================================
# 4. صندوق معلومات التضاريس (Terrain Info Box)
# ==========================================
def draw_terrain_info(surface, hovered_hex, terrain_grid):
    """رسم مربع صغير يوضح نوع التضاريس التي يمر فوقها الماوس وتأثيرها"""
    if not hovered_hex:
        return
        
    t_type = terrain_grid.get(hovered_hex, "Void")
    t_data = TERRAIN_TYPES[t_type]
    
    # مربع المعلومات في أعلى اليمين
    box_rect = pygame.Rect(WIDTH - 220, HEIGHT - 220, 200, 90)
    pygame.draw.rect(surface, HUD_BG, box_rect)
    pygame.draw.rect(surface, BORDER_COLOR, box_rect, 2)
    
    # اسم التضاريس
    surface.blit(font_small.render(f"Terrain: {t_data['name']}", True, HIGHLIGHT), (box_rect.x + 10, box_rect.y + 10))
    
    # تكلفة الحركة
    cost_str = "Impassable" if t_data["cost"] > 90 else str(t_data["cost"])
    surface.blit(font_mini.render(f"Move Cost: {cost_str}", True, WHITE), (box_rect.x + 10, box_rect.y + 40))
    
    # مكافأة الدفاع
    def_bonus = t_data["def_bonus"]
    def_str = f"Defense: {'+' if def_bonus > 0 else ''}{def_bonus}"
    def_color = (100, 255, 100) if def_bonus > 0 else ((255, 100, 100) if def_bonus < 0 else WHITE)
    
    surface.blit(font_mini.render(def_str, True, def_color), (box_rect.x + 10, box_rect.y + 65))

# ==========================================
# 5. الدليل الموسوعي (Tactical Guide / Encyclopedia)
# ==========================================
def draw_guide_overlay(surface, mecha):
    """رسم شاشة الدليل الشفافة عند النقر بالزر الأيمن على الآلي"""
    # خلفية شفافة
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(GUIDE_BG)
    surface.blit(overlay, (0, 0))
    
    # مربع الدليل المركزي
    box_w = 600
    box_h = 450
    box_x = (WIDTH - box_w) // 2
    box_y = (HEIGHT - box_h) // 2
    box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
    
    pygame.draw.rect(surface, BLACK, box_rect)
    pygame.draw.rect(surface, BORDER_COLOR, box_rect, 3)
    
    # العنوان
    color = PLAYER_COLOR if mecha.faction == "Player" else ENEMY_COLOR
    title = font_large.render(f"ENCYCLOPEDIA: {mecha.name}", True, color)
    surface.blit(title, (box_x + 20, box_y + 20))
    pygame.draw.line(surface, BORDER_COLOR, (box_x + 20, box_y + 70), (box_x + box_w - 20, box_y + 70), 2)
    
    # النص الوصفي (القصة/Lore) - مقسم لأسطر لتجنب تجاوز الحواف
    desc_words = mecha.description.split(" ")
    lines = []
    current_line = ""
    for word in desc_words:
        if font_small.size(current_line + word)[0] < box_w - 40:
            current_line += word + " "
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)
    
    y_offset = box_y + 90
    for line in lines:
        surface.blit(font_small.render(line, True, WHITE), (box_x + 20, y_offset))
        y_offset += 30

    # التحليل التكتيكي
    y_offset += 20
    surface.blit(font_medium.render("Tactical Analysis:", True, HIGHLIGHT), (box_x + 20, y_offset))
    y_offset += 40
    
    immune_str = mecha.immunity if mecha.immunity else 'None'
    info = [
        f"- Combat Class: {mecha.attack_type}",
        f"- Critical Weakness: Vulnerable to {mecha.weakness}. Takes 1.5x damage.",
        f"- Defensive Plating: Absorbs {mecha.defense} damage.",
        f"- Immunity: {immune_str}."
    ]
    
    for item in info:
        surface.blit(font_small.render(item, True, (200, 200, 200)), (box_x + 30, y_offset))
        y_offset += 30
        
    close_txt = font_small.render("Click anywhere or press [ESC] to close", True, (150, 150, 150))
    surface.blit(close_txt, (box_x + box_w // 2 - 150, box_y + box_h - 40))