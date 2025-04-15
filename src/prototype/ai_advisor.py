# ai_advisor.py
import os
import pickle
import numpy as np
from sklearn.tree import DecisionTreeClassifier

class AIAdvisor:
    def __init__(self, model_path="advisor_model.pkl"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(model_path):
            model_path = os.path.join(script_dir, model_path)
        self.model_path = model_path

        self.model = None
        self.loaded = False
        self.new_data_log = []

        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    loaded_model = pickle.load(f)
                if isinstance(loaded_model, DecisionTreeClassifier):
                    self.model = loaded_model
                    self.loaded = True
                    print(f"AIAdvisor: Loaded DecisionTreeClassifier from {self.model_path}")
                else:
                    print("AIAdvisor: The file is not a DecisionTreeClassifier.")
            except Exception as e:
                print(f"AIAdvisor: Error loading model => {e}")
        else:
            print("AIAdvisor: No existing model. Starting fresh.")

    def is_loaded(self):
        return self.loaded

    def record_expedition_outcome(self, health, food, weapon_mod, armor_res, cooldown, day, success):
        """
        Logs a single expedition outcome for incremental training.
        EXACT 6 features:
         [health, food, weapon_mod, armor_res, cooldown, day] 
        success => 1 (survived) or 0 (died).
        """
        self.new_data_log.append({
            "health": health,
            "food": food,
            "weapon_mod": weapon_mod,
            "armor_res": armor_res,
            "cooldown": cooldown,
            "day": day,
            "success": success
        })

    def retrain_model(self):
        """
        Retrains the DecisionTreeClassifier using the 6 features:
         [health, food, weapon_mod, armor_res, cooldown, day].
        """
        if not self.new_data_log:
            print("AIAdvisor: No new data to retrain on.")
            return False

        X = []
        Y = []
        for row in self.new_data_log:
            X.append([
                float(row["health"]),
                float(row["food"]),
                float(row["weapon_mod"]),
                float(row["armor_res"]),
                float(row["cooldown"]),
                float(row["day"])
            ])
            Y.append(row["success"])

        X = np.array(X, dtype=float)
        Y = np.array(Y, dtype=int)

        # If we only have one class in Y => the model
        # will produce a single column for predict_proba, 
        # so we might want to handle that gracefully
        if len(np.unique(Y)) == 1:
            unique_class = np.unique(Y)[0]
            print(f"AIAdvisor: WARNING - Training data has only one class: {unique_class}")
            print("All predictions will be that single class.")
        else:
            print(f"AIAdvisor: Training data has {len(np.unique(Y))} classes => good to go.")

        dt = DecisionTreeClassifier(max_depth=5, random_state=15)
        dt.fit(X, Y)
        self.model = dt
        self.loaded = True

        # Save updated model
        try:
            with open(self.model_path, "wb") as f:
                pickle.dump(self.model, f)
            print(f"AIAdvisor: Retrained model saved to {self.model_path}")
        except Exception as e:
            print(f"AIAdvisor: Error saving updated model => {e}")

        self.new_data_log.clear()
        return True

    def predict_expedition_success(self, health, food, weapon_mod, armor_res, cooldown, day):
        """
        EXACT 6 features => [health, food, weapon_mod, armor_res, cooldown, day].
        If single-class, handle it gracefully.
        """
        if not self.loaded or self.model is None:
            return 0.5

        features = np.array([[health, food, weapon_mod, armor_res, cooldown, day]], dtype=float)
        # predict_proba => shape [1, n_classes]
        proba = self.model.predict_proba(features)

        if proba.shape[1] == 1:
            # Means only one class was in training data
            # If that single class is "0", we interpret success prob=0
            # If that single class is "1", we interpret success prob=1
            # But we need to see what the model's classes_ are
            single_class = self.model.classes_[0]  # e.g. [0], [1]
            if single_class == 1:
                return 1.0
            else:
                return 0.0
        else:
            # We have 2 classes => normal
            return proba[0][1]

    def get_advanced_advice(self, health, food, weapon_mod, armor_res, cooldown, day, shared_inv):
        """
        Merges ML-based probability with rule-based logic, returning multi-line advice.
        """
        prob = self.predict_expedition_success(health, food, weapon_mod, armor_res, cooldown, day)
        lines = []
        lines.append(f"Expedition success chance: ~{int(prob*100)}%")

        if prob < 0.4:
            lines.append(" - Odds are low. Consider healing or skipping a day.")
            if shared_inv.get("medical_kit", 0) > 0 or shared_inv.get("bandages", 0) > 0:
                lines.append(" - You have medical items that might improve survival.")
            if shared_inv.get("banana", 0) and food < 50:
                lines.append(" - You have bananas; using one might help.")
        elif prob < 0.7:
            lines.append(" - Moderate odds. Better gear or a day of rest might help.")
        else:
            lines.append(" - Looks good! A good time to embark.")

        if day > 20:
            lines.append(" - The day count is high; do not wait too long.")

        if cooldown > 2:
            lines.append(" - The character is recovering; skipping a day might help.")
        return "\n".join(lines)
