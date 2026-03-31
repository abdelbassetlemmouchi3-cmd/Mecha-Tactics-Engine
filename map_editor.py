import pygame
import sys
import json
import os
from settings import *
from hex_map import (
    get_hex_center, get_hex_vertices, get_hex_at_mouse, 
    initialize_terrain_textures, TERRAIN_TYPES
)
from mecha import load_level_units

# ==========================================
# إعدادات المحرر والدقة
# ==========================================
EDITOR_ROWS = 15
EDITOR_COLS = 20
TOOLBAR_HEIGHT = 140

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mecha Tactics - Professional Map Editor")

initialize_terrain_textures()
available_units = load_level_units() 

clock = pygame.time.Clock()

font_ui = pygame.font.Font(None, 24)
font_bold = pygame.font.Font(None, 28)
font_mini = pygame.font.Font(None, 20) 
font_large = pygame.font.Font(None, 48) # خط كبير لنافذة الحفظ

# ==========================================
# بيانات الخريطة
# ==========================================
map_terrain = {}
def populate_missing_terrain():
    for r in range(EDITOR_ROWS):
        for c in range(EDITOR_COLS):
            key = f"{r},{c}"
            if key not in map_terrain:
                map_terrain[key] = "Void"

populate_missing_terrain()
placed_units = []

current_brush_type = "Terrain"
current_brush_value = "Void"

cam_x, cam_y = 0, 0

# ==========================================
# نظام إدخال النصوص (لحفظ الخريطة باسم)
# ==========================================
is_typing_name = False
map_name_input = ""

# ==========================================
# واجهة المستخدم (UI Layout)
# ==========================================
PANEL_RECT = pygame.Rect(0, 0, 300, 250)
TOOLBAR_RECT = pygame.Rect(0, HEIGHT - TOOLBAR_HEIGHT, WIDTH, TOOLBAR_HEIGHT)

btn_row_add = pygame.Rect(10, 180, 110, 25)
btn_row_sub = pygame.Rect(130, 180, 110, 25)
btn_col_add = pygame.Rect(10, 210, 110, 25)
btn_col_sub = pygame.Rect(130, 210, 110, 25)

def get_toolbar_buttons():
    buttons = []
    x_start = 20
    y_top = HEIGHT - TOOLBAR_HEIGHT + 40
    
    for t_name, t_data in TERRAIN_TYPES.items():
        rect = pygame.Rect(x_start, y_top, 60, 70)
        buttons.append({"type": "Terrain", "value": t_name, "rect": rect, "img": t_data["texture"]})
        x_start += 80
        
    x_start += 40
    
    for unit in available_units:
        rect = pygame.Rect(x_start, y_top, 70, 70)
        buttons.append({"type": "Unit", "value": unit.name, "rect": rect, "img": unit.image})
        x_start += 90
        
    return buttons

toolbar_buttons = get_toolbar_buttons()

# ==========================================
# وظيفة الحفظ بالاسم الجديد
# ==========================================
def save_map(filename):
    data = {
        "metadata": {"rows": EDITOR_ROWS, "cols": EDITOR_COLS},
        "terrain": {},
        "units": []
    }
    for r in range(EDITOR_ROWS):
        for c in range(EDITOR_COLS):
            key = f"{r},{c}"
            data["terrain"][key] = map_terrain.get(key, "Void")
            
    for u in placed_units:
        if u['row'] < EDITOR_ROWS and u['col'] < EDITOR_COLS:
            data["units"].append({"name": u['name'], "faction": u['faction'], "row": u['row'], "col": u['col']})
    
    # التأكد من أن الامتداد هو .json
    if not filename.endswith(".json"):
        filename += ".json"
        
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Map Saved Successfully as {filename}!")

