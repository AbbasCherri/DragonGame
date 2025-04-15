# Dragon.py
import random
from dragon_moves import DragonMoveModel

class Dragon:
    def __init__(self):
        self.hp = 1500
        self.base_attack = 50
        self.focus_boost = 1.0  # if Focus is used, this can go up
        self.move_model = DragonMoveModel("dragon_move_model.pkl")  # or default
        # The dragon might store some ephemeral state like "is_focused"
        self.is_focused = False

    def is_defeated(self):
        return self.hp <= 0

    def choose_and_execute_move(self, player_char, screen, font, chat_box):
        """
        Called each turn in the pokemon_style_fight. We'll gather features,
        pick a move via self.move_model, apply the move, and record the example.
        If Flee => we call retrain_model afterwards.
        """
        # Build features for the model. For demonstration, let's pick 4 features:
        # [dragonHP, playerHP, is_focused=1/0, focus_boost].
        # We'll keep it consistent with the training approach:
        dHP = float(self.hp)
        pHP = float(player_char.health)
        is_focused_num = 1.0 if self.is_focused else 0.0
        focus_scale = float(self.focus_boost)
        features = [dHP, pHP, is_focused_num, focus_scale]

        move_label = self.move_model.choose_move(features)
        # 0=Dragon Breath, 1=Heal, 2=Claw, 3=Flee, 4=Focus

        # We'll record the example for future training
        self.move_model.record_move_example(features, move_label)

        if move_label == 0:
            # DRAGON BREATH => High damage => 60
            # but the dragon can't do anything next turn => we can store a "skip turn" next time
            dmg = int(60 * self.focus_boost)
            player_char.health -= dmg
            chat_box.add_message(f"Dragon uses DRAGON BREATH for {dmg} damage!")
            # Next turn skip => we can do it by setting a special var, or
            # for demonstration, let's set is_focused = False if you want
        elif move_label == 1:
            # HEAL => +100 HP
            old_hp = self.hp
            self.hp = min(self.hp+100, 2000)  # cap or no?
            chat_box.add_message(f"Dragon casts HEAL! HP: {old_hp} -> {self.hp}")
        elif move_label == 2:
            # CLAW => 10% damage
            # combine with baseAttack * focusBoost
            raw_attack = self.base_attack * 0.1 * self.focus_boost
            dmg = int(raw_attack)
            player_char.health -= dmg
            chat_box.add_message(f"Dragon uses CLAW for {dmg} damage!")
        elif move_label == 3:
            # FLEE => the dragon runs away, healing 20%
            heal_amount = int(self.hp * 0.2)
            old_hp = self.hp
            self.hp += heal_amount
            chat_box.add_message(f"Dragon FLEES! Heals {heal_amount} => {old_hp}->{self.hp}")
            chat_box.add_message("Combat ends — player returns to main screen.")
            # retrain the model
            self.move_model.retrain_model()
            return "fled"
        elif move_label == 4:
            # FOCUS => increases the dragon's base attack scale
            self.focus_boost += 0.2
            chat_box.add_message("Dragon focuses, raising its attack power!")
        else:
            # Fallback => random
            chat_box.add_message("Dragon hesitates... does nothing.")
        return "continue"

    def skip_turn_if_needed(self):
        # If you'd like to replicate "Dragon Breath requires skip next turn," 
        # you can track a boolean "skipNextTurn" or something. 
        pass
