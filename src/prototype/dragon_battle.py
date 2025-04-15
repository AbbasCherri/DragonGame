# dragon_battle.py

import pygame
import sys
import random

def pokemon_style_fight(player_char, dragon, screen, font, chat_box):
    """
    Turn-based fight. On the player's turn, they pick a move.
    Then the dragon picks a move from its ML model.

    Now the dragon has 5 distinct moves:
      0=Dragon Breath, 1=Heal, 2=Claw, 3=Flee, 4=Focus
    If the dragon flees => we exit the fight w/ return False
    """
    clock = pygame.time.Clock()

    move_texts = ["Attack", "Use Item", "Run"]
    move_rects = []
    move_overlay = pygame.Rect(100, 300, 400, 150)

    done = False
    player_won = False

    def draw_battle_state():
        screen.fill((60, 60, 60))

        # Player HP
        pc_surf = font.render(f"{player_char.name} HP: {player_char.health}", True, (255,255,255))
        screen.blit(pc_surf, (50, 50))

        # Dragon HP
        dr_surf = font.render(f"Dragon HP: {dragon.hp}", True, (255, 100, 100))
        screen.blit(dr_surf, (350, 50))

        # Moves overlay for the player
        pygame.draw.rect(screen, (30,30,30), move_overlay)
        pygame.draw.rect(screen, (200,200,200), move_overlay, 2)

        prompt_surf = font.render("Choose a move:", True, (255,255,255))
        screen.blit(prompt_surf, (move_overlay.x+10, move_overlay.y+10))

        y_offset = move_overlay.y+40
        spacing = 40
        move_rects.clear()
        for i, txt in enumerate(move_texts):
            rect = pygame.Rect(move_overlay.x+10, y_offset, 100, 30)
            move_rects.append(rect)
            pygame.draw.rect(screen, (100,100,100), rect)
            t_surf = font.render(txt, True, (255,255,255))
            screen.blit(t_surf, (rect.x+5, rect.y+5))
            y_offset += spacing

        chat_box.draw(screen)
        pygame.display.flip()

    def handle_player_move(choice_index):
        """
        Player moves:
         0 => Attack
         1 => Use Item
         2 => Run
        """
        if choice_index == 0:
            # Attack
            base_damage = 50  # or player_char.getDamage() 
            final_dmg = random.randint(int(base_damage*0.8), int(base_damage*1.2))
            dragon.hp -= final_dmg
            chat_box.add_message(f"{player_char.name} ATTACKS for {final_dmg} dmg!")
        elif choice_index == 1:
            # Use item => heal 30, or some logic
            old_hp = player_char.health
            heal_amt = 30
            player_char.health = min(player_char.max_health, player_char.health+heal_amt)
            chat_box.add_message(f"{player_char.name} uses an item. HP: {old_hp}->{player_char.health}")
        elif choice_index == 2:
            # Run => 50% chance
            if random.random() < 0.5:
                chat_box.add_message(f"{player_char.name} successfully ran away from the dragon!")
                return "fled"
            else:
                chat_box.add_message("Failed to run away!")
        return "continue"

    while not done:
        draw_battle_state()

        if dragon.is_defeated():
            chat_box.add_message("Dragon is already defeated!")
            player_won = True
            break
        if player_char.health <= 0:
            player_char.is_dead = True
            player_won = False
            break

        # Player picks a move
        player_move = None
        while player_move is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    for i, r in enumerate(move_rects):
                        if r.collidepoint(pos):
                            player_move = i
                            break
            clock.tick(30)

        outcome = handle_player_move(player_move)
        if outcome == "fled":
            # The player fled => fight ends
            player_won = False
            break

        if dragon.hp <= 0:
            chat_box.add_message("Dragon has been slain!")
            player_won = True
            break
        if player_char.health <= 0:
            player_char.is_dead = True
            player_won = False
            break

        # DRAGON's turn: pick a move from the model
        result = dragon.choose_and_execute_move(player_char, screen, font, chat_box)
        if result == "fled":
            # Dragon flees => fight ends => player "wins" but no loot, or however you want
            # We'll treat it as a break => no kill
            chat_box.add_message("The dragon fled the scene!")
            player_won = False
            break

        # Check HP after dragon move
        if player_char.health <= 0:
            player_char.is_dead = True
            chat_box.add_message(f"{player_char.name} died from the dragon's move!")
            player_won = False
            break
        if dragon.is_defeated():
            chat_box.add_message("Dragon is defeated from its own poor choice or the prior attack!")
            player_won = True
            break

    # final display
    draw_battle_state()
    pygame.time.wait(1500)
    return player_won
