import pygame
import sys
import time

pygame.init()

# Dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Interactive ball with gravity")

# Colors
WHITE = (255, 255, 255)
BLUE = (30, 144, 255)

# Ball parameters
radius = 20
x, y = WIDTH // 2, HEIGHT // 2
vx, vy = 0, 0
gravity = 0.5
bounce_factor = 0.85
friction = 0.98

# Mouse interaction
dragging = False
last_mouse_pos = None
last_time = None

clock = pygame.time.Clock()

while True:
    screen.fill(WHITE)
    dt = clock.tick(60) / 1000  # time in seconde

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if (x - mx) ** 2 + (y - my) ** 2 <= radius ** 2:
                dragging = True
                last_mouse_pos = (mx, my)
                last_time = time.time()
                vx, vy = 0, 0  # We stop the mouvement during the drag

        elif event.type == pygame.MOUSEBUTTONUP:
            if dragging:
                dragging = False
                mx, my = pygame.mouse.get_pos()
                now = time.time()
                dt_drag = now - last_time if last_time else 0.01
                dx = mx - last_mouse_pos[0]
                dy = my - last_mouse_pos[1]
                # We calculate the speed
                vx = dx / dt_drag * 0.01
                vy = dy / dt_drag * 0.01

    if dragging:
        x, y = pygame.mouse.get_pos()
        last_mouse_pos = (x, y)
        last_time = time.time()
    else:
        # Normal physic
        vy += gravity
        x += vx
        y += vy

        # Rebond on screen sides
        if x - radius < 0:
            x = radius
            vx = -vx * bounce_factor
        elif x + radius > WIDTH:
            x = WIDTH - radius
            vx = -vx * bounce_factor

        if y + radius > HEIGHT:
            y = HEIGHT - radius
            vy = -vy * bounce_factor
            vx *= friction
            if abs(vy) < 1:
                vy = 0
        elif y + radius <= 0:
            y = radius
            vy *= -bounce_factor

    # Draw the ball
    pygame.draw.circle(screen, BLUE, (int(x), int(y)), radius)
    pygame.display.flip()
