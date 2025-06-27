import pygame
import math

pygame.init()

# Fenetre
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# --- Fonctions utilitaires pour le GJK ---
def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]

def vector_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])

def vector_neg(v):
    return (-v[0], -v[1])

def triple_product(a, b, c):
    ac = dot(a, c)
    bc = dot(b, c)
    return (b[0] * ac - a[0] * bc, b[1] * ac - a[1] * bc)

def support(shape1, shape2, direction):
    def farthest_point(shape, d):
        return max(shape, key=lambda p: dot(p, d))

    p1 = farthest_point(shape1, direction)
    p2 = farthest_point(shape2, [-direction[0], -direction[1]])
    return (p1[0] - p2[0], p1[1] - p2[1])

def handle_simplex(simplex, direction):
    if len(simplex) == 2:
        B, A = simplex
        AB = vector_sub(B, A)
        AO = vector_neg(A)
        direction[0], direction[1] = triple_product(AB, AO, AB)
    elif len(simplex) == 3:
        C, B, A = simplex
        AB = vector_sub(B, A)
        AC = vector_sub(C, A)
        AO = vector_neg(A)

        AB_perp = triple_product(AC, AB, AB)
        AC_perp = triple_product(AB, AC, AC)

        if dot(AB_perp, AO) > 0:
            simplex.remove(C)
            direction[0], direction[1] = AB_perp
        elif dot(AC_perp, AO) > 0:
            simplex.remove(B)
            direction[0], direction[1] = AC_perp
        else:
            return True
    return False

def gjk(shape1, shape2):
    direction = [1, 0]
    simplex = [support(shape1, shape2, direction)]
    direction = [-simplex[0][0], -simplex[0][1]]

    while True:
        A = support(shape1, shape2, direction)
        if dot(A, direction) <= 0:
            return False

        simplex.append(A)

        if handle_simplex(simplex, direction):
            return True

# --- Démo ---
def translate_shape(shape, offset):
    return [(x + offset[0], y + offset[1]) for x, y in shape]

square = [(-30, -30), (30, -30), (30, 30), (-30, 30)]
triangle = [(0, -40), (40, 40), (-40, 40)]

running = True
static_pos = (WIDTH // 2, HEIGHT // 2)
moving_pos = list(pygame.mouse.get_pos())

while running:
    screen.fill((255, 255, 255))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if pygame.mouse.get_pressed()[0]:
        moving_pos = list(pygame.mouse.get_pos())

    static_shape = translate_shape(square, static_pos)
    moving_shape = translate_shape(triangle, moving_pos)

    # Collision
    is_colliding = gjk(static_shape, moving_shape)

    # Dessin
    pygame.draw.polygon(screen, (0, 255, 0) if not is_colliding else (255, 0, 0), static_shape, 2)
    pygame.draw.polygon(screen, (0, 0, 255), moving_shape, 2)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
