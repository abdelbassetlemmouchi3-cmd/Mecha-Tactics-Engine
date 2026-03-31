import pygame
import os
import math
from settings import *

class Mecha:
    def __init__(self, name, row, col, faction, hp, attack, defense, max_move, attack_range, attack_type, weakness, immunity, description, image_filename):
        self.name = name
        self.row = row
        self.col = col
        self.faction = faction
        self.max_hp = hp
        self.hp = hp
        self.attack_power = attack
        self.defense = defense
        self.max_move = max_move
        self.attack_range = attack_range
        self.attack_type = attack_type
        self.weakness = weakness
        self.immunity = immunity
        self.description = description
        self.image_filename = image_filename
        
        self.is_done = False
        self.moved_this_turn = False
        self.attacked_this_turn = False
        
        # متغيرات الأنيميشن (المشي السلس)
        self.anim_path = []
        self.is_animating = False
        self.world_x = 0
        self.world_y = 0
        
        self.image = None
        self.original_image = None
        if image_filename:
            path = os.path.join("assets", "units", image_filename)
            try:
                self.original_image = pygame.image.load(path).convert_alpha()
                size = int(HEX_SIZE * 1.8) 
                self.image = pygame.transform.smoothscale(self.original_image, (size, size))
            except pygame.error as e:
                print(f"Error loading {path}: {e}")
                self.image = pygame.Surface((30, 30))
                self.image.fill(PLAYER_COLOR if faction == "Player" else ENEMY_COLOR)

    def start_animation(self, path, get_hex_center):
        """تجهيز الوحدة لبدء المشي الانسيابي"""
        self.anim_path = path
        self.is_animating = True
        # تعيين نقطة الانطلاق
        self.world_x, self.world_y = get_hex_center(self.row, self.col, 0, 0)
        
    def draw(self, screen, cx, cy):
        if self.image:
            rect = self.image.get_rect(center=(int(cx), int(cy)))
            
            # تأثير اللون الرمادي
            if self.is_done:
                temp_img = self.image.copy()
                temp_img.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
                screen.blit(temp_img, rect)
            else:
                screen.blit(self.image, rect)
            
            # شريط الصحة
            health_width = 40
            health_x = cx - health_width // 2
            health_y = cy + 25
            pygame.draw.rect(screen, (100, 0, 0), (health_x, health_y, health_width, 4))
            pygame.draw.rect(screen, (0, 255, 0), (health_x, health_y, health_width * (self.hp / self.max_hp), 4))
            pygame.draw.rect(screen, WHITE, (health_x, health_y, health_width, 4), 1)

    def take_damage(self, attacker, terrain_bonus):
        damage = attacker.attack_power - (self.defense + terrain_bonus)
        if attacker.attack_type == self.weakness:
            damage *= 1.5
        if attacker.attack_type == self.immunity:
            damage = 0
        damage = max(0, int(damage))
        self.hp -= damage
        return damage

    def reset_turn(self):
        self.is_done = False
        self.moved_this_turn = False
        self.attacked_this_turn = False

def load_level_units():
    return [
        Mecha("Zain Vanguard", 0, 0, "Player", 120, 45, 15, 4, 1, "Melee", "Energy", "Projectile", "آلي زين المتخصص في القتال القريب.", "zain.png"),
        Mecha("Naya Artillery", 0, 0, "Player", 80, 55, 5, 2, 4, "Projectile", "Melee", "Energy", "آلية نايا المجهزة بمدفعية بعيدة المدى.", "naya.png"),
        Mecha("Zain Command Base", 0, 0, "Player", 300, 0, 20, 0, 0, "None", "None", "None", "مركز القيادة الخاص بك. تدميره يعني الهزيمة.", "base_player.png"),
        
        Mecha("Enemy Command Base", 0, 0, "Enemy", 300, 0, 20, 0, 0, "None", "None", "None", "مركز قيادة العدو. دمره للانتصار.", "base_enemy.png"),
        Mecha("Shield Drone", 0, 0, "Enemy", 150, 30, 25, 2, 1, "Melee", "Energy", "Projectile", "طائرة عدو مدرعة يصعب اختراقها.", "shield_drone.png"),
        Mecha("Scout Drone", 0, 0, "Enemy", 60, 25, 5, 5, 2, "Energy", "Projectile", "None", "طائرة استطلاع سريعة وخطيرة.", "scout_drone.png"),
        Mecha("Heavy Titan", 0, 0, "Enemy", 200, 60, 10, 2, 2, "Projectile", "Energy", "None", "آلي ثقيل يمتلك قوة نيران هائلة.", "titan.png")
    ]