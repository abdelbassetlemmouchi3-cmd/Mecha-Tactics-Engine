import pygame
import math

# ==========================================
# MechaTactics - Settings & Constants
# ==========================================

# 1. إعدادات الشاشة (Display Settings)
WIDTH = 1024
HEIGHT = 768
FPS = 60 # سرعة التحديث (60 إطار في الثانية)

# 2. إعدادات الشبكة السداسية والخرائط (Grid & Camera Settings)
HEX_SIZE = 35 # حجم الخلية السداسية الواحدة
CAMERA_SPEED = 15 # سرعة تحريك الكاميرا (بكسل في الثانية)

# 3. إعدادات شاشة المعركة الجانبية السينمائية (Combat Screen Settings)
COMBAT_BOX_WIDTH = 800 # عرض صندوق المعركة
COMBAT_BOX_HEIGHT = 400 # ارتفاع صندوق المعركة

# 4. لوحة الألوان (Color Palette)
# الألوان الأساسية
BLACK = (5, 5, 10) # لون الفضاء العميق
WHITE = (255, 255, 255) # الأبيض (للحدود والنصوص)
HIGHLIGHT = (255, 200, 50) # الأصفر (للتمييز والاختيارات)
TERRAIN_COLOR = (20, 30, 45) # لون الفراغ
BORDER_COLOR = (100, 200, 255) # لون حدود الشبكة

# ألوان الفصائل (Faction Colors)
PLAYER_COLOR = (50, 150, 255) # لون قوات اللاعب (أزرق)
ENEMY_COLOR = (255, 50, 50) # لون قوات العدو (أحمر)
UNIT_DONE_COLOR = (100, 100, 100) # لون رمادي باهت إذا انتهى دور الوحدة

# ألوان نطاق الحركة والهجوم (Move & Attack Range Colors)
MOVE_HIGHLIGHT = (50, 255, 50) # أخضر شفاف لنطاق الحركة
ATTACK_HIGHLIGHT = (255, 50, 50) # أحمر شفاف لنطاق الهجوم

# ألوان واجهة المستخدم (UI Colors)
HUD_BG = (20, 25, 35) # خلفية شريط المعلومات (HUD)
GUIDE_BG = (15, 15, 25, 230) # خلفية الدليل الموسوعي (شفافية عالية)
MENU_BG = (30, 30, 50) # خلفية القائمة التكتيكية

# 5. مواقع شاشة المعركة (Combat Screen Locations)
# صندوق المهاجم (اليسار)
ATTACKER_BOX = pygame.Rect(
    (WIDTH - COMBAT_BOX_WIDTH) // 2,
    (HEIGHT - COMBAT_BOX_HEIGHT) // 2 - 100,
    COMBAT_BOX_WIDTH // 2,
    COMBAT_BOX_HEIGHT
)

# صندوق المدافع (اليمين)
DEFENDER_BOX = pygame.Rect(
    ATTACKER_BOX.right,
    ATTACKER_BOX.top,
    COMBAT_BOX_WIDTH // 2,
    COMBAT_BOX_HEIGHT
)

# 6. زر إنهاء الدور (UI Button location)
END_TURN_RECT = pygame.Rect(WIDTH - 160, 10, 140, 40)