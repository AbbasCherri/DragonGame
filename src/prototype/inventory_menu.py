# inventory_menu.py

import pygame
from typing import Optional

# We keep the same item data definitions
ITEM_DATA = {
    "banana": {
        "display_name": "Banana",
        "description": "Restores 30 Food to the selected character.",
        "stats": "Food +30",
        "usable": True,
        "is_weapon": False,
        "is_armor": False
    },
    "medical_kit": {
        "display_name": "Medical Kit",
        "description": "Fully heals the selected character.",
        "stats": "Full Heal",
        "usable": True,
        "is_weapon": False,
        "is_armor": False
    },
    "bandages": {
        "display_name": "Bandages",
        "description": "Heals 30 HP for the selected character.",
        "stats": "HP +30",
        "usable": True,
        "is_weapon": False,
        "is_armor": False
    },
    "wood_sword": {
        "display_name": "Wood Sword",
        "description": "A basic sword (DMG x1.2).",
        "stats": "Damage x1.2",
        "usable": False,
        "is_weapon": True,
        "is_armor": False
    },
    "iron_sword": {
        "display_name": "Iron Sword",
        "description": "A decent sword (DMG x1.5).",
        "stats": "Damage x1.5",
        "usable": False,
        "is_weapon": True,
        "is_armor": False
    },
    "diamond_sword": {
        "display_name": "Diamond Sword",
        "description": "A strong sword (DMG x2).",
        "stats": "Damage x2",
        "usable": False,
        "is_weapon": True,
        "is_armor": False
    },
    "demonic_sword": {
        "display_name": "Demonic Sword",
        "description": "A cursed sword (DMG x3).",
        "stats": "Damage x3",
        "usable": False,
        "is_weapon": True,
        "is_armor": False
    },
    "iron_protection": {
        "display_name": "Iron Armor",
        "description": "20% damage reduction.",
        "stats": "Resist = 0.2",
        "usable": False,
        "is_weapon": False,
        "is_armor": True
    },
    "diamond_protection": {
        "display_name": "Diamond Armor",
        "description": "50% damage reduction.",
        "stats": "Resist = 0.5",
        "usable": False,
        "is_weapon": False,
        "is_armor": True
    },
    "time_sandwich": {
        "display_name": "Time Sandwich",
        "description": "Halves chance of dying on expedition. Must be used before expedition. (TBD).",
        "stats": "Death chance x0.5 (not auto-applied here)",
        "usable": False,
        "is_weapon": False,
        "is_armor": False
    },
    "temp_damage_boost": {
        "display_name": "Damage Boost",
        "description": "Temporary +0.5 DMG in fights.",
        "stats": "Additional +0.5 multiplier",
        "usable": False,
        "is_weapon": False,
        "is_armor": False
    },
    "temp_damage_reduction": {
        "display_name": "Damage Injury",
        "description": "Temporary -??? DMG in fights.",
        "stats": "Injury effect",
        "usable": False,
        "is_weapon": False,
        "is_armor": False
    }
}

