import pygame
import math
import random
import os
from settings import *

# ==========================================
# دالة تحميل التضاريس (القص السداسي الأنيق)
# ==========================================
def load_terrain_texture(filename):
    image_path = os.path.join("assets", "terrain", filename)
    w = int(math.sqrt(3) * HEX_SIZE)
    h = int(2 * HEX_SIZE)
    
    try:
        raw_img = pygame.image.load(image_path).convert_alpha()
        scaled_img = pygame.transform.scale(raw_img, (w, h))
        
        hex_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        
        cx, cy = w // 2, h // 2
        vertices = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.pi / 180 * angle_deg
            x = cx + HEX_SIZE * math.cos(angle_rad)
            y = cy + HEX_SIZE * math.sin(angle_rad)
            vertices.append((x, y))
            
        pygame.draw.polygon(hex_surface, (255, 255, 255, 255), vertices)
        hex_surface.blit(scaled_img, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        return hex_surface
        
    except pygame.error as e:
        print(f"Error loading terrain image {image_path}: {e}")
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        return surf

# ==========================================
# التضاريس الفضائية
# ==========================================
TERRAIN_TYPES = {
    "Void": {
        "color": TERRAIN_COLOR, "cost": 1, "def_bonus": 0, "name": "Deep Space",
        "file": None, "texture": None
    },
    "Asteroid": {
        "color": (100, 95, 90), "cost": 99, "def_bonus": 0, "name": "Asteroid Field",
        "file": "asteroid.png", "texture": None
    },
    "Crater": {
        "color": (10, 15, 25), "cost": 2, "def_bonus": -10, "name": "Impact Crater",
        "file": "crater.png", "texture": None
    },
    "Nebula": {
        "color": (80, 30, 100), "cost": 1, "def_bonus": 15, "name": "Nebula Dust",
        "file": "nebula.png", "texture": None
    }
}

def initialize_terrain_textures():
    for t_type in TERRAIN_TYPES:
        file_name = TERRAIN_TYPES[t_type]["file"]
        if file_name:
            TERRAIN_TYPES[t_type]["texture"] = load_terrain_texture(file_name)
        else:
            TERRAIN_TYPES[t_type]["texture"] = None

campaign_levels = {}

# ==========================================
# دوال الرياضيات للشبكة السداسية
# ==========================================
def get_hex_center(row, col, cam_x, cam_y):
    x_offset = math.sqrt(3) * HEX_SIZE
    y_offset = (3/2) * HEX_SIZE
    x = col * x_offset + cam_x + 100
    if row % 2 != 0:
        x += x_offset / 2
    y = row * y_offset + cam_y + 100
    return x, y

def get_hex_vertices(center_x, center_y, size):
    vertices = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.pi / 180 * angle_deg
        x = center_x + size * math.cos(angle_rad)
        y = center_y + size * math.sin(angle_rad)
        vertices.append((x, y))
    return vertices

def get_hex_at_mouse(mouse_x, mouse_y, cam_x, cam_y, rows, cols):
    closest_hex = None
    min_dist = float('inf')
    for row in range(rows):
        for col in range(cols):
            cx, cy = get_hex_center(row, col, cam_x, cam_y)
            dist = math.hypot(mouse_x - cx, mouse_y - cy)
            if dist < min_dist:
                min_dist = dist
                closest_hex = (row, col)
    if min_dist <= HEX_SIZE:
        return closest_hex
    return None

def hex_distance(r1, c1, r2, c2):
    q1 = c1 - (r1 - (r1 % 2)) // 2
    x1 = q1
    z1 = r1
    y1 = -x1 - z1
    q2 = c2 - (r2 - (r2 % 2)) // 2
    x2 = q2
    z2 = r2
    y2 = -x2 - z2
    return max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))

def get_hex_neighbors(r, c, rows, cols):
    if r % 2 == 0:
        dirs = [(0, -1), (0, 1), (-1, -1), (-1, 0), (1, -1), (1, 0)]
    else:
        dirs = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, 1)]
    neighbors = []
    for dr, dc in dirs:
        nr = r + dr
        nc = c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            neighbors.append((nr, nc))
    return neighbors

# ==========================================
# خوارزميات الملاحة (النطاق + المسار)
# ==========================================
def get_reachable_hexes(start_r, start_c, max_move, terrain_grid, rows, cols, current_units):
    reachable = {(start_r, start_c): 0}
    queue = [(start_r, start_c)]
    
    unit_positions = set()
    for u in current_units:
        if not (u.row == start_r and u.col == start_c):
            unit_positions.add((u.row, u.col))
    
    while queue:
        curr_r, curr_c = queue.pop(0)
        curr_cost = reachable[(curr_r, curr_c)]
        
        for nr, nc in get_hex_neighbors(curr_r, curr_c, rows, cols):
            if (nr, nc) in unit_positions:
                continue 
                
            terrain_type = terrain_grid.get((nr, nc), "Void")
            cost_to_enter = TERRAIN_TYPES[terrain_type]["cost"]
            
            if cost_to_enter > 90:
                continue 
                
            new_cost = curr_cost + cost_to_enter
            
            if new_cost <= max_move:
                if (nr, nc) not in reachable or new_cost < reachable[(nr, nc)]:
                    reachable[(nr, nc)] = new_cost
                    queue.append((nr, nc))
                    
    return reachable

def get_path(start_r, start_c, target_r, target_c, terrain_grid, rows, cols, current_units):
    """خوارزمية جديدة لإيجاد أقصر مسار لكي تمشي فيه الوحدة (خطوة بخطوة)"""
    queue = [(start_r, start_c)]
    came_from = {(start_r, start_c): None}
    
    unit_positions = set()
    for u in current_units:
        unit_positions.add((u.row, u.col))
    
    # نسمح بالمرور للهدف النهائي حتى لو كان به عدو (لأننا نقف بجانبه للهجوم)
    if (target_r, target_c) in unit_positions:
        unit_positions.remove((target_r, target_c))
        
    while queue:
        curr = queue.pop(0)
        
        if curr == (target_r, target_c):
            break
            
        for nr, nc in get_hex_neighbors(curr[0], curr[1], rows, cols):
            if (nr, nc) in unit_positions:
                continue
                
            terrain_type = terrain_grid.get((nr, nc), "Void")
            cost_to_enter = TERRAIN_TYPES[terrain_type]["cost"]
            
            if cost_to_enter > 90:
                continue
                
            if (nr, nc) not in came_from:
                came_from[(nr, nc)] = curr
                queue.append((nr, nc))
                
    if (target_r, target_c) not in came_from:
        return [] # لا يوجد مسار
        
    path = []
    curr = (target_r, target_c)
    while curr != (start_r, start_c):
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    
    return path