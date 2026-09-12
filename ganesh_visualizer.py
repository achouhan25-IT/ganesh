import pygame
import cv2
import numpy as np
import random
import math
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

IMAGE_PATH = os.path.join(SCRIPT_DIR, 'image.png')
if not os.path.exists(IMAGE_PATH):
    IMAGE_PATH = os.path.join(SCRIPT_DIR, 'image_2.png')

WIDTH, HEIGHT = 1280, 720  
FPS = 60

def create_sharp_dot(color, size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (0, 0, size, size))
    return surf

def create_glow_particle(color, size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    pygame.draw.circle(surf, (*color, 80), (center, center), center)
    pygame.draw.circle(surf, (*color, 255), (center, center), max(1, center // 2))
    return surf

def create_flower_sprite(base_color, size=12):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    petal_radius = max(2, size // 3)
    
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        px = center + int(math.cos(rad) * (size / 3.5))
        py = center + int(math.sin(rad) * (size / 3.5))
        pygame.draw.circle(surf, base_color, (int(px), int(py)), petal_radius)
        
    pygame.draw.circle(surf, (255, 215, 0), (center, center), max(2, petal_radius - 1))
    pygame.draw.circle(surf, (255, 100, 0), (center, center), max(1, petal_radius - 2))
    return surf

def create_glossy_pastel_aura(w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, int(h * 0.45) 
    max_r = int(math.hypot(cx, cy)) 
    
    for r in range(max_r, 0, -5):
        factor = r / max_r
        alpha = int(180 * (1 - factor)**1.5) 
        pygame.draw.circle(surf, (255, 240, 200, alpha), (cx, cy), r)
    return surf

def analyze_image_and_targets(image_path, screen_w, screen_h):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"Error: Could not find {image_path}. Please ensure image.png is in the directory.")
        sys.exit()
        
    new_w, new_h = screen_w, screen_h
    offset_x, offset_y = 0, 0
    
    img_smooth = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(img_smooth, cv2.COLOR_BGR2GRAY)
    
    blurred = cv2.bilateralFilter(gray, 5, 50, 50)
    edges = cv2.Canny(blurred, 50, 150) 
            
    outline_targets = []
    for y in range(new_h):
        for x in range(new_w):
            if edges[y, x] > 0:
                outline_targets.append({'x': x + offset_x, 'y': y + offset_y})

    flame_ratios = [
        (0.244, 0.548), (0.287, 0.525), (0.332, 0.548), 
        (0.668, 0.548), (0.713, 0.525), (0.756, 0.548)  
    ]
    flame_centers = []
    for rx, ry in flame_ratios:
        flame_centers.append({
            'x': int(new_w * rx) + offset_x, 
            'y': int(new_h * ry) + offset_y
        })

    rgb_img = cv2.cvtColor(img_smooth, cv2.COLOR_BGR2RGB)
    surface_temp = pygame.image.frombuffer(rgb_img.tobytes(), (new_w, new_h), 'RGB')
    reveal_color_surface = pygame.Surface((screen_w, screen_h))
    reveal_color_surface.blit(surface_temp, (offset_x, offset_y))
    
    reveal_targets = []
    TILE_SIZE = 2 
    for y in range(0, new_h, TILE_SIZE):
        for x in range(0, new_w, TILE_SIZE):
            reveal_targets.append({'x': x + offset_x, 'y': y + offset_y})
                
    # Sort targets based on 'y' ascending so the highest Y (bottom of image)
    # is at the end of the list. `.pop()` will grab these bottom targets first.
    outline_targets.sort(key=lambda t: t['y'])
    reveal_targets.sort(key=lambda t: t['y'])
    
    return outline_targets, reveal_targets, reveal_color_surface, flame_centers

def load_and_scale_image(path, target_height):
    try:
        img = pygame.image.load(path).convert_alpha()
        w, h = img.get_size()
        scale = target_height / h
        scaled_img = pygame.transform.scale(img, (int(w * scale), target_height))
        scaled_img.set_colorkey((0, 0, 0)) 
        return scaled_img
    except:
        return None

def main():
    global WIDTH, HEIGHT
    pygame.init()
    
    os.environ['SDL_VIDEO_WINDOW_POS'] = "0,35"
    
    info = pygame.display.Info()
    WIDTH = info.current_w
    HEIGHT = info.current_h - 130
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption("Ganesha Visualizer - Restored Masterpiece")
    clock = pygame.time.Clock()

    targets = analyze_image_and_targets(IMAGE_PATH, WIDTH, HEIGHT)
    outline_targets, reveal_targets, reveal_color_surface, flame_centers = targets
    
    pastel_aura = create_glossy_pastel_aura(WIDTH, HEIGHT)
    
    outline_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    fill_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    spr_outline_gold = create_sharp_dot((255, 215, 0), 1)  

    bg_flower_sprites = [
        create_flower_sprite((255, 20, 147), 12),  
        create_flower_sprite((0, 220, 120), 12),   
        create_flower_sprite((65, 130, 255), 12),  
        create_flower_sprite((255, 215, 0), 12)    
    ]
    
    bg_glitter_sprites = [
        create_glow_particle((255, 215, 0), 4),    
        create_glow_particle((255, 255, 255), 3)   
    ]
    
    TILE_SIZE = 2
    active_particles = []
    bg_particles = []
    running = True
    phase = 1

    while running:
        screen.fill((5, 2, 5))
        
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        if phase == 1:
            hue = (current_time // 30) % 360 
            pastel_color = pygame.Color(0)
            pastel_color.hsva = (hue, 25, 95, 100)
            colored_aura = pastel_aura.copy()
            colored_aura.fill(pastel_color, special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(colored_aura, (0, 0))

        if phase < 3:
            screen.blit(outline_surface, (0, 0))
            
        screen.blit(fill_surface, (0, 0))

        surviving_particles = []
        for p in active_particles:
            if p['state'] == 'falling':
                p['y'] += p['speed'] * 2  # Fall to floor quickly
                if p['y'] >= HEIGHT:
                    p['y'] = HEIGHT
                    p['state'] = 'rising'
                
                # Render during initial fall
                if p['type'] == 'tile':
                    rect = (p['target_x'], p['target_y'], TILE_SIZE, TILE_SIZE)
                    screen.blit(reveal_color_surface, (p['x'], int(p['y'])), rect)
                elif p['type'] == 'outline':
                    sprite = p['sprite']
                    sprite_rect = sprite.get_rect(center=(p['target_x'], int(p['y'])))
                    screen.blit(sprite, sprite_rect)
                surviving_particles.append(p)
                
            elif p['state'] == 'rising':
                p['y'] -= p['speed']  # Move up to target position
                if p['y'] <= p['target_y']:
                    # Reached target
                    if p['type'] == 'tile':
                        rect = (p['target_x'], p['target_y'], TILE_SIZE, TILE_SIZE)
                        fill_surface.blit(reveal_color_surface, (p['target_x'], p['target_y']), rect)
                    elif p['type'] == 'outline':
                        sprite = p['sprite']
                        target_rect = sprite.get_rect(center=(p['target_x'], p['target_y']))
                        outline_surface.blit(sprite, target_rect)
                else:
                    # Still rising
                    if p['type'] == 'tile':
                        rect = (p['target_x'], p['target_y'], TILE_SIZE, TILE_SIZE)
                        screen.blit(reveal_color_surface, (p['x'], int(p['y'])), rect)
                    elif p['type'] == 'outline':
                        sprite = p['sprite']
                        sprite_rect = sprite.get_rect(center=(p['target_x'], int(p['y'])))
                        screen.blit(sprite, sprite_rect)
                    surviving_particles.append(p)
                
        active_particles = surviving_particles
                
        if phase == 1:
            for _ in range(800):
                if outline_targets:
                    t = outline_targets.pop()
                    active_particles.append({
                        'type': 'outline',
                        'sprite': spr_outline_gold,
                        'x': t['x'],
                        'y': random.randint(-150, -10),
                        'target_x': t['x'],
                        'target_y': t['y'],
                        'speed': random.uniform(4, 9),
                        'state': 'falling'
                    })
            if not outline_targets and len(active_particles) == 0:
                phase = 2
                
        elif phase == 2:
            for _ in range(600):
                if reveal_targets:
                    t = reveal_targets.pop()
                    active_particles.append({
                        'type': 'tile',
                        'x': t['x'],
                        'y': random.randint(-250, -10),
                        'target_x': t['x'],
                        'target_y': t['y'],
                        'speed': random.uniform(4, 10),
                        'state': 'falling'
                    })
            if not reveal_targets and len(active_particles) == 0:
                phase = 3 

        if phase >= 3:
            for i, center in enumerate(flame_centers):
                pulse = math.sin(current_time * 0.006 + i) 
                radius = int(10 + pulse * 4) 
                alpha = int(140 + pulse * 60)
                
                glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
                c_pt = radius * 2
                
                pygame.draw.circle(glow_surf, (255, 255, 200, alpha), (c_pt, c_pt), int(radius * 0.4))
                pygame.draw.circle(glow_surf, (255, 180, 50, int(alpha * 0.6)), (c_pt, c_pt), int(radius * 0.8))
                pygame.draw.circle(glow_surf, (255, 80, 0, int(alpha * 0.2)), (c_pt, c_pt), radius)
                
                shake_x = center['x'] + random.uniform(-0.5, 0.5)
                shake_y = center['y'] + random.uniform(-0.5, 0.5)
                
                rect = glow_surf.get_rect(center=(shake_x, shake_y))
                screen.blit(glow_surf, rect, special_flags=pygame.BLEND_RGBA_ADD)

        if phase >= 2:
            if random.random() < 0.08: 
                is_flower = random.random() < 0.50  
                if is_flower:
                    sprite = random.choice(bg_flower_sprites)
                    speed_y = random.uniform(1.2, 2.5)
                    wobble_width = random.uniform(0.8, 1.8)
                else:
                    sprite = random.choice(bg_glitter_sprites)
                    speed_y = random.uniform(1.0, 3.5) 
                    wobble_width = random.uniform(0.1, 0.4)

                bg_particles.append({
                    'sprite': sprite,
                    'x': random.randint(0, WIDTH),
                    'y': random.randint(-50, -10),
                    'speed_y': speed_y,
                    'wobble_speed': random.uniform(0.002, 0.005),
                    'wobble_offset': random.uniform(0, math.pi * 2),
                    'wobble_width': wobble_width
                })

        surviving_bg = []
        for p in bg_particles:
            p['y'] += p['speed_y']
            draw_x = p['x'] + math.sin(current_time * p['wobble_speed'] + p['wobble_offset']) * p['wobble_width'] * 20
            
            if p['y'] < HEIGHT:
                screen.blit(p['sprite'], (int(draw_x), int(p['y'])))
                surviving_bg.append(p)
        bg_particles = surviving_bg

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()