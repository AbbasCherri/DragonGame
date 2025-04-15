# trader_event.py
# --------------------------------------------------------
# A dedicated trader system with exclusive shop-only items
# and a UI overlay. The user can buy items if they have
# enough coins. 
# --------------------------------------------------------
import pygame

SHOP_ITEMS = {
    "platinum_sword": {
        "price": 75,
        "description": "Rare sword (Damage x2.5)",
        "type": "weapon",
        "damage_multiplier": 2.5
    },
    "titanium_armor": {
        "price": 80,
        "description": "Armor with 60% damage reduction",
        "type": "armor",
        "damage_reduction": 0.6
    },
    "magic_elixir": {
        "price": 40,
        "description": "Fully heals and adds 30 food",
        "type": "consumable",
        "health_restore": 100,
        "food_restore": 30
    },
    "phoenix_feather": {
        "price": 50,
        "description": "Revives a character instantly if they die (one-time use).",
        "type": "consumable",
        "revive": True
    },
    "arcane_amulet": {
        "price": 60,
        "description": "Accessory that slightly boosts all stats and expedition success chance.",
        "type": "accessory",
        "stat_boost": 0.1  # 10% 
    }
}

class TraderUI:
    def __init__(self, x, y, width, height, font, chat_box, shared_inventory, get_player_coins_func, set_player_coins_func):
        """
        x,y: top-left of the trader UI
        width, height: dimensions
        font: pygame font
        chat_box: reference to your ChatBox
        shared_inventory: reference to the global shared inventory
        get_player_coins_func: function to retrieve player's coin count
        set_player_coins_func: function to update player's coin count
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.chat_box = chat_box
        self.shared_inventory = shared_inventory
        self.get_player_coins = get_player_coins_func
        self.set_player_coins = set_player_coins_func

        self.visible = False

        self.close_button_rect = pygame.Rect(x + width - 70, y + height - 40, 60, 30)

        # For item selection
        self.selected_item = None

    def open(self):
        self.visible = True
        self.selected_item = None

    def close(self):
        self.visible = False
        self.selected_item = None

    def is_open(self):
        return self.visible

    def handle_event(self, event):
        if not self.visible:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if not self.rect.collidepoint(pos):
                # click outside => close the UI if you want that behavior
                # self.close()
                pass
            else:
                # check if close button is clicked
                if self.close_button_rect.collidepoint(pos):
                    self.close()
                    return

                # check each shop item row
                item_y_start = self.rect.y + 40
                spacing = 25
                i = 0
                for item_name, data in SHOP_ITEMS.items():
                    row_rect = pygame.Rect(self.rect.x+20, item_y_start + i*spacing, 200, 20)
                    if row_rect.collidepoint(pos):
                        self.selected_item = item_name
                    i += 1

                # If we want to handle a "Buy" button next to each item, we can do that too
                # But let's keep it simple: selecting an item triggers purchase or a second click?
                # Let's do a second approach: if an item is selected, do a purchase right away
                # Or you can add a single "Buy" button. We'll do single click for demonstration
                if self.selected_item:
                    self.attempt_purchase(self.selected_item, 1)  # buy 1

    def attempt_purchase(self, item_name, quantity):
        # get price
        if item_name not in SHOP_ITEMS:
            return
        data = SHOP_ITEMS[item_name]
        price_each = data["price"]
        total_cost = price_each * quantity
        coins = self.get_player_coins()

        if coins < total_cost:
            self.chat_box.add_message("Not enough coins to buy this item!")
            return

        # deduct coins
        coins -= total_cost
        self.set_player_coins(coins)

        # add to shared inventory
        if item_name not in self.shared_inventory:
            self.shared_inventory[item_name] = 0
        self.shared_inventory[item_name] += quantity

        self.chat_box.add_message(f"Purchased {quantity} x {item_name} for {total_cost} coins.")

    def draw(self, screen):
        if not self.visible:
            return

        pygame.draw.rect(screen, (60, 60, 60), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)

        title_surf = self.font.render("Trader's Shop", True, (255, 255, 255))
        screen.blit(title_surf, (self.rect.x + 10, self.rect.y + 10))

        # draw close button
        pygame.draw.rect(screen, (100,100,100), self.close_button_rect)
        close_text = self.font.render("Close", True, (255,255,255))
        screen.blit(close_text, close_text.get_rect(center=self.close_button_rect.center))

        # display player's coins
        coins = self.get_player_coins()
        coins_text = self.font.render(f"Coins: {coins}", True, (255, 255, 0))
        screen.blit(coins_text, (self.rect.x + 10, self.rect.y + 300))

        # list shop items
        item_y_start = self.rect.y + 40
        spacing = 25
        i = 0
        for item_name, data in SHOP_ITEMS.items():
            row_y = item_y_start + i*spacing
            disp = f"{item_name} (Price: {data['price']})"
            item_surf = self.font.render(disp, True, (255,255,255))
            screen.blit(item_surf, (self.rect.x + 20, row_y))
            i += 1

        # if an item is selected, show details
        if self.selected_item and self.selected_item in SHOP_ITEMS:
            item_data = SHOP_ITEMS[self.selected_item]
            info_x = self.rect.x + 250
            info_y = self.rect.y + 40
            sel_name = self.font.render(self.selected_item, True, (255,255,0))
            screen.blit(sel_name, (info_x, info_y))
            info_y += 25

            desc_surf = self.font.render(item_data["description"], True, (200,200,200))
            screen.blit(desc_surf, (info_x, info_y))
