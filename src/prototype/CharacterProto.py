# CharacterProto.py
import pygame
import random
import constants
from dragon_encounter import dragon_encounter_during_expedition

class Character:
    def __init__(self, name, x, y, width=250, height=100):
        self.name = name
        self.max_health = 100
        self.health = 100
        self.food = 100

        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.coins = 0
        self.points = 0

        self.on_expedition = False
        self.expedition_end_time = 0
        self.days_cooldown_left = 0
        self.is_dead = False

        self.pending_damage = 0
        self.pending_food_loss = 0
        self.pending_loot_spins = 0
        self.pending_death_check = False

        self.equipped_weapon = None
        self.equipped_armor = None

    def getDamage(self):
        return 50

    def get_damage_modifier(self):
        w = self.equipped_weapon
        if w == "wood_sword":
            return 1.2
        elif w == "iron_sword":
            return 1.5
        elif w == "diamond_sword":
            return 2.0
        elif w == "demonic_sword":
            return 3.0
        return 1.0

    def get_damage_resistance(self):
        a = self.equipped_armor
        if a == "iron_protection":
            return 0.2
        elif a == "diamond_protection":
            return 0.5
        return 0.0

    def update_daily(self):
        if self.is_dead:
            return

        if self.food >= 50:
            self.food = max(0, self.food - constants.FOOD_DRAIN_HIGH)
        else:
            self.food = max(0, self.food - constants.FOOD_DRAIN_LOW)

        if self.food == 0:
            self.health = max(0, self.health - constants.HEALTH_DAMAGE_NO_FOOD)

        if self.days_cooldown_left > 0:
            self.days_cooldown_left -= 1

        if self.health <= 0:
            self.is_dead = True

    def update_expedition_status(self, current_time, dragon=None, shared_inv=None):
        if self.on_expedition and current_time >= self.expedition_end_time:
            self.complete_expedition(dragon, shared_inv)

    def start_expedition(self, current_time, dragon=None):
        if self.is_dead or self.on_expedition or self.days_cooldown_left > 0:
            return

        self.on_expedition = True
        self.expedition_end_time = current_time + 2000

        base_food_loss = random.randint(10, 30)
        self.pending_food_loss = int(base_food_loss * constants.EXPEDITION_FOOD_LOSS_MULT)

        base_hp_loss = random.randint(0, 10)
        self.pending_damage = int(base_hp_loss * constants.EXPEDITION_HP_LOSS_MULT)

        chance_to_die = constants.DAILY_DEATH_CHANCE
        self.pending_death_check = (random.random() < chance_to_die)

        self.pending_loot_spins = random.randint(
            constants.EXTRA_EXPEDITION_SPIN_MIN,
            constants.EXTRA_EXPEDITION_SPIN_MAX
        )

    def complete_expedition(self, dragon=None, shared_inv=None):
        self.on_expedition = False
        if self.is_dead:
            return

        if self.pending_death_check:
            self.is_dead = True
            return

        self.health = max(0, self.health - self.pending_damage)
        self.food   = max(0, self.food - self.pending_food_loss)
        if self.health <= 0:
            self.is_dead = True
            return

        if random.random() < 0.2 and dragon and not dragon.is_defeated():
            survived, keep_loot = dragon_encounter_during_expedition(self, dragon)
            if not survived:
                self.is_dead = True
                return
            if not keep_loot:
                self.pending_loot_spins = 0

        if self.is_dead:
            return

        if shared_inv is not None:
            for _ in range(self.pending_loot_spins):
                n = constants.get_random_int()
                spin_for_item(n, None, shared_inv)

        self.days_cooldown_left = constants.EXPEDITION_COOLDOWN
        self.pending_damage = 0
        self.pending_food_loss = 0
        self.pending_death_check = False
        self.pending_loot_spins = 0

    def equip_weapon(self, weapon_name):
        self.equipped_weapon = weapon_name

    def equip_armor(self, armor_name):
        self.equipped_armor = armor_name

    def draw(self, screen, font, selected=False):
        """Draw character with health bar, food bar, equip info, etc."""
        # If character is dead => darker color
        if self.is_dead:
            color_rect = (100,100,100)
        else:
            color_rect = (200,200,200)

        # If selected => highlight border
        if selected and not self.is_dead:
            pygame.draw.rect(screen, (255,215,0), (self.x-5, self.y-5, self.width+10, self.height+10))

        # Main rectangle
        pygame.draw.rect(screen, color_rect, (self.x, self.y, self.width, self.height))

        # Show name + (Dead) if is_dead
        name_text = font.render(self.name + (" (Dead)" if self.is_dead else ""), True, (0,0,0))
        screen.blit(name_text, (self.x+5, self.y+5))

        # If on expedition => show a small progress bar on top
        if self.on_expedition:
            current_time = pygame.time.get_ticks()
            time_left = max(0, self.expedition_end_time - current_time)
            total_time = 2000
            progress = 1 - (time_left / total_time)
            bar_width = int(self.width * progress)
            pygame.draw.rect(screen, (0,200,0), (self.x, self.y-20, bar_width, 5))

        # Health and Food bars
        self._draw_bar(screen, font, "HP", self.health, self.max_health,
                       self.x+5, self.y+30, (255,0,0), (0,255,0))
        self._draw_bar(screen, font, "Food", self.food, 100,
                       self.x+5, self.y+50, (255,0,0), (0,0,255))

        # Show expedition cooldown if any
        if self.days_cooldown_left > 0:
            cd_text = font.render(f"Cooldown: {self.days_cooldown_left}d", True, (50,50,50))
            screen.blit(cd_text, (self.x+self.width-90, self.y+5))

        # Show equipped weapon + armor
        eqp_wpn = self.equipped_weapon if self.equipped_weapon else "None"
        eqp_arm = self.equipped_armor if self.equipped_armor else "None"
        eqp_text = font.render(f"W:{eqp_wpn} A:{eqp_arm}", True, (20,20,20))
        screen.blit(eqp_text, (self.x+5, self.y+85))

    def _draw_bar(self, screen, font, label, value, max_value, x, y, bg_color, fg_color):
        """Helper to draw a labeled bar (HP or Food)."""
        bar_width = self.width - 10
        if max_value > 0:
            filled = int((value / max_value) * bar_width)
        else:
            filled = 0

        pygame.draw.rect(screen, bg_color, (x, y, bar_width, 10))
        pygame.draw.rect(screen, fg_color, (x, y, filled, 10))
        label_text = font.render(f"{label}: {value}", True, (0,0,0))
        screen.blit(label_text, (x + bar_width + 10, y))

    def is_clicked(self, pos):
        """
        Checks if mouse 'pos' is within this character's bounding rect,
        enabling selection on MOUSEBUTTONDOWN in maintProto.
        """
        return (self.x <= pos[0] <= self.x + self.width and
                self.y <= pos[1] <= self.y + self.height)

