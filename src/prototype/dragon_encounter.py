# dragon_encounter.py
import pygame
import random
import constants
# from Dragon import generate_math_problem

def dragon_encounter_during_expedition(character, dragon):
    """
    Single puzzle approach for random expedition-based dragon fight.
    If the user chooses Attack => one puzzle. If correct => damage dragon, else character takes damage.
    Returns (survived, keep_loot).
    """
    screen = pygame.display.get_surface()
    font = pygame.font.SysFont(None, 28)

    action = show_attack_or_run_ui(screen, font, character)
    if action == "run":
        # run => 30% chance to die
        if random.random() < 0.3:
            return (False, False)
        else:
            # 60% chance to lose loot
            keep_loot = (random.random() >= 0.6)
            return (True, keep_loot)
    else:
        # Attack => do puzzle
        success = show_math_problem_ui_with_timer(screen, font, character, time_limit_seconds=constants.MATH_TIME_LIMIT)
        if success:
            dmg = int(character.getDamage() * character.get_damage_modifier())
            dragon.take_damage(dmg)
            if dragon.is_defeated():
                pass
            return (True, True)
        else:
            # character or random living char takes damage
            from maintProto import game_over_screen
            living_chars = get_all_living_characters()
            if living_chars:
                victim = random.choice(living_chars)
                dr = victim.get_damage_resistance()
                final_dmg = int(50*(1 - dr))
                victim.health -= final_dmg
                if victim.health <= 0:
                    victim.is_dead = True
            return (True, True)

def show_attack_or_run_ui(screen, font, character):
    clock = pygame.time.Clock()
    attack_rect = pygame.Rect(250,300,100,50)
    run_rect = pygame.Rect(450,300,100,50)
    choice = None

    while choice is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if attack_rect.collidepoint(pos):
                    choice = "attack"
                elif run_rect.collidepoint(pos):
                    choice = "run"

        screen.fill((30,30,30))
        t1 = font.render("Dragon Encounter!", True, (255,0,0))
        t2 = font.render(f"{character.name} must choose:", True, (255,255,255))
        t3 = font.render("Attack or Run?", True, (255,255,255))
        screen.blit(t1, (300,150))
        screen.blit(t2, (300,200))
        screen.blit(t3, (300,250))

        pygame.draw.rect(screen, (100,100,100), attack_rect)
        pygame.draw.rect(screen, (100,100,100), run_rect)
        a_surf = font.render("ATTACK", True, (255,255,255))
        r_surf = font.render("RUN", True, (255,255,255))
        screen.blit(a_surf, (attack_rect.x+10, attack_rect.y+10))
        screen.blit(r_surf, (run_rect.x+25, run_rect.y+10))

        pygame.display.flip()
        clock.tick(30)

    return choice

def show_math_problem_ui_with_timer(screen, font, character, time_limit_seconds=6):
    clock = pygame.time.Clock()
    # problem, answer = generate_math_problem()
    user_input = ""
    input_rect = pygame.Rect(300,300,200,50)

    start_time = pygame.time.get_ticks()
    done = False
    correct = False

    while not done:
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - start_time)/1000.0
        remain = time_limit_seconds - elapsed
        if remain <= 0:
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]
                elif event.key == pygame.K_RETURN:
                    try:
                        if int(user_input) == answer:
                            correct = True
                        else:
                            correct = False
                        done = True
                    except:
                        correct = False
                        done = True
                else:
                    if event.unicode.isdigit():
                        user_input += event.unicode

        screen.fill((0,0,0))
        p_surf = font.render(f"Math Problem: {problem} = ?", True, (255,255,255))
        screen.blit(p_surf, (250,200))

        pygame.draw.rect(screen, (200,200,200), input_rect)
        text_surf = font.render(user_input, True, (0,0,0))
        screen.blit(text_surf, (input_rect.x+5, input_rect.y+10))

        timer_surf = font.render(f"Time Left: {int(remain)}", True, (255,255,0))
        screen.blit(timer_surf, (300,250))

        pygame.display.flip()
        clock.tick(30)

    return correct and done

def get_all_living_characters():
    import maintProto
    if hasattr(maintProto, 'game_characters'):
        return [c for c in maintProto.game_characters if not c.is_dead]
    return []
