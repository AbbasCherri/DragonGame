# dragon_moves.py

import os
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression

class DragonMoveModel:
    def __init__(self, model_file="dragon_move_model.pkl"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(model_file):
            model_file = os.path.join(script_dir, model_file)

        self.model_path = model_file
        self.model = None
        self.loaded = False
        self.new_data = []  # logs new (features, move_label) for retraining
        self.num_moves = 5  # e.g., 5 possible moves

        # Attempt load
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    loaded_model = pickle.load(f)
                if hasattr(loaded_model, "predict") and hasattr(loaded_model, "predict_proba"):
                    self.model = loaded_model
                    self.loaded = True
                    print(f"DragonMoveModel: Loaded from {self.model_path}")
                else:
                    print("DragonMoveModel: The file isn't a valid sklearn model.")
            except Exception as e:
                print(f"DragonMoveModel: Error loading => {e}")
        else:
            print("DragonMoveModel: No existing model file. Starting fresh.")

    def record_move_example(self, features, move_label):
        """
        features => e.g. [dragonHP, playerHP, isDragonFocused, focusBoost]
        move_label => integer in [0..4], representing the chosen move
        """
        self.new_data.append((features, move_label))

    def retrain_model(self):
        """
        Re-train the model. If we only have one class in new_data, skip to avoid
        ValueError: 'needs samples of at least 2 classes'.
        """
        if not self.new_data:
            print("DragonMoveModel: No new data to retrain on.")
            return

        X = []
        Y = []
        for (feat, lab) in self.new_data:
            X.append(feat)
            Y.append(lab)

        X = np.array(X, dtype=float)
        Y = np.array(Y, dtype=int)

        # Check for multiple classes
        unique_classes = np.unique(Y)
        if len(unique_classes) < 2:
            print(f"DragonMoveModel: Only one class in new data (class={unique_classes[0]}) => skipping training.")
            # We do not update the model, so old model stays loaded
            self.new_data.clear()
            return

        # Otherwise => we can train
        lr = LogisticRegression(solver='lbfgs', multi_class='multinomial', max_iter=200)
        lr.fit(X, Y)
        self.model = lr
        self.loaded = True
        self.new_data.clear()

        # Save updated model
        try:
            with open(self.model_path, "wb") as f:
                pickle.dump(self.model, f)
            print(f"DragonMoveModel: Retrained and saved to {self.model_path}")
        except Exception as e:
            print(f"DragonMoveModel: Error saving => {e}")

    def choose_move(self, features):
        """
        Predict a move label. If no valid model, fallback to random.
        """
        if not self.loaded or self.model is None:
            import random
            return random.randint(0, self.num_moves-1)

        X = np.array([features], dtype=float)
        try:
            move_pred = self.model.predict(X)[0]
            return move_pred
        except Exception as e:
            print(f"DragonMoveModel: Predict error => {e}")
            import random
            return random.randint(0, self.num_moves-1)
