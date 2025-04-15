# chat_box.py

import pygame

class ChatBox:
    def __init__(self, x, y, width, height, font, max_messages=100):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.messages = []
        self.max_messages = max_messages

        self.bg_color = (230, 230, 230)
        self.text_color = (0, 0, 0)
        self.border_color = (100, 100, 100)

    def add_message(self, msg: str):
        self.messages.append(msg)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)

        padding = 5
        line_height = self.font.get_linesize()
        num_visible_lines = (self.rect.height - padding*2)//line_height

        visible_msgs = self.messages[-num_visible_lines:] if num_visible_lines>0 else self.messages
        current_y = self.rect.bottom - padding - line_height

        for msg in reversed(visible_msgs):
            text_surf = self.font.render(msg, True, self.text_color)
            screen.blit(text_surf, (self.rect.x + padding, current_y))
            current_y -= line_height