def spin_for_item(n, unused_char, shared_inv):
    import random
    if n % 10 == 0:
        shared_inv["points"] = shared_inv.get("points", 0) + 10
    elif n % 5 == 0:
        shared_inv["coins"] = shared_inv.get("coins", 0) + 5
    if n % 2 == 0:
        shared_inv["coins"] = shared_inv.get("coins", 0) + 2

    if 0 <= n <= 45:
        add_to_inv(shared_inv, "banana", 1)
    elif 45 < n <= 58:
        add_to_inv(shared_inv, "medical_kit", 1)
    elif 58 < n <= 64:
        add_to_inv(shared_inv, "wood_sword", 1)
    elif 64 < n <= 72:
        add_to_inv(shared_inv, "iron_sword", 1)
    elif 72 < n <= 78:
        add_to_inv(shared_inv, "diamond_sword", 1)
    elif 78 < n <= 82:
        add_to_inv(shared_inv, "demonic_sword", 1)
    elif 82 < n <= 92:
        add_to_inv(shared_inv, "iron_protection", 1)
    elif 92 < n <= 97:
        add_to_inv(shared_inv, "diamond_protection", 1)
    elif 97 < n <= 100:
        if random.random() < 0.5:
            add_to_inv(shared_inv, "time_sandwich", 1)
        else:
            add_to_inv(shared_inv, "bandages", 1)

def add_to_inv(shared_inv, item_name, amount):
    shared_inv[item_name] = shared_inv.get(item_name, 0) + amount
