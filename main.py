import pygame
import sys
import os
import json
import glob
import math
import random

# استيراد كل الوحدات التي قمنا ببرمجتها
from settings import *
from mecha import Mecha, load_level_units
from hex_map import (
    campaign_levels, get_hex_center, get_hex_vertices, 
    get_hex_at_mouse, hex_distance, get_reachable_hexes, 
    get_path, TERRAIN_TYPES, initialize_terrain_textures
)
from ui import (
    draw_level_selection, draw_command_menu, draw_bottom_hud, 
    draw_terrain_info, draw_guide_overlay
)
from combat import play_combat_animation

# ==========================================
# تهيئة محرك اللعبة والخطوط وفتح النافذة
# ==========================================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mecha Tactics - Earth Light Edition")

initialize_terrain_textures()

clock = pygame.time.Clock()
font_large = pygame.font.Font(None, 64) 
font_medium = pygame.font.Font(None, 32)
font_small = pygame.font.Font(None, 24)

# ==========================================
# قراءة الخرائط المخصصة من المحرر
# ==========================================
map_files = glob.glob("*.json")
campaign_levels.clear()

if not map_files:
    campaign_levels[1] = {"name": "No Maps Found! Please use map_editor.py", "rows": 10, "cols": 10, "file": None}
else:
    for i, f in enumerate(map_files):
        try:
            with open(f, 'r') as file:
                data = json.load(file)
                r = data.get("metadata", {}).get("rows", 10)
                c = data.get("metadata", {}).get("cols", 10)
            campaign_levels[i+1] = {"name": f.replace('.json', ''), "rows": r, "cols": c, "file": f}
        except:
            campaign_levels[i+1] = {"name": f"Error loading {f}", "rows": 10, "cols": 10, "file": None}

def load_custom_map(filename):
    with open(filename, "r") as f:
        data = json.load(f)
        
    rows = data["metadata"]["rows"]
    cols = data["metadata"]["cols"]
    
    terrain_grid = {}
    for key, t_type in data.get("terrain", {}).items():
        r, c = map(int, key.split(','))
        terrain_grid[(r, c)] = t_type
        
    units = []
    base_units = load_level_units() 
    
    for u_data in data.get("units", []):
        template = next((u for u in base_units if u.name == u_data["name"]), None)
        if template:
            new_unit = Mecha(
                template.name, u_data["row"], u_data["col"], u_data["faction"],
                template.max_hp, template.attack_power, template.defense,
                template.max_move, template.attack_range, template.attack_type,
                template.weakness, template.immunity, template.description,
                template.image_filename
            )
            units.append(new_unit)
            
    return terrain_grid, units, rows, cols

# تحميل الخلفية الفضائية
background_image = None
bg_path = os.path.join("assets", "backgrounds", "space_bg.png")
try:
    raw_bg = pygame.image.load(bg_path).convert()
    background_image = pygame.transform.scale(raw_bg, (WIDTH, HEIGHT))
except pygame.error as e:
    background_image = pygame.Surface((WIDTH, HEIGHT))
    background_image.fill(BLACK)

# ==========================================
# المتغيرات الرئيسية وحالة اللعبة
# ==========================================
game_state = "MAIN_MENU" 
game_result = "" 
tactical_state = "IDLE"  
selected_level = 1

units = []
terrain_grid = {}
active_menu_buttons = {}
current_reachable_hexes = {}

selected_unit = None
inspected_unit = None
guide_unit = None
hovered_hex = None

camera_x = 0
camera_y = 0
rows = 0
cols = 0

last_enemy_action_time = 0 
enemy_phase = 0
acting_enemy = None
enemy_target_hex = None
enemy_target_unit = None

running = True

