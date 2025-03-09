<code>
import pygame
import random
import math

# Initialize Pygame and game window
pygame.init()
window_size = (800, 600)
screen = pygame.display.set_mode(window_size)
clock = pygame.time.Clock()
font = pygame.font.Font(None, 74)

class Ship:
    def __init__(self):
        self.position = [400, 300]
        self.velocity = [0, 0]
        self.angle = 0
        self.radius = 20
    
    def rotate(self, direction):
        self.angle += direction
        self.velocity = [
            math.cos(math.radians(self.angle)) * self.velocity[1],
            -math.sin(math.radians(self.angle)) * self.velocity[1]
        ]

class Asteroid:
    def __init__(self):
        self.position = [random.randint(0, window_size[0]), random.randint(0, window_size[1])]
        self.radius = random.uniform(30, 50)
        self.angle = random.uniform(0, math.pi * 2)
        self.velocity = [
            random.choice([5, -5, 5, -5]) * math.cos(math.radians(self.angle)),
            random.choice([5, -5, 5, -5]) * math.sin(math.radians(self.angle))
        ]

def is_colliding(ship, asteroid):
    dx = ship.position[0] - asteroid.position[0]
    dy = ship.position[1] - asteroid.position[1]
    distance = math.sqrt(dx**2 + dy**2)
    if distance < (ship.radius + asteroid.radius):
        return True
    return False

# Game variables
game_over = False
score = 0
space_bar_pressed = False

# Create ship and asteroids
ship = Ship()
asteroids = []
for _ in range(5):
    asteroids.append(Asteroid())

while not game_over:
    screen.fill((0, 0, 0))
    
    # Handle key presses
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and not space_bar_pressed:
                ship.angle += 2
                space_bar_pressed = False
            elif event.key == pygame.K_DOWN and not space_bar_pressed:
                ship.angle -= 2
                space_bar_pressed = False
            elif event.key == pygame.K_LEFT:
                ship.velocity[0] = math.cos(math.radians(ship.angle)) * ship.velocity[1]
                ship.velocity[1] = -math.sin(math.radians(ship.angle)) * ship.velocity[1]
            elif event.key == pygame.K_RIGHT:
                ship.velocity[0] = math.cos(math.radians(ship.angle)) * ship.velocity[1]
                ship.velocity[1] = math.sin(math.radians(ship.angle)) * ship.velocity[1]
            elif event.key == pygame.K_SPACE and game_over:
                space_bar_pressed = True
    
    # Update positions
    if not game_over:
        ship.position[0] += ship.velocity[0]
        ship.position[1] += ship.velocity[1]
        
        for i, asteroid in enumerate(asteroids):
            asteroid.position[0] += asteroid.velocity[0]
            asteroid.position[1] += asteroid.velocity[1]
            
            if is_colliding(ship, asteroid):
                game_over = True
                score = len(asteroids) - i - 1
                
    # Draw objects
    pygame.draw.circle(screen, (255, 0, 0), ship.position[0], ship.radius)
    for asteroid in asteroids:
        pygame.draw.circle(screen, (200, 200, 200), asteroid.position[0], asteroid.radius)
    
    text = font.render(f'Score: {score}', True, (255, 255, 255))
    screen.blit(text, (10, 50))
    
    if game_over:
        pygame.display.set_caption("Press SPACE to restart")
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
</code>