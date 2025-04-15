# events.py
import random
import pygame
from constants import POSITIVE_EVENT_CHANCE, get_random_int
import constants
import trader_event  # Our new trader system

def handle_daily_events(characters, screen, font, chat_box, set_blocking_event, dragon):
    """
    We'll do 3 daily events. 
    Add a random chance to trigger a Trader Event. 
    If triggered, we open the trader UI overlay.
    """
    for _ in range(3):
        n = get_random_int()
        if n % 2 != 0:
            continue

        # Suppose if n is in 20..25 => trader event
        if 20 <= n <= 25:
            # Trader arrives
            chat_box.add_message("A traveling trader appears with exclusive items!")
            set_blocking_event(True)
            # We'll open the trader UI here. We'll assume we have a reference to a TraderUI object somewhere.
            # The user might pass it in or keep it global. We'll assume a global approach for demonstration:
            import maintProto
            if hasattr(maintProto, 'trader_ui'):
                maintProto.trader_ui.open()
                # We'll block until user closes it
                # We'll do a mini loop or rely on the main loop to show the UI, then wait
                # for the user to close it. We'll break out of daily event chain for now.
            set_blocking_event(False)
            continue

        handle_dilemma_event(n, characters, screen, font, chat_box, set_blocking_event, dragon)

def handle_dilemma_event(n, characters, screen, font, chat_box, set_blocking_event, dragon):
    living_chars = [c for c in characters if not c.is_dead]
    if not living_chars:
        return

    character = random.choice(living_chars)

    # Let's keep the existing special range for dragon day
    if 75 < n <= 80 and dragon and not dragon.is_defeated():
        choice = ask_event_choice(screen, font, "Dragon day encounter! Fight? (Yes => puzzle, No => all die)", set_blocking_event)
        if choice == "yes":
            from dragon_encounter import show_math_problem_ui_with_timer, get_all_living_characters
            success = show_math_problem_ui_with_timer(screen, font, character, time_limit_seconds=dragon_time_limit())
            if success:
                dmg = int(character.getDamage() * character.get_damage_modifier())
                dragon.take_damage(dmg)
                chat_box.add_message(f"{character.name} hit the dragon for {dmg}!")
                if dragon.is_defeated():
                    chat_box.add_message("The dragon has been slain!")
            else:
                living = get_all_living_characters()
                if living:
                    victim = random.choice(living)
                    final_dmg = int(50 * (1 - victim.get_damage_resistance()))
                    victim.health -= final_dmg
                    chat_box.add_message(f"{victim.name} took {final_dmg} dmg from dragon!")
                    if victim.health <= 0:
                        victim.is_dead = True
                        chat_box.add_message(f"{victim.name} died!")
        else:
            for c in living_chars:
                c.is_dead = True
            chat_box.add_message("No one fought the dragon. Everyone died!")
        return

    # Otherwise, do normal event logic
    choice = ask_event_choice(screen, font, event_prompt(n, character), set_blocking_event)
    apply_choice_effect(n, choice, character, characters, chat_box)

def ask_event_choice(screen, font, prompt_text, set_blocking_event):
    set_blocking_event(True)
    clock = pygame.time.Clock()
    yes_rect = pygame.Rect(250,300,100,50)
    no_rect  = pygame.Rect(450,300,100,50)
    choice = None

    while choice is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if yes_rect.collidepoint(pos):
                    choice = "yes"
                elif no_rect.collidepoint(pos):
                    choice = "no"

        screen.fill((30,30,30))
        lines = wrap_text(prompt_text, font, 500)
        y_offset = 150
        for line in lines:
            line_surf = font.render(line, True, (255,255,255))
            screen.blit(line_surf, (200, y_offset))
            y_offset += 30

        pygame.draw.rect(screen, (100,100,100), yes_rect)
        pygame.draw.rect(screen, (100,100,100), no_rect)

        yes_surf = font.render("YES", True, (255,255,255))
        no_surf  = font.render("NO", True, (255,255,255))
        screen.blit(yes_surf, (yes_rect.x+25, yes_rect.y+10))
        screen.blit(no_surf,  (no_rect.x+30,  no_rect.y+10))

        pygame.display.flip()
        clock.tick(30)

    set_blocking_event(False)
    return choice

def event_prompt(n, character):
    if 0 <= n <= 6:
        return "A dealer arrives, no real choice needed. (Ok => no effect)?"
    elif 6 < n <= 20:
        return f"{character.name}: Bunker is broken, fix it? (Yes/No)"
    elif 20 < n <= 30:
        return f"{character.name}: Explore rumored cave? (Yes/No)"
    elif 30 < n <= 50:
        return f"{character.name}: Play hide & seek? (Yes/No)"
    elif 50 < n <= 75:
        return f"{character.name}: Someone is knocking, open door? (Yes/No)"
    elif 80 < n <= 90:
        return f"{character.name} found a book. Read it? (Yes/No)"
    else:
        return f"{character.name} wants to train? (Yes/No)"

def apply_choice_effect(n, choice, character, characters, chat_box):
    living_chars = [c for c in characters if not c.is_dead]
    if n <= 6:
        chat_box.add_message("Dealer event: no big effect.")
        return
    if 6 < n <= 20:
        if choice == "yes":
            import random
            if random.random() < POSITIVE_EVENT_CHANCE:
                chat_box.add_message(f"{character.name} fixed the bunker with no issues.")
            else:
                dmg = random.randint(5, 15)
                character.health = max(0, character.health - dmg)
                chat_box.add_message(f"{character.name} got sick! -{dmg} HP.")
        else:
            import random
            victim = random.choice(living_chars)
            dmg = random.randint(5, 15)
            victim.health = max(0, victim.health - dmg)
            chat_box.add_message(f"{victim.name} got sick because the bunker wasn't fixed! -{dmg} HP.")

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

def dragon_time_limit():
    return constants.MATH_TIME_LIMIT
