# ButtonProto.py

import pygame
from constants import *

class Button:
    def __init__(self, text, x, y, width, height, callback, font,
                 bg_color=(100, 100, 100), text_color=(255, 255, 255)):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.callback = callback
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_color, self.rect)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def click(self):
        self.callback()
