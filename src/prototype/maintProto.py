# maintProto.py

import pygame
import sys
import uuid

import constants
from constants import WIDTH, HEIGHT, FPS, WHITE, BLACK, get_random_int
import events
from CharacterProto import Character
from ButtonProto import Button
from Dragon import Dragon
from inventory_menu import InventoryMenu
from chat_box import ChatBox
from ai_advisor import AIAdvisor
from trader_event import TraderUI
from dragon_battle import pokemon_style_fight  # Example "Pokemon-style" battle

###############################################################################
# GLOBALS
###############################################################################
shared_inventory = {}
game_characters = []
day = 1  # <-- Kept at module level
session_id = str(uuid.uuid4())

def select_difficulty(screen, font):
    clock = pygame.time.Clock()
    easy_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 60, 100, 50)
    med_rect  = pygame.Rect(WIDTH//2 -  50, HEIGHT//2 - 60, 100, 50)
    hard_rect = pygame.Rect(WIDTH//2 +  50, HEIGHT//2 - 60, 100, 50)
    chosen = None

    while chosen is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if easy_rect.collidepoint(pos):
                    chosen = "easy"
                elif med_rect.collidepoint(pos):
                    chosen = "medium"
                elif hard_rect.collidepoint(pos):
                    chosen = "hard"

        screen.fill((0,0,0))
        title_surf = font.render("Select Difficulty", True, (255,255,255))
        screen.blit(title_surf, (WIDTH//2 - 70, HEIGHT//2 - 130))

        pygame.draw.rect(screen, (100,100,100), easy_rect)
        pygame.draw.rect(screen, (100,100,100), med_rect)
        pygame.draw.rect(screen, (100,100,100), hard_rect)

        e_surf = font.render("Easy", True, (255,255,255))
        m_surf = font.render("Medium", True, (255,255,255))
        h_surf = font.render("Hard", True, (255,255,255))
        screen.blit(e_surf, (easy_rect.x+15, easy_rect.y+10))
        screen.blit(m_surf, (med_rect.x+3, med_rect.y+10))
        screen.blit(h_surf, (hard_rect.x+15, hard_rect.y+10))

        pygame.display.flip()
        clock.tick(30)
    return chosen

def apply_difficulty_settings(diff):
    if diff == "easy":
        constants.DAILY_DEATH_CHANCE = 0.15
        constants.POSITIVE_EVENT_CHANCE = 0.60
        constants.STARTING_SPINS = 8
        constants.MATH_TIME_LIMIT = 6
    elif diff == "medium":
        constants.DAILY_DEATH_CHANCE = 0.20
        constants.POSITIVE_EVENT_CHANCE = 0.55
        constants.STARTING_SPINS = 8
        constants.MATH_TIME_LIMIT = 5
    else:
        constants.DAILY_DEATH_CHANCE = 0.25
        constants.POSITIVE_EVENT_CHANCE = 0.50
        constants.STARTING_SPINS = 8
        constants.MATH_TIME_LIMIT = 4

def game_over_screen(screen, font):
    clock = pygame.time.Clock()
    button_rect = pygame.Rect(WIDTH//2 - 60, HEIGHT//2, 120, 50)
    running = True
    user_choice_restart = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    user_choice_restart = True
                    running = False

        screen.fill((50,0,0))
        over_surf = font.render("GAME OVER", True, (255,255,255))
        over_rect = over_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        screen.blit(over_surf, over_rect)

        pygame.draw.rect(screen, (100,100,100), button_rect)
        retry_surf = font.render("Try Again", True, (255,255,255))
        retry_rect = retry_surf.get_rect(center=button_rect.center)
        screen.blit(retry_surf, retry_rect)

        pygame.display.flip()
        clock.tick(30)

    return user_choice_restart

def main():
    global shared_inventory, game_characters, day  # day is global => fix no binding for nonlocal 'day'

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bunker Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    diff = select_difficulty(screen, font)
    apply_difficulty_settings(diff)

    chat_box = ChatBox(10, HEIGHT-150, 380, 140, font)

    advisor = AIAdvisor("advisor_model.pkl")
    if advisor.is_loaded():
        chat_box.add_message("Decision Tree Advisor loaded successfully!")
    else:
        chat_box.add_message("No AI model found. Using fallback 50% guess.")

    # local definitions
    from trader_event import TraderUI
    player_coins = 50

    def get_player_coins():
        return player_coins
    def set_player_coins(val):
        nonlocal player_coins
        player_coins = val

    trader_ui = TraderUI(
        x=WIDTH//4, y=HEIGHT//4,
        width=WIDTH//2, height=HEIGHT//2,
        font=font,
        chat_box=chat_box,
        shared_inventory=shared_inventory,
        get_player_coins_func=get_player_coins,
        set_player_coins_func=set_player_coins
    )

    # create characters
    characters = [
        Character("Alice", 50, 50),
        Character("Bob", 50, 200),
        Character("Charlie", 50, 350)
    ]
    game_characters = characters

    from CharacterProto import spin_for_item
    for _ in range(constants.STARTING_SPINS):
        n = get_random_int()
        spin_for_item(n, None, shared_inventory)

    dragon = Dragon()

    blocking_event_in_progress = [False]
    def set_blocking_event(state: bool):
        blocking_event_in_progress[0] = state

    selected_character = None

    def skip_day_callback():
        global day  # remove nonlocal, we want day as module-level global
        if blocking_event_in_progress[0]:
            chat_box.add_message("Cannot skip day during an event!")
            return

        day += 1
        chat_box.add_message(f"--- Start of Day {day} ---")

        updated = advisor.retrain_model()
        if updated:
            chat_box.add_message("AI re-trained from new data.")

        for c in characters:
            c.update_daily()
        events.handle_daily_events(characters, screen, font, chat_box, set_blocking_event, dragon)

    skip_day_button = Button("Skip Day", WIDTH-200, HEIGHT-220, 150, 50, skip_day_callback, font)

    def expedition_callback():
        nonlocal selected_character
        if blocking_event_in_progress[0]:
            chat_box.add_message("Cannot send expedition now!")
            return
        if selected_character and not selected_character.is_dead:
            adv_text = advisor.get_advanced_advice(
                selected_character.health,
                selected_character.food,
                selected_character.get_damage_modifier(),
                selected_character.get_damage_resistance(),
                selected_character.days_cooldown_left,
                day,
                shared_inventory
            )
            for line in adv_text.split("\n"):
                chat_box.add_message(line)

            current_time = pygame.time.get_ticks()
            selected_character.start_expedition(current_time, dragon=dragon)
            chat_box.add_message(f"{selected_character.name} goes on an expedition...")
            selected_character = None
        else:
            chat_box.add_message("No valid character selected or is dead!")

    expedition_button = Button("Send Expedition", WIDTH-200, HEIGHT-100, 150, 50, expedition_callback, font)

    def fight_dragon_callback():
        nonlocal selected_character
        if dragon.is_defeated():
            chat_box.add_message("Dragon is already slain!")
            return
        if not selected_character or selected_character.is_dead:
            chat_box.add_message("Select a living character to fight the dragon!")
            return

        from dragon_battle import pokemon_style_fight
        result = pokemon_style_fight(selected_character, dragon, screen, font, chat_box)
        if result:
            chat_box.add_message("You overcame the dragon in Pokemon-style combat!")
        else:
            if selected_character.is_dead:
                chat_box.add_message("You died to the dragon!")
            else:
                chat_box.add_message("Fight ended, possibly by fleeing.")

    fight_dragon_button = Button("Fight Dragon", WIDTH-200, HEIGHT-40, 150, 50, fight_dragon_callback, font)

    def inventory_button_callback():
        if blocking_event_in_progress[0]:
            chat_box.add_message("Cannot open inventory now!")
            return
        if selected_character and not selected_character.is_dead:
            inventory_menu.open(selected_character)
        else:
            chat_box.add_message("No valid character selected or is dead!")

    inventory_button = Button("Inventory", WIDTH-200, HEIGHT-160, 150, 50, inventory_button_callback, font)

    # ask advisor
    ask_advisor_open = False
    question_texts = [
        "1) Which character is best to send?",
        "2) Should I skip a day now?",
        "3) Should I buy from trader now?",
        "4) Which item do I equip?",
        "5) Is it safe to fight the dragon?",
        "6) Are my stats good enough?"
    ]
    question_rects = []
    question_overlay_rect = pygame.Rect(20, 20, 300, 200)

    def ask_advisor_callback():
        if blocking_event_in_progress[0]:
            chat_box.add_message("Cannot ask advisor during an event!")
            return
        nonlocal ask_advisor_open
        ask_advisor_open = not ask_advisor_open

    ask_advisor_button = Button("Ask Advisor", WIDTH-370, HEIGHT-220, 150, 50, ask_advisor_callback, font)

    def draw_ask_advisor_overlay():
        pygame.draw.rect(screen, (30,30,30), question_overlay_rect)
        pygame.draw.rect(screen, (200,200,200), question_overlay_rect, 2)
        header = font.render("Ask the Advisor:", True, (255,255,255))
        screen.blit(header, (question_overlay_rect.x+10, question_overlay_rect.y+5))

        y_offset = 40
        spacing = 25
        question_rects.clear()

        for i, txt in enumerate(question_texts):
            rect = pygame.Rect(question_overlay_rect.x+10, question_overlay_rect.y + y_offset, 280, 20)
            question_rects.append(rect)
            pygame.draw.rect(screen, (80,80,80), rect)
            q_surf = font.render(txt, True, (255,255,255))
            screen.blit(q_surf, (rect.x+5, rect.y+2))
            y_offset += spacing

    def handle_ask_advisor_click(pos):
        for i, rect in enumerate(question_rects):
            if rect.collidepoint(pos):
                answer = get_advisor_answer(i)
                for line in answer.split("\n"):
                    chat_box.add_message(line)
                break

    def get_advisor_answer(q_index):
        if q_index == 0:
            return "Advisor: Bob has the best stats right now."
        elif q_index == 1:
            return "Advisor: Skipping a day might help if cooldown is high."
        elif q_index == 2:
            return "Advisor: Trader might have special items if you have enough coins."
        elif q_index == 3:
            return "Advisor: Equip your best gear to raise your chance."
        elif q_index == 4:
            return "Advisor: The dragon is tough. Check your HP!"
        elif q_index == 5:
            return "Advisor: Consider healing if HP < 50."
        return "Advisor doesn't understand that question."

    inventory_menu = InventoryMenu(
        x=WIDTH//4, y=HEIGHT//4,
        width=WIDTH//2, height=HEIGHT//2,
        font=font,
        chat_box=chat_box,
        shared_inv=shared_inventory
    )

    import sys
    sys.modules[__name__].trader_ui = trader_ui

    running = True
    while running:
        if all(c.is_dead for c in characters):
            if game_over_screen(screen, font):
                main()
            else:
                running = False
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if trader_ui.is_open():
                trader_ui.handle_event(event)
                continue

            if inventory_menu.is_open():
                inventory_menu.handle_event(event)
                continue

            if ask_advisor_open:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if question_overlay_rect.collidepoint(pos):
                        handle_ask_advisor_click(pos)

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if skip_day_button.is_clicked(pos):
                    skip_day_button.click()
                elif expedition_button.is_clicked(pos):
                    expedition_button.click()
                elif fight_dragon_button.is_clicked(pos):
                    fight_dragon_button.click()
                elif inventory_button.is_clicked(pos):
                    inventory_button.click()
                elif ask_advisor_button.is_clicked(pos):
                    ask_advisor_button.click()
                else:
                    clicked_any = False
                    for char in characters:
                        if char.is_clicked(pos) and not char.on_expedition and not char.is_dead:
                            selected_character = char
                            clicked_any = True
                            break
                    if not clicked_any:
                        selected_character = None

        # update expeditions
        curr_time = pygame.time.get_ticks()
        for c in characters:
            was_exped = c.on_expedition
            c.update_expedition_status(curr_time, dragon=dragon, shared_inv=shared_inventory)
            if was_exped and not c.on_expedition:
                if c.is_dead:
                    chat_box.add_message(f"{c.name} died on expedition!")
                    advisor.record_expedition_outcome(
                        c.health, c.food, c.get_damage_modifier(), c.get_damage_resistance(),
                        c.days_cooldown_left, day, 0
                    )
                else:
                    chat_box.add_message(f"{c.name} returned from expedition.")
                    advisor.record_expedition_outcome(
                        c.health, c.food, c.get_damage_modifier(), c.get_damage_resistance(),
                        c.days_cooldown_left, day, 1
                    )

        screen.fill(WHITE)

        for c in characters:
            is_sel = (c == selected_character and not c.is_dead)
            c.draw(screen, font, selected=is_sel)

        skip_day_button.draw(screen)
        expedition_button.draw(screen)
        fight_dragon_button.draw(screen)
        ask_advisor_button.draw(screen)
        if selected_character and not selected_character.is_dead:
            inventory_button.draw(screen)

        day_surf = font.render(f"Day: {day}", True, BLACK)
        screen.blit(day_surf, (WIDTH - 150, 20))

        drg_surf = font.render(f"Dragon HP: {dragon.hp}", True, (200,0,0))
        screen.blit(drg_surf, (WIDTH - 150, 50))

        coin_surf = font.render(f"Coins: {player_coins}", True, (200,200,0))
        screen.blit(coin_surf, (WIDTH - 150, 80))

        chat_box.draw(screen)
        inventory_menu.draw(screen)
        trader_ui.draw(screen)

        if ask_advisor_open:
            draw_ask_advisor_overlay()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