class InventoryMenu:
    def __init__(self, x, y, width, height, font, chat_box=None, shared_inv=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.visible = False
        self.chat_box = chat_box

        # The single, shared inventory
        self.shared_inventory = shared_inv if shared_inv else {}

        # The 'selected_character' is who we do "Use" or "Equip" on
        self.current_character = None
        self.selected_item = None

        # Rects for buttons
        self.use_button_rect   = pygame.Rect(x + width - 160, y + height - 40, 70, 30)
        self.equip_button_rect = pygame.Rect(x + width - 80,  y + height - 40, 70, 30)

    def open(self, character):
        self.current_character = character
        self.selected_item = None
        self.visible = True

    def close(self):
        self.visible = False
        self.current_character = None
        self.selected_item = None

    def is_open(self):
        return self.visible

    def handle_event(self, event):
        if not self.visible or self.current_character is None:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if not self.rect.collidepoint(pos):
                # optionally close if outside
                pass
            else:
                # Check item selection in the shared inventory
                start_y = self.rect.y + 40
                spacing = 25
                i = 0
                # We'll iterate over the items in the shared_inventory
                for item_name, qty in self.shared_inventory.items():
                    text_rect = pygame.Rect(self.rect.x+20, start_y + i*spacing, 200, 20)
                    if text_rect.collidepoint(pos):
                        self.selected_item = item_name
                    i += 1

                # "Use" button
                if self.use_button_rect.collidepoint(pos) and self.selected_item:
                    data = ITEM_DATA.get(self.selected_item, {})
                    if data.get("usable", False):
                        # This item is consumable => apply to self.current_character
                        self.use_consumable(self.selected_item, self.current_character)
                    else:
                        if self.chat_box:
                            self.chat_box.add_message("Item cannot be used.")
                
                # "Equip" button
                if self.equip_button_rect.collidepoint(pos) and self.selected_item:
                    data = ITEM_DATA.get(self.selected_item, {})
                    if data.get("is_weapon", False):
                        self.equip_weapon(self.selected_item, self.current_character)
                    elif data.get("is_armor", False):
                        self.equip_armor(self.selected_item, self.current_character)
                    else:
                        if self.chat_box:
                            self.chat_box.add_message("Item cannot be equipped.")

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()

    def draw(self, screen):
        if not self.visible or self.current_character is None:
            return

        pygame.draw.rect(screen, (50, 50, 50), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)

        title_surf = self.font.render(f"Shared Inventory (Using: {self.current_character.name})", True, (255,255,255))
        screen.blit(title_surf, (self.rect.x+10, self.rect.y+10))

        # List the shared inventory items
        start_y = self.rect.y + 40
        spacing = 25
        i = 0
        for item_name, qty in self.shared_inventory.items():
            # skip items with zero quantity
            if qty <= 0:
                continue
            disp_name = ITEM_DATA.get(item_name, {}).get("display_name", item_name)
            line_str = f"{disp_name} x{qty}"
            line_surf = self.font.render(line_str, True, (255,255,255))
            screen.blit(line_surf, (self.rect.x+20, start_y + i*spacing))
            i += 1

        # If something selected, show details
        if self.selected_item:
            data = ITEM_DATA.get(self.selected_item, {})
            info_x = self.rect.x + 250
            info_y = self.rect.y + 40

            name_surf = self.font.render(data.get("display_name", self.selected_item), True, (255,255,0))
            screen.blit(name_surf, (info_x, info_y))
            info_y += 25

            desc_lines = wrap_text(data.get("description",""), self.font, 200)
            for line in desc_lines:
                line_surf = self.font.render(line, True, (255,255,255))
                screen.blit(line_surf, (info_x, info_y))
                info_y += 20

            stats_surf = self.font.render(f"Stats: {data.get('stats','N/A')}", True, (200,200,200))
            screen.blit(stats_surf, (info_x, info_y))

        # Draw Use/Equip buttons
        pygame.draw.rect(screen, (100,100,100), self.use_button_rect)
        u_surf = self.font.render("Use", True, (255,255,255))
        screen.blit(u_surf, u_surf.get_rect(center=self.use_button_rect.center))

        pygame.draw.rect(screen, (100,100,100), self.equip_button_rect)
        e_surf = self.font.render("Equip", True, (255,255,255))
        screen.blit(e_surf, e_surf.get_rect(center=self.equip_button_rect.center))

        # "Press ESC to Exit"
        esc_text = self.font.render("Press ESC to Exit", True, (200,200,200))
        screen.blit(esc_text, (self.rect.right - esc_text.get_width() - 10, self.rect.bottom - esc_text.get_height() - 5))

    # --------------------
    #   HELPER METHODS
    # --------------------
    def use_consumable(self, item_name, character):
        """Consume one item from shared_inventory; apply effect to 'character'."""
        if self.shared_inventory.get(item_name, 0) <= 0:
            if self.chat_box:
                self.chat_box.add_message(f"No {item_name} left.")
            return
        
        # Actually consume
        self.shared_inventory[item_name] -= 1
        if self.shared_inventory[item_name] <= 0:
            self.shared_inventory.pop(item_name)

        # Now apply effect to the character
        if item_name == "banana":
            healed_food = min(100 - character.food, 30)
            character.food += healed_food
            if self.chat_box:
                self.chat_box.add_message(f"{character.name} ate Banana. +{healed_food} Food.")
        elif item_name == "medical_kit":
            old_hp = character.health
            character.health = character.max_health
            if self.chat_box:
                self.chat_box.add_message(f"{character.name} used a Medical Kit. HP from {old_hp} to {character.health}.")
        elif item_name == "bandages":
            to_heal = min(character.max_health - character.health, 30)
            character.health += to_heal
            if self.chat_box:
                self.chat_box.add_message(f"{character.name} used Bandages. +{to_heal} HP!")
        else:
            # If you want to handle "time_sandwich" usage or others, do it here
            if self.chat_box:
                self.chat_box.add_message(f"Item {item_name} used, but no effect coded.")

    def equip_weapon(self, item_name, character):
        """Equip a weapon from the shared inventory onto this character."""
        if self.shared_inventory.get(item_name, 0) <= 0:
            if self.chat_box:
                self.chat_box.add_message(f"No {item_name} left to equip.")
            return
        
        # Deduct 1 from shared
        self.shared_inventory[item_name] -= 1
        if self.shared_inventory[item_name] <= 0:
            self.shared_inventory.pop(item_name)

        # The old weapon is effectively lost or returned to shared inventory if you want. We'll skip returning it.
        character.equip_weapon(item_name)
        if self.chat_box:
            self.chat_box.add_message(f"{character.name} equipped {item_name} as a weapon!")

    def equip_armor(self, item_name, character):
        """Equip armor from the shared inventory."""
        if self.shared_inventory.get(item_name, 0) <= 0:
            if self.chat_box:
                self.chat_box.add_message(f"No {item_name} left to equip.")
            return

        self.shared_inventory[item_name] -= 1
        if self.shared_inventory[item_name] <= 0:
            self.shared_inventory.pop(item_name)
        character.equip_armor(item_name)
        if self.chat_box:
            self.chat_box.add_message(f"{character.name} equipped {item_name} as armor!")

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""
    for w in words:
        test_line = current_line + w + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = w + " "
    if current_line:
        lines.append(current_line.strip())
    return lines
