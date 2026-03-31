import pygame
import sys
from settings import *
from hex_map import TERRAIN_TYPES

# ==========================================
# تهيئة خطوط شاشة المعركة
# ==========================================
pygame.init()
font_title = pygame.font.Font(None, 64)
font_large = pygame.font.Font(None, 48)
font_medium = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 24)

# ==========================================
# المشهد السينمائي للمعركة (Combat Cinematic) - نسخة الصور!
# ==========================================
def play_combat_animation(screen, attacker, defender, target_terrain):
    """
    هذه الدالة توقف اللعبة التكتيكية مؤقتاً، وتفتح مشهداً سينمائياً
    يعرض الهجوم بالصور الحقيقية وتناقص الصحة، ثم تعود اللعبة لحالتها الطبيعية.
    """
    clock = pygame.time.Clock()
    
    # حساب الضرر قبل بدء الأنيميشن لتجهيز شريط الصحة
    old_hp = defender.hp
    terrain_bonus = TERRAIN_TYPES[target_terrain]["def_bonus"]
    damage_dealt = defender.take_damage(attacker, terrain_bonus)
    new_hp = defender.hp
    
    # إعدادات المشهد الزمني
    timer = 0
    duration = 180  # مدة المشهد 3 ثوانٍ (60 إطار × 3)
    
    # خلفيات الشاشة المنقسمة
    left_bg = BLACK # المهاجم دائماً في الفضاء
    right_bg = TERRAIN_TYPES[target_terrain]["color"] # المدافع في تضاريسه
    
    # ألوان الفصائل (للنصوص والواجهة)
    att_color = PLAYER_COLOR if attacker.faction == "Player" else ENEMY_COLOR
    def_color = PLAYER_COLOR if defender.faction == "Player" else ENEMY_COLOR
    
    # [التعديل الجديد]: تجهيز الصور وتكبيرها للعرض السينمائي
    # نستخدم الصورة الأصلية (original_image) ونكبرها لنحافظ على جودتها
    img_size = 180
    if attacker.original_image:
        att_large_img = pygame.transform.scale(attacker.original_image, (img_size, img_size))
    else:
        att_large_img = pygame.Surface((img_size, img_size))
        att_large_img.fill(att_color)

    if defender.original_image:
        def_large_img = pygame.transform.scale(defender.original_image, (img_size, img_size))
    else:
        def_large_img = pygame.Surface((img_size, img_size))
        def_large_img.fill(def_color)

    # تحديد مواقع الصور المبدئية
    att_x = WIDTH // 4 - (img_size // 2)
    att_y = HEIGHT // 3 - (img_size // 2)
    
    def_x = 3 * WIDTH // 4 - (img_size // 2)
    def_y = HEIGHT // 3 - (img_size // 2)

    running = True
    while running and timer < duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        # 1. رسم الشاشة المنقسمة (Split Screen)
        pygame.draw.rect(screen, left_bg, (0, 0, WIDTH//2, HEIGHT - 200))
        pygame.draw.rect(screen, right_bg, (WIDTH//2, 0, WIDTH//2, HEIGHT - 200))
        pygame.draw.line(screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT - 200), 5)
        
        # 2. أنيميشن حركة المهاجم (حسب نوع السلاح)
        current_att_x = att_x
        if 40 < timer < 90:
            if attacker.attack_type == "Melee":
                # أنيميشن سيف/اشتباك: المهاجم يقترب بسرعة لليمين
                offset = (timer - 40) * 12
                if offset > (WIDTH//2 - 160):
                    offset = WIDTH//2 - 160
                current_att_x = att_x + offset
        
        # رسم صور الآليات
        screen.blit(att_large_img, (current_att_x, att_y))
        screen.blit(def_large_img, (def_x, def_y))
        
        # 3. أنيميشن إطلاق النار (للأسلحة البعيدة)
        if 40 < timer < 90:
            if attacker.attack_type == "Energy" or attacker.attack_type == "Projectile":
                # شعاع ليزر أو رصاصة تنطلق من المهاجم نحو المدافع
                beam_width = (timer - 40) * 20
                beam_rect = pygame.Rect(current_att_x + img_size - 20, att_y + (img_size//2) - 10, beam_width, 20)
                
                # إيقاف الشعاع عند اصطدامه بالمدافع
                if beam_rect.right > def_x + 20:
                    beam_rect.right = def_x + 20
                    
                color = HIGHLIGHT if attacker.attack_type == "Energy" else (200, 200, 200)
                pygame.draw.rect(screen, color, beam_rect)
        
        # 4. أنيميشن الانفجار أو الاصطدام فوق المدافع
        if 80 < timer < 110:
            explosion_radius = (timer - 80) * 4
            pygame.draw.circle(screen, (255, 100, 50), (def_x + (img_size//2), def_y + (img_size//2)), explosion_radius)
            pygame.draw.circle(screen, WHITE, (def_x + (img_size//2), def_y + (img_size//2)), explosion_radius - 5, 3)

        # 5. رسائل المعركة (IMMUNE أو CRITICAL)
        if damage_dealt == 0 and timer > 90:
            immune_txt = font_title.render("IMMUNE!", True, (100, 255, 100))
            screen.blit(immune_txt, (def_x + (img_size//2) - immune_txt.get_width()//2, def_y - 60))
        elif attacker.attack_type == defender.weakness and timer > 90:
            crit_txt = font_title.render("CRITICAL!", True, (255, 50, 50))
            screen.blit(crit_txt, (def_x + (img_size//2) - crit_txt.get_width()//2, def_y - 60))

        # ==========================================
        # 6. لوحة المواجهة السفلية (Duel HUD)
        # ==========================================
        hud_y = HEIGHT - 200
        pygame.draw.rect(screen, HUD_BG, (0, hud_y, WIDTH, 200))
        pygame.draw.line(screen, BORDER_COLOR, (0, hud_y), (WIDTH, hud_y), 5)
        pygame.draw.line(screen, BORDER_COLOR, (WIDTH//2, hud_y), (WIDTH//2, HEIGHT), 5)
        
        # --- قسم المهاجم (اليسار) ---
        screen.blit(font_large.render(attacker.name, True, att_color), (30, hud_y + 20))
        screen.blit(font_medium.render("ATTACKER", True, HIGHLIGHT), (30, hud_y + 60))
        
        screen.blit(font_small.render(f"Weapon Type: {attacker.attack_type}", True, WHITE), (30, hud_y + 110))
        screen.blit(font_small.render(f"Base Attack: {attacker.attack_power}", True, WHITE), (30, hud_y + 140))
        
        # --- قسم المدافع (اليمين) ---
        screen.blit(font_large.render(defender.name, True, def_color), (WIDTH//2 + 30, hud_y + 20))
        screen.blit(font_medium.render("DEFENDER", True, BORDER_COLOR), (WIDTH//2 + 30, hud_y + 60))
        
        screen.blit(font_small.render(f"Terrain: {TERRAIN_TYPES[target_terrain]['name']}", True, WHITE), (WIDTH//2 + 30, hud_y + 110))
        screen.blit(font_small.render(f"Total Defense: {defender.defense + terrain_bonus}", True, WHITE), (WIDTH//2 + 30, hud_y + 140))
        
        # 7. أنيميشن شريط الصحة المتناقص (Smooth HP Drain)
        current_displayed_hp = old_hp
        if timer > 90:
            drain_progress = min(1.0, (timer - 90) / 30.0)
            current_displayed_hp = old_hp - (old_hp - new_hp) * drain_progress
            
        hp_text = font_large.render(f"HP: {int(current_displayed_hp)}", True, WHITE)
        screen.blit(hp_text, (WIDTH - 200, hud_y + 110))
        
        bar_w = 300
        pygame.draw.rect(screen, (100, 0, 0), (WIDTH - 350, hud_y + 150, bar_w, 20))
        pygame.draw.rect(screen, (0, 255, 0), (WIDTH - 350, hud_y + 150, bar_w * max(0, current_displayed_hp / defender.max_hp), 20))
        pygame.draw.rect(screen, WHITE, (WIDTH - 350, hud_y + 150, bar_w, 20), 2)
        
        # إظهار رقم الضرر الأحمر الصاعد
        if timer > 90 and damage_dealt > 0:
            float_y = def_y + 20 - (timer - 90)
            dmg_txt = font_large.render(f"-{damage_dealt}", True, (255, 50, 50))
            screen.blit(dmg_txt, (def_x - 40, float_y))

        pygame.display.flip()
        clock.tick(FPS)
        timer += 1