# ==========================================
# الحلقة الرئيسية
# ==========================================
while True:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        # -----------------------------------
        # التقاط أزرار الكيبورد أثناء كتابة اسم الخريطة
        # -----------------------------------
        if is_typing_name:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # إذا ضغط Enter وكان الحقل فارغاً، سمّه custom_map
                    final_name = map_name_input.strip() if map_name_input.strip() else "custom_map"
                    save_map(final_name)
                    is_typing_name = False
                    map_name_input = ""
                elif event.key == pygame.K_ESCAPE:
                    is_typing_name = False # إلغاء الحفظ
                    map_name_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    map_name_input = map_name_input[:-1]
                else:
                    # إضافة الحروف المكتوبة (إذا كانت ضمن الحروف الإنجليزية والأرقام)
                    if event.unicode.isprintable():
                        map_name_input += event.unicode
            continue # تخطي باقي الأوامر (لا يمكن الرسم أثناء الكتابة)

        # -----------------------------------
        # الأوامر الطبيعية (إذا لم نكن نكتب الاسم)
        # -----------------------------------
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if TOOLBAR_RECT.collidepoint(mouse_pos):
                    for btn in toolbar_buttons:
                        if btn["rect"].collidepoint(mouse_pos):
                            current_brush_type = btn["type"]
                            current_brush_value = btn["value"]
                            break
                elif btn_row_add.collidepoint(mouse_pos): EDITOR_ROWS += 1; populate_missing_terrain()
                elif btn_row_sub.collidepoint(mouse_pos): EDITOR_ROWS = max(5, EDITOR_ROWS - 1)
                elif btn_col_add.collidepoint(mouse_pos): EDITOR_COLS += 1; populate_missing_terrain()
                elif btn_col_sub.collidepoint(mouse_pos): EDITOR_COLS = max(5, EDITOR_COLS - 1)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                is_typing_name = True # تفعيل نافذة الكتابة

    # الرسم المستمر بالماوس (مغلق أثناء نافذة الكتابة)
    if not is_typing_name:
        if pygame.mouse.get_pressed()[0]:
            if not PANEL_RECT.collidepoint(mouse_pos) and not TOOLBAR_RECT.collidepoint(mouse_pos):
                hovered = get_hex_at_mouse(mouse_pos[0], mouse_pos[1], cam_x, cam_y, EDITOR_ROWS, EDITOR_COLS)
                if hovered:
                    r, c = hovered
                    if current_brush_type == "Terrain":
                        map_terrain[f"{r},{c}"] = current_brush_value
                    else:
                        placed_units = [u for u in placed_units if not (u['row'] == r and u['col'] == c)]
                        faction = "Player" if "Zain" in current_brush_value or "Naya" in current_brush_value else "Enemy"
                        placed_units.append({"name": current_brush_value, "faction": faction, "row": r, "col": c})

        if pygame.mouse.get_pressed()[2]:
            hovered = get_hex_at_mouse(mouse_pos[0], mouse_pos[1], cam_x, cam_y, EDITOR_ROWS, EDITOR_COLS)
            if hovered:
                placed_units = [u for u in placed_units if not (u['row'] == hovered[0] and u['col'] == hovered[1])]

        # حركة الكاميرا
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: cam_x += CAMERA_SPEED
        if keys[pygame.K_RIGHT]: cam_x -= CAMERA_SPEED
        if keys[pygame.K_UP]: cam_y += CAMERA_SPEED
        if keys[pygame.K_DOWN]: cam_y -= CAMERA_SPEED

    # ==========================================
    # الرسم (Rendering)
    # ==========================================
    screen.fill(BLACK)
    
    for r in range(EDITOR_ROWS):
        for c in range(EDITOR_COLS):
            cx, cy = get_hex_center(r, c, cam_x, cam_y)
            t_type = map_terrain.get(f"{r},{c}", "Void")
            texture = TERRAIN_TYPES[t_type]["texture"]
            if texture:
                screen.blit(texture, (int(cx - texture.get_width()//2), int(cy - texture.get_height()//2)))
            pygame.draw.polygon(screen, (60, 60, 80), get_hex_vertices(cx, cy, HEX_SIZE), 1)

    for u in placed_units:
        if u['row'] < EDITOR_ROWS and u['col'] < EDITOR_COLS:
            cx, cy = get_hex_center(u['row'], u['col'], cam_x, cam_y)
            for temp_u in available_units:
                if temp_u.name == u['name']:
                    rect = temp_u.image.get_rect(center=(int(cx), int(cy)))
                    screen.blit(temp_u.image, rect)
                    break

    pygame.draw.rect(screen, (30, 30, 45), PANEL_RECT)
    pygame.draw.rect(screen, WHITE, PANEL_RECT, 2)
    screen.blit(font_bold.render("CONTROLS", True, HIGHLIGHT), (10, 10))
    screen.blit(font_ui.render(f"Brush: {current_brush_value}", True, WHITE), (10, 40))
    screen.blit(font_ui.render("S: Save Map | R-Click: Erase", True, (200, 200, 200)), (10, 70))
    
    for btn, txt in [(btn_row_add, f"+ Row ({EDITOR_ROWS})"), (btn_row_sub, f"- Row ({EDITOR_ROWS})"),
                     (btn_col_add, f"+ Col ({EDITOR_COLS})"), (btn_col_sub, f"- Col ({EDITOR_COLS})")]:
        pygame.draw.rect(screen, (50, 50, 70), btn)
        pygame.draw.rect(screen, WHITE, btn, 1)
        screen.blit(font_mini.render(txt, True, WHITE), (btn.x + 10, btn.y + 5))

    pygame.draw.rect(screen, (20, 20, 30), TOOLBAR_RECT)
    pygame.draw.line(screen, HIGHLIGHT, (0, HEIGHT - TOOLBAR_HEIGHT), (WIDTH, HEIGHT - TOOLBAR_HEIGHT), 3)
    screen.blit(font_bold.render("ASSETS PALETTE (Terrains & Units)", True, HIGHLIGHT), (20, HEIGHT - TOOLBAR_HEIGHT + 10))

    for btn in toolbar_buttons:
        if current_brush_value == btn["value"]:
            pygame.draw.rect(screen, (60, 60, 100), btn["rect"])
            pygame.draw.rect(screen, WHITE, btn["rect"], 2)
        if btn["img"]:
            temp_img = pygame.transform.scale(btn["img"], (50, 50))
            img_rect = temp_img.get_rect(center=btn["rect"].center)
            screen.blit(temp_img, img_rect)
        txt = font_mini.render(btn["value"].split()[0], True, WHITE)
        screen.blit(txt, (btn["rect"].x + (btn["rect"].width//2 - txt.get_width()//2), btn["rect"].bottom + 2))

    # ==========================================
    # رسم نافذة إدخال الاسم (عند الضغط على S)
    # ==========================================
    if is_typing_name:
        # خلفية شفافة مظلمة
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # صندوق الكتابة
        box_w, box_h = 500, 200
        box_x, box_y = WIDTH//2 - box_w//2, HEIGHT//2 - box_h//2
        pygame.draw.rect(screen, (40, 40, 55), (box_x, box_y, box_w, box_h))
        pygame.draw.rect(screen, HIGHLIGHT, (box_x, box_y, box_w, box_h), 3)
        
        # النصوص
        title_txt = font_bold.render("Save Map As:", True, WHITE)
        screen.blit(title_txt, (box_x + 20, box_y + 20))
        
        hint_txt = font_mini.render("Type filename and press [ENTER]. Press [ESC] to cancel.", True, (180, 180, 180))
        screen.blit(hint_txt, (box_x + 20, box_y + 60))
        
        # حقل الإدخال
        input_rect = pygame.Rect(box_x + 20, box_y + 100, box_w - 40, 50)
        pygame.draw.rect(screen, (20, 20, 30), input_rect)
        pygame.draw.rect(screen, WHITE, input_rect, 2)
        
        name_txt = font_large.render(map_name_input + "_", True, HIGHLIGHT)
        screen.blit(name_txt, (input_rect.x + 10, input_rect.y + 10))

    pygame.display.flip()
    clock.tick(FPS)