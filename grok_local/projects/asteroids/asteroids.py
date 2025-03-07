import pygame
import random
import math

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SHIP_SPEED = 5
ASTEROID_SPEED = 2
ASTEROID_SPAWN_RATE = 0.05  # Spawns asteroids every 1/0.05 ~20 seconds

class Ship:
    def __init__(self):
        self.image = pygame.Surface((40, 40))
        self.image.fill('white')
        self.rect = self.image.get_rect(center=(400, 300))
        self.velocity = math向量(0, 0)
        self.angle = 0
        
    def rotate(self, direction):
        self.angle += direction
        self.image = pygame.transform.rotate(self.image, -self.angle)
        
    def move(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.velocity.x = -SHIP_SPEED
        elif keys[pygame.K_RIGHT]:
            self.velocity.x = SHIP_SPEED
            
    def update(self):
        self.velocity.x += math.sin(self.angle) * ASTEROID_SPEED * 0.01
        self.rect.center = (self.image.get_width() // 2 + self.rect.centerx, 
                          self.image.get_height() // 2 + self.rect.centery)
        
class Asteroid:
    def __init__(self):
        self.image = pygame.Surface((30, 30))
        self.image.fill('gray')
        self.rect = self.image.get_rect(random.choice([(-800, -800), (800, -800), (-800, 800), (800, 800)]))
        self.velocity = math向量(0, 0)
        
    def update(self):
        self.velocity.x += random.uniform(-1, 1) * ASTEROID_SPEED * 0.02
        self.rect.centerx += self.velocity.x
        self.rect.centery += self.velocity.y
        
    def check_collision(self, objects):
        for obj in objects:
            if (self.rect.colliderect(obj.rect)):
                return True
        return False

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    ship = Ship()
    asteroids = [Asteroid() for _ in range(5)]
    
    def spawn_asteroids():
        if random.random() < ASTEROID_SPAWN_RATE:
            new_asteroid = Asteroid()
            asteroids.append(new_asteroid)
            
    running = True
    while running:
        screen.fill('black')
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        # Spawn asteroids
        spawn_asteroids()
        
        # Update game state
        ship.update()
        [a.update() for a in asteroids]
        
        # Check collisions
        ship_collisions = []
        for asteroid in asteroids:
            if asteroid.check_collision(ship):
                ship_collisions.append(asteroid)
                
            for other_asteroid in asteroids:
                if asteroid != other_asteroid and other_asteroid.check_collision(asteroid):
                    asteroidDeaths = [a for a in asteroids if a.rect == other_asteroid.rect]
                    asteroids.extend(a for a in asteroidDeaths)
                    break
                    
        # Remove dead asteroids
        new_asteroids = []
        for a in asteroids:
            if not a.dead:
                new_asteroids.append(a)
                
        asteroids = new_asteroids
        
        # Draw everything
        ship.image.fill('white')
        screen.blit(ship.image, (ship.rect.centerx - 20, ship.rect.centery - 20))
        
        for asteroid in asteroids:
            asteroid.image.fill('gray')
            screen.blit(asteroid.image, (asteroid.rect.centerx - 15, asteroid.rect.centery - 15))
            
        pygame.display.flip()
        clock.tick(60)
        
if __name__ == "__main__":
    main()