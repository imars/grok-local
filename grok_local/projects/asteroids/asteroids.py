import pygame
import math
import random

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
ASTEROID_NUM = 100
SHIP_SPEED = 5
SHIP_ROTATION_SPEED = 0.5

class Ship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.radius = 20
        
    def rotate(self, direction):
        self.angle += direction * math.radians()
        
    def move(self, direction):
        self.x += math.cos(self.angle) * SHIP_SPEED * direction
        self.y -= math.sin(self.angle) * SHIP_SPEED * direction
        
    def draw(self, screen):
        pygame.draw.circle(screen, (0, 0, 0), (self.x, self.y), self.radius)

class Asteroid:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = random.uniform(0, 2 * math.pi)
        self.radius = 30
        self.velocity = (random.uniform(-1, 1), random.uniform(-1, 1)) * FPS
        
    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.angle += random.uniform(-1/FPS, 1/FPS)
        
    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), (self.x, self.y), self.radius)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    ship = Ship(400, 300)
    asteroids = [Asteroid(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(ASTEROID_NUM)]
    
    clock = pygame.time.Clock()
    key_right = False
    key_left = False
    
    while True:
        screen.fill((0, 0, 0))
        
        # Handle keyboard input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    ship.rotate(-SHIP_ROTATION_SPEED)
                    key_right = False
                elif event.key == pygame.K_RIGHT:
                    ship.rotate(SHIP_ROTATION_SPEED)
                    key_left = False
                elif event.key == pygame.K_UP:
                    ship.move((0, -1))
                    key_left = False
                elif event.key == pygame.K_DOWN:
                    ship.move((0, 1))
                    key_right = False
                    
        # Update asteroids
        for i in range(len(asteroids)):
            asteroids[i].update()
            
        # Check collisions
        for asteroid in asteroids:
            if (
                abs(ship.x - asteroid.x) < ship.radius + asteroid.radius and
                abs(ship.y - asteroid.y) < ship.radius + asteroid.radius
            ):
                print("Collision!")
                return
                
        # Draw everything
        ship.draw(screen)
        for asteroid in asteroids:
            asteroid.draw(screen)
            
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()