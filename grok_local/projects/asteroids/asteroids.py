import pygame
from settings import *
import random
from ship import Ship
from asteroid import Asteroid

class Game:
    def __init__(self):
        self.ship = Ship()
        self.asteroids = []
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("Asteroids")
    
    def spawn_asteroid(self):
        size = random.choice([10, 20, 30])
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        dx = random.choice([-1, 1]) * random.uniform(2, 5)
        dy = random.choice([-1, 1]) * random.uniform(2, 5)
        return Asteroid(x, y, size, dx, dy)
    
    def check_collision(self, ship_pos, asteroids):
        for asteroid in asteroids:
            if self.ship.check_collision(asteroid):
                print("Game Over!")
                return False
        return True
    
    def main_loop(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            self.screen.fill(BLACK)
            
            # Handle keyboard input
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.ship.move_left()
            elif keys[pygame.K_RIGHT]:
                self.ship.move_right()
            elif keys[pygame.K_UP]:
                self.ship.move_up()
            
            # Spawn new asteroids at random intervals
            if random.random() < 0.015:
                self.asteroids.append(self.spawn_asteroid())
            
            # Update positions and check for collisions
            self.ship.update()
            self.asteroids = [a for a in self.asteroids if not a.decompose()]
            running = self.check_collision(self.ship.position, self.asteroids)
            
            # Draw elements
            pygame.draw.rect(self.screen, WHITE, self.ship.rectangle)
            for asteroid in self.asteroids:
                pygame.draw.rect(self.screen, GREY, asteroid.rectangle)
            
            pygame.display.flip()
            clock.tick(FPS)

# Initialize the game
game = Game()
game.main_loop()