# ==========================================
# حلقة اللعبة الرئيسية 
# ==========================================
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN:
            if game_state == "MAIN_MENU":
                if event.key == pygame.K_RIGHT: 
                    selected_level = min(len(campaign_levels), selected_level + 1)
                elif event.key == pygame.K_LEFT: 
                    selected_level = max(1, selected_level - 1)
                    
                elif event.key == pygame.K_RETURN:
                    map_filename = campaign_levels[selected_level]["file"]
                    if map_filename: 
                        game_state = "LEVEL_PLAYING"
                        game_result = ""
                        tactical_state = "IDLE"
                        terrain_grid, units, rows, cols = load_custom_map(map_filename)
                        inspected_unit = units[0] if units else None
                        camera_x = 0
                        camera_y = 0
                elif event.key == pygame.K_ESCAPE: 
                    running = False
            
            elif game_state == "LEVEL_PLAYING":
                if event.key == pygame.K_ESCAPE:
                    if tactical_state == "GUIDE": 
                        tactical_state = "IDLE"
                    else: 
                        game_state = "MAIN_MENU"
                        
            elif game_state == "GAME_OVER":
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    game_state = "MAIN_MENU"
                    tactical_state = "IDLE"

        # منع ضغطات الماوس أثناء تحرك اللاعب
        if event.type == pygame.MOUSEBUTTONDOWN and game_state == "LEVEL_PLAYING" and tactical_state != "ANIMATING_PLAYER_MOVE":
            if event.button == 3 and tactical_state not in ["GUIDE", "ENEMY_TURN"]: 
                if hovered_hex:
                    for u in units:
                        if (u.row, u.col) == hovered_hex:
                            guide_unit = u
                            tactical_state = "GUIDE"
                            break

            elif event.button == 1:
                if tactical_state == "GUIDE":
                    tactical_state = "IDLE"
                    continue
                
                if END_TURN_RECT.collidepoint(mouse_pos) and tactical_state != "ENEMY_TURN":
                    for u in units:
                        if u.faction == "Player": 
                            u.is_done = True
                    tactical_state = "ENEMY_TURN"
                    enemy_phase = 0
                    acting_enemy = None
                    last_enemy_action_time = pygame.time.get_ticks()
                    continue

                if mouse_pos[1] > HEIGHT - 120 or END_TURN_RECT.collidepoint(mouse_pos):
                    continue

                if tactical_state == "IDLE":
                    if hovered_hex:
                        clicked_on_unit = False
                        for u in units:
                            if (u.row, u.col) == hovered_hex:
                                inspected_unit = u
                                clicked_on_unit = True
                                if u.faction == "Player" and not u.is_done:
                                    selected_unit = u
                                    tactical_state = "TACTICAL_MENU"
                                break
                        if not clicked_on_unit: 
                            inspected_unit = None

                elif tactical_state == "TACTICAL_MENU":
                    action = None
                    clicked_in_menu = False
                    
                    # درع الحماية (Bounding Box) لمنع النفاذ
                    menu_bounding_rect = None
                    if active_menu_buttons:
                        rects = list(active_menu_buttons.values())
                        menu_bounding_rect = rects[0].unionall(rects).inflate(50, 50)
                    
                    for opt, rect in active_menu_buttons.items():
                        if rect.collidepoint(mouse_pos): 
                            action = opt
                            clicked_in_menu = True
                    
                    if action == "MOVE":
                        current_reachable_hexes = get_reachable_hexes(
                            selected_unit.row, selected_unit.col, selected_unit.max_move, 
                            terrain_grid, rows, cols, units
                        )
                        tactical_state = "TARGETING_MOVE"
                    elif action == "ATTACK":
                        tactical_state = "TARGETING_ATTACK"
                    elif action == "WAIT":
                        if selected_unit: 
                            selected_unit.is_done = True
                        tactical_state = "IDLE"
                        selected_unit = None
                    elif action == "CANCEL":
                        tactical_state = "IDLE"
                        selected_unit = None
                    elif not clicked_in_menu:
                        if menu_bounding_rect and not menu_bounding_rect.collidepoint(mouse_pos):
                            tactical_state = "IDLE"
                            selected_unit = None
                            if hovered_hex:
                                clicked_on_unit = False
                                for u in units:
                                    if (u.row, u.col) == hovered_hex:
                                        inspected_unit = u
                                        clicked_on_unit = True
                                        if u.faction == "Player" and not u.is_done:
                                            selected_unit = u
                                            tactical_state = "TACTICAL_MENU"
                                        break
                                if not clicked_on_unit: 
                                    inspected_unit = None

                elif tactical_state == "TARGETING_MOVE":
                    if hovered_hex and selected_unit:
                        if hovered_hex in current_reachable_hexes:
                            # 1. إيجاد المسار الانسيابي
                            path = get_path(selected_unit.row, selected_unit.col, hovered_hex[0], hovered_hex[1], terrain_grid, rows, cols, units)
                            # 2. بدء الأنيميشن
                            if path:
                                selected_unit.start_animation(path, get_hex_center)
                                tactical_state = "ANIMATING_PLAYER_MOVE"
                            else:
                                tactical_state = "TACTICAL_MENU"
                        else:
                            tactical_state = "TACTICAL_MENU"

                elif tactical_state == "TARGETING_ATTACK":
                    if hovered_hex and selected_unit:
                        if hex_distance(selected_unit.row, selected_unit.col, hovered_hex[0], hovered_hex[1]) <= selected_unit.attack_range:
                            for target in units:
                                if (target.row, target.col) == hovered_hex and target.faction != selected_unit.faction:
                                    target_terrain = terrain_grid.get(hovered_hex, "Void")
                                    play_combat_animation(screen, selected_unit, target, target_terrain)
                                    selected_unit.attacked_this_turn = True
                                    selected_unit.is_done = True 
                                    
                                    # منطق الفوز والخسارة للاعب
                                    if target.hp <= 0: 
                                        if "Base" in target.name:
                                            game_state = "GAME_OVER"
                                            game_result = "VICTORY" if target.faction == "Enemy" else "DEFEAT"
                                        units.remove(target)
                                        
                                        if not [u for u in units if u.faction == "Enemy"] and game_state != "GAME_OVER":
                                            game_state = "GAME_OVER"
                                            game_result = "VICTORY"
                                            
                                    tactical_state = "IDLE"
                                    selected_unit = None
                                    break
                        else:
                            tactical_state = "TACTICAL_MENU"

    # ==========================================
    # تحديث الأنيميشن الخاص بمشي اللاعب
    # ==========================================
    if tactical_state == "ANIMATING_PLAYER_MOVE":
        if selected_unit and selected_unit.is_animating:
            target_r, target_c = selected_unit.anim_path[0]
            tx, ty = get_hex_center(target_r, target_c, 0, 0)
            
            dx = tx - selected_unit.world_x
            dy = ty - selected_unit.world_y
            dist = math.hypot(dx, dy)
            speed = 12 # سرعة المشي
            
            if dist <= speed:
                selected_unit.world_x = tx
                selected_unit.world_y = ty
                selected_unit.row = target_r
                selected_unit.col = target_c
                selected_unit.anim_path.pop(0)
                
                if not selected_unit.anim_path:
                    selected_unit.is_animating = False
            else:
                selected_unit.world_x += (dx / dist) * speed
                selected_unit.world_y += (dy / dist) * speed
        else:
            selected_unit.moved_this_turn = True
            tactical_state = "TACTICAL_MENU"

    if game_state in ["LEVEL_PLAYING", "GAME_OVER"]:
        hovered_hex = get_hex_at_mouse(mouse_pos[0], mouse_pos[1], camera_x, camera_y, rows, cols)
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: camera_x += CAMERA_SPEED
        if keys[pygame.K_RIGHT]: camera_x -= CAMERA_SPEED
        if keys[pygame.K_UP]: camera_y += CAMERA_SPEED
        if keys[pygame.K_DOWN]: camera_y -= CAMERA_SPEED
            
        x_offset = math.sqrt(3) * HEX_SIZE
        y_offset = (3/2) * HEX_SIZE
        max_cam_x = min(0, WIDTH - ((cols * x_offset) + 200))
        max_cam_y = min(0, HEIGHT - ((rows * y_offset) + 200))
        camera_x = max(max_cam_x, min(0, camera_x))
        camera_y = max(max_cam_y, min(0, camera_y))

    # ==========================================
    # الذكاء الاصطناعي التكتيكي (Smart AI)
    # ==========================================
    if game_state == "LEVEL_PLAYING" and tactical_state == "ENEMY_TURN":
        current_time = pygame.time.get_ticks()
        
        if current_time - last_enemy_action_time > 500: 
            
            # المرحلة 0: اختيار الوحدة الأفضل وتقييم التكتيك
            if enemy_phase == 0:
                ready_enemies = [u for u in units if u.faction == "Enemy" and not u.is_done]
                
                if not ready_enemies:
                    for u in units: 
                        u.reset_turn()
                    tactical_state = "IDLE"
                    enemy_phase = 0
                else:
                    # اختيار عشوائي للوحدة لكي لا يكون النمط مكشوفاً للاعب
                    random.shuffle(ready_enemies)
                    acting_enemy = ready_enemies[0]
                    inspected_unit = acting_enemy 
                    
                    # نظام التقييم (Scoring System)
                    best_score = -99999
                    best_hex = (acting_enemy.row, acting_enemy.col)
                    best_target = None
                    
                    ai_reachable = get_reachable_hexes(acting_enemy.row, acting_enemy.col, acting_enemy.max_move, terrain_grid, rows, cols, units)
                    
                    for r, c in ai_reachable.keys():
                        # 1. الدفاع: الذكاء الاصطناعي يحب الوقوف في السديم
                        score = TERRAIN_TYPES[terrain_grid.get((r, c), "Void")]["def_bonus"] * 2 
                        
                        possible_targets = []
                        for p in units:
                            if p.faction == "Player":
                                dist = hex_distance(r, c, p.row, p.col)
                                
                                # هل يمكنني الهجوم عليه من هذه الخلية؟
                                if dist <= acting_enemy.attack_range:
                                    dmg = acting_enemy.attack_power - p.defense
                                    if acting_enemy.attack_type == p.weakness: dmg *= 1.5
                                    if acting_enemy.attack_type == p.immunity: dmg = 0
                                    
                                    target_score = 500 + dmg * 5 # نقاط أساسية للهجوم
                                    
                                    if "Base" in p.name: 
                                        target_score += 3000 # الأولوية القصوى لتدمير القاعدة!
                                    if p.hp <= dmg: 
                                        target_score += 1500 # الأولوية لقتل الوحدة الضعيفة
                                        
                                    possible_targets.append((target_score, p))
                                else:
                                    # إذا لم أستطع الهجوم، أحاول الاقتراب من هدفي
                                    dist_penalty = dist * 10
                                    if "Base" in p.name: 
                                        dist_penalty -= 30 # الانجذاب نحو القاعدة
                                    score -= dist_penalty
                                    
                        if possible_targets:
                            best_t_score, best_t = max(possible_targets, key=lambda x: x[0])
                            score += best_t_score
                            
                        if score > best_score:
                            best_score = score
                            best_hex = (r, c)
                            best_target = best_t if possible_targets else None
                    
                    enemy_target_hex = best_hex
                    enemy_target_unit = best_target
                    enemy_phase = 1 
                    last_enemy_action_time = current_time 
            
            # المرحلة 1: حساب مسار العدو وبدء المشي
            elif enemy_phase == 1:
                if acting_enemy and enemy_target_hex != (acting_enemy.row, acting_enemy.col):
                    path = get_path(acting_enemy.row, acting_enemy.col, enemy_target_hex[0], enemy_target_hex[1], terrain_grid, rows, cols, units)
                    if path:
                        acting_enemy.start_animation(path, get_hex_center)
                        enemy_phase = 1.5 # دخول مرحلة مشي العدو
                    else:
                        enemy_phase = 2 # إذا تعذر المشي، انتقل للهجوم
                else:
                    enemy_phase = 2 
            
            # المرحلة 1.5: تحديث إحداثيات مشي العدو على الشاشة
            elif enemy_phase == 1.5:
                if acting_enemy.is_animating:
                    target_r, target_c = acting_enemy.anim_path[0]
                    tx, ty = get_hex_center(target_r, target_c, 0, 0)
                    
                    dx = tx - acting_enemy.world_x
                    dy = ty - acting_enemy.world_y
                    dist = math.hypot(dx, dy)
                    speed = 10
                    
                    if dist <= speed:
                        acting_enemy.world_x = tx
                        acting_enemy.world_y = ty
                        acting_enemy.row = target_r
                        acting_enemy.col = target_c
                        acting_enemy.anim_path.pop(0)
                        
                        if not acting_enemy.anim_path:
                            acting_enemy.is_animating = False
                    else:
                        acting_enemy.world_x += (dx / dist) * speed
                        acting_enemy.world_y += (dy / dist) * speed
                else:
                    enemy_phase = 2
                    last_enemy_action_time = current_time
                
            # المرحلة 2: تنفيذ الهجوم ونهاية الدور للوحدة
            elif enemy_phase == 2:
                if acting_enemy and enemy_target_unit and enemy_target_unit in units:
                    target_terrain = terrain_grid.get((enemy_target_unit.row, enemy_target_unit.col), "Void")
                    play_combat_animation(screen, acting_enemy, enemy_target_unit, target_terrain)
                    
                    if enemy_target_unit.hp <= 0: 
                        if "Base" in enemy_target_unit.name:
                            game_state = "GAME_OVER"
                            game_result = "DEFEAT"
                        units.remove(enemy_target_unit)
                        
                        if not [u for u in units if u.faction == "Player"] and game_state != "GAME_OVER":
                            game_state = "GAME_OVER"
                            game_result = "DEFEAT"
                        
                if acting_enemy:
                    acting_enemy.is_done = True
                
                acting_enemy = None
                enemy_target_hex = None
                enemy_target_unit = None
                enemy_phase = 0 
                last_enemy_action_time = current_time

    # ==========================================
    # الرسم والمشاهد (Rendering)
    # ==========================================
    screen.fill(BLACK)
    
    if game_state == "MAIN_MENU":
        draw_level_selection(screen, selected_level)
        
    elif game_state in ["LEVEL_PLAYING", "GAME_OVER"]:
        
        screen.blit(background_image, (0, 0))
        
        for row in range(rows):
            for col in range(cols):
                cx, cy = get_hex_center(row, col, camera_x, camera_y)
                
                if -HEX_SIZE*2 < cx < WIDTH + HEX_SIZE*2 and -HEX_SIZE*2 < cy < HEIGHT + HEX_SIZE*2:
                    terrain_type = terrain_grid.get((row, col), "Void")
                    texture = TERRAIN_TYPES[terrain_type]["texture"]
                    
                    if texture:
                        w = texture.get_width()
                        h = texture.get_height()
                        screen.blit(texture, (int(cx - w//2), int(cy - h//2)))
                    
                    vertices = get_hex_vertices(cx, cy, HEX_SIZE)
                    if tactical_state == "TARGETING_MOVE" and selected_unit:
                        if (row, col) in current_reachable_hexes:
                            pygame.draw.polygon(screen, MOVE_HIGHLIGHT, vertices, 4)
                    elif tactical_state == "TARGETING_ATTACK" and selected_unit:
                        if hex_distance(selected_unit.row, selected_unit.col, row, col) <= selected_unit.attack_range:
                            pygame.draw.polygon(screen, ATTACK_HIGHLIGHT, vertices, 4)
                            
        for u in units: 
            # إذا كانت الوحدة تمشي حالياً، نرسمها حسب إحداثيات المشي الديناميكية
            if u.is_animating:
                unit_cx = u.world_x + camera_x
                unit_cy = u.world_y + camera_y
            else:
                unit_cx, unit_cy = get_hex_center(u.row, u.col, camera_x, camera_y)
            u.draw(screen, unit_cx, unit_cy)

        # رسم مؤشرات نية العدو أثناء دوره
        if tactical_state == "ENEMY_TURN" and acting_enemy:
            # موقع العدو (سواء كان ثابتاً أو يمشي)
            if acting_enemy.is_animating:
                ecx = acting_enemy.world_x + camera_x
                ecy = acting_enemy.world_y + camera_y
            else:
                ecx, ecy = get_hex_center(acting_enemy.row, acting_enemy.col, camera_x, camera_y)
                
            pygame.draw.polygon(screen, (255, 150, 0), get_hex_vertices(ecx, ecy, HEX_SIZE), 4)
            
            if enemy_phase == 1 and enemy_target_hex and enemy_target_hex != (acting_enemy.row, acting_enemy.col):
                tcx, tcy = get_hex_center(enemy_target_hex[0], enemy_target_hex[1], camera_x, camera_y)
                pygame.draw.polygon(screen, MOVE_HIGHLIGHT, get_hex_vertices(tcx, tcy, HEX_SIZE), 4)
                pygame.draw.line(screen, MOVE_HIGHLIGHT, (ecx, ecy), (tcx, tcy), 3)
                
            if enemy_phase == 2 and enemy_target_unit:
                tcx, tcy = get_hex_center(enemy_target_unit.row, enemy_target_unit.col, camera_x, camera_y)
                pygame.draw.polygon(screen, ATTACK_HIGHLIGHT, get_hex_vertices(tcx, tcy, HEX_SIZE), 4)
                pygame.draw.line(screen, ATTACK_HIGHLIGHT, (ecx, ecy), (tcx, tcy), 4)
        
        if tactical_state == "TACTICAL_MENU" and selected_unit:
            active_menu_buttons = draw_command_menu(screen, selected_unit, camera_x, camera_y)

        pygame.draw.rect(screen, (20, 20, 30), (0, 0, WIDTH, 50))
        level_name = campaign_levels[selected_level]['name'] if selected_level in campaign_levels else "Unknown Sector"
        screen.blit(font_medium.render(f"{level_name} | Press [ESC] to Quit", True, HIGHLIGHT), (20, 15))

        btn_color = (150, 0, 0) if tactical_state == "ENEMY_TURN" else (50, 150, 50)
        pygame.draw.rect(screen, btn_color, END_TURN_RECT)
        pygame.draw.rect(screen, WHITE, END_TURN_RECT, 2)
        btn_text = "ENEMY TURN" if tactical_state == "ENEMY_TURN" else "END TURN"
        screen.blit(font_small.render(btn_text, True, WHITE), (END_TURN_RECT.x + 20, END_TURN_RECT.y + 10))

        draw_terrain_info(screen, hovered_hex, terrain_grid)
        draw_bottom_hud(screen, inspected_unit)
        
        if tactical_state == "GUIDE" and guide_unit:
            draw_guide_overlay(screen, guide_unit)

        # شاشة النهاية
        if game_state == "GAME_OVER":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            color = (0, 150, 0, 180) if game_result == "VICTORY" else (150, 0, 0, 180)
            overlay.fill(color)
            screen.blit(overlay, (0, 0))
            
            msg = "MISSION ACCOMPLISHED" if game_result == "VICTORY" else "MISSION FAILED"
            txt = font_large.render(msg, True, WHITE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 50))
            
            hint = font_medium.render("Press [ENTER] or [ESC] to return to Main Menu", True, WHITE)
            screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 50))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()