import pygame
from settings import *

# Initialize Pygame and set up display
pygame.init()
display_width = 800
display_height = 600

# Create game objects
ship = Ship(display_width//2, display_height//2)
asteroids = [Asteroid(max(0, 0), max(0, 0))]

# Game loop
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Handle ship movement and asteroid collisions here
    clock.tick(60)
pygame.quit()