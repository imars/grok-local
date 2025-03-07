import pygame
import random
import math
import time

# Set up constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SHIP_SPEED = 5
SHIP_ROTATION_SPEED = 0.3
ASTEROID_SPEED = 1
ASTEROID_SIZE_MIN = 20
ASTEROID_SIZE_MAX = 30
ASTEROID_COLOR_SPACE = (0, 0, 255)  # Blue color palette

class Ship:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.angle = 0
        self.image = pygame.image.load("ship.png").convert_alpha()
    
    def update(self, keys):
        # Handle movement and rotation based on key inputs
        speed = SHIP_SPEED
        dx = 0
        dy = 0
        
        if pygame.KUP in keys or pygame.KDOWN in keys:
            dy = -speed
        if pygame.KDP in keys or pygame.KUP in keys:
            dy = +speed
            
        if pygame.KLEFT in keys:
            self.x -= speed * math.cos(self.angle)
        if pygame.KRIGHT in keys:
            self.x += speed * math.cos(self.angle)
        
        # Rotate ship based on arrow keys
        if pygame.KUP in keys:
            self.angle -= SHIP_ROTATION_SPEED
        if pygame.KDOWN in keys:
            self.angle += SHIP_ROTATION_SPEED
            
        self.image = pygame.transform.rotate(self.image, -self.angle)

class Asteroid:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.size = random.uniform(ASTEROID_SIZE_MIN, ASTEROID_SIZE_MAX)
        self.image = pygame.image.frombuffer(ASTEROID_COLOR_SPACE[int(random.uniform(0, 255))], 
                                       (self.size//2, self.size//2))
        # Randomize position slightly within the buffer
        self.x += random.uniform(-self.size/2, self.size/2)
        self.y += random.uniform(-self.size/2, self.size/2)
    
    def update(self):
        self.x = (self.x + random.uniform(-ASTEROID_SPEED, ASTEROID_SPEED))
        if self.x < 0 or self.x > SCREEN_WIDTH:
            self.x = max(0, min(SCREEN_WIDTH, self.x))
    
    def collision(self, ship):
        # Check bounding box collision
        return (abs(self.x - ship.x) <= self.size/2 + 1 and 
                abs(self.y - ship.y) <= self.size/2 + 1)

def draw_text(text, x, y, size=20):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, (0, 0, 0))
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

def draw_screen():
    # Clear the screen
    screen.fill((0, 0, 0))
    
    # Draw asteroids
    for asteroid in asteroids:
        screen.blit(asteroid.image, (asteroid.x - asteroid.size//2, asteroid.y - asteroid.size//2))
    
    # Draw ship
    screen.blit(ship.image, 
               (ship.x + ship.size//2, ship.y + ship.size//2))

def handle_keys(keys):
    global ship, asteroids, game_over
    if not game_over:
        ship.update(keys)
        for asteroid in asteroids:
            asteroid.update()
        
        # Check collisions
        if any(asteroid.collision(ship) for asteroid in asteroids):
            print("Game Over!")
            game_over = True
        
        # Add new asteroids periodically
        if time.time() % 30 < current_time:
            asteroids.append(Asteroid())
            
    return time.time()

def main():
    global screen, ship, asteroids, game_over
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Asteroids Game")
    
    ship = Ship()
    asteroids = []
    game_over = False
    current_time = 0
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        time.sleep(1/60)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                
        screen.fill((0, 0, 0))
        handle_keys(pygame.key.get_pressed())
        draw_screen()
        
        current_time = time.time()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()