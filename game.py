import pygame, sys, configparser, os

pygame.init()

# Screen Settings
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
WINDOW_WIDTH, WINDOW_HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT
FPS = 60

# Colors
BLACK, BLUE, GREEN, YELLOW, PURPLE, RED, WHITE = (0, 0, 0), (50, 50, 200), (50, 200, 50), (255, 255, 0), (150, 50, 150), (255, 0, 0), (255, 255, 255)

# Pygame Initialization
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Level Engine (Dev Mode)")
clock = pygame.time.Clock()

# Config for Development Mode with Error Handling
config = configparser.ConfigParser()
config_file = 'config.ini'

if os.path.exists(config_file):
    config.read(config_file)
    if 'settings' in config and 'mode' in config['settings']:
        DEVELOPMENT_MODE = config['settings']['mode'] == 'development'
    else:
        print("Error: 'settings' section or 'mode' key not found in config.ini.")
        sys.exit(1)
else:
    print(f"Error: {config_file} does not exist.")
    sys.exit(1)

# Game States
STATE_LEVEL_SELECTION, STATE_LEVEL_EDITOR, STATE_GAMEPLAY, STATE_PAUSED = 'level_selection', 'level_editor', 'gameplay', 'paused'

# Utility Functions
def load_level(file):
    return [list(line.strip()) for line in open(file)]

def reset_level(level):
    return [row[:] for row in level]

# Level Data
level_1, level_2 = load_level('level1.txt'), load_level('level2.txt')

# Player Class
class Player:
    def __init__(self):
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.pos = [0, 0]
        self.start_pos = [TILE_SIZE, TILE_SIZE]  # Store the spawn point separately
        self.vel_y = 0
        self.speed = 4
        self.gravity = 1
        self.jump_power = -15
        self.on_ground = False

    def initialize(self, level_data):
        offset_x = (WINDOW_WIDTH - (len(level_data[0]) * TILE_SIZE)) // 2
        offset_y = (WINDOW_HEIGHT - (len(level_data) * TILE_SIZE)) // 2
        for row in range(len(level_data)):
            for col in range(len(level_data[row])):
                if level_data[row][col] == '3':
                    self.start_pos = [offset_x + col * TILE_SIZE, offset_y + row * TILE_SIZE]
                    self.pos = self.start_pos[:]
                    level_data[row][col] = '0'
                    return
        self.pos = [TILE_SIZE, TILE_SIZE]  # Default spawn

    def move(self, keys, level_data):
        future_x = self.pos[0]
        future_y = self.pos[1] + self.vel_y

        # Horizontal Movement
        if keys[pygame.K_LEFT]:
            future_x -= self.speed
            if not check_collision(future_x, self.pos[1], level_data, game.level):
                self.pos[0] = future_x

        if keys[pygame.K_RIGHT]:
            future_x += self.speed
            if not check_collision(future_x + self.width, self.pos[1], level_data, game.level):
                self.pos[0] = future_x

        # Jumping
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = self.jump_power

        # Apply Gravity
        self.vel_y += self.gravity

        # Check for vertical collisions
        if self.vel_y > 0:  # Falling
            if check_collision(self.pos[0], future_y + self.height, level_data, game.level):
                self.vel_y = 0
                self.on_ground = True
                future_y = (future_y // TILE_SIZE) * TILE_SIZE - self.height
            self.pos[1] = future_y
        elif self.vel_y < 0:  # Jumping
            if check_collision(self.pos[0], future_y, level_data, game.level):
                self.vel_y = 0
                future_y = (future_y // TILE_SIZE + 1) * TILE_SIZE
            self.pos[1] = future_y
        else:
            self.pos[1] = future_y

# Collision Detection
def check_collision(x, y, level_data, level):
    if y >= WINDOW_HEIGHT:
        game.player.pos = game.player.start_pos[:]
        game.player.vel_y = 0  # Respawn at starting point
        return True
    offset_x = (WINDOW_WIDTH - (level.cols * TILE_SIZE)) // 2
    offset_y = (WINDOW_HEIGHT - (level.rows * TILE_SIZE)) // 2
    col = (x - offset_x + TILE_SIZE // 2) // TILE_SIZE
    row = (y - offset_y + TILE_SIZE // 2) // TILE_SIZE
    if 0 <= col < level.cols and 0 <= row < level.rows:
        if level_data[row][col] in colors:
            return True
    return False

# Grid Renderer
class Level:
    def __init__(self, data):
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0])
        self.dirty_rects = []

    def draw(self):
        offset_x = (WINDOW_WIDTH - (self.cols * TILE_SIZE)) // 2
        offset_y = (WINDOW_HEIGHT - (self.rows * TILE_SIZE)) // 2
        self.dirty_rects = []
        for row in range(self.rows):
            for col in range(self.cols):
                color = colors.get(self.data[row][col])
                if color:
                    rect = pygame.Rect(offset_x + col * TILE_SIZE, offset_y + row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(screen, color, rect)
                    self.dirty_rects.append(rect)

# Game Class
class Game:
    def __init__(self):
        self.state = STATE_LEVEL_SELECTION
        self.selected_level = 1
        self.level = Level(level_1)
        self.player = Player()
        self.editing_tile = '1'  # Default tile for editing
        self.pause_menu = False
        self.pause_options = ['Return to Level Select', 'Quit']
        self.pause_selected = 0

    def handle_events(self):
        keys = pygame.key.get_pressed()
        if self.state == STATE_GAMEPLAY and not self.pause_menu:
            self.player.move(keys, self.level.data)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.state != STATE_LEVEL_SELECTION:
                self.pause_menu = not self.pause_menu

            if self.state == STATE_LEVEL_SELECTION:
                self.level_selection_events(event)
            elif self.pause_menu:
                self.pause_menu_events(event)
        return True

    def level_selection_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected_level = max(1, self.selected_level - 1)
            elif event.key == pygame.K_RIGHT:
                self.selected_level = min(3, self.selected_level + 1)
            elif event.key == pygame.K_SPACE:
                self.start_level()

    def pause_menu_events(self, event):
        if self.state == STATE_LEVEL_EDITOR and event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            col = (mouse_x - (WINDOW_WIDTH - self.level.cols * TILE_SIZE) // 2) // TILE_SIZE
            row = (mouse_y - (WINDOW_HEIGHT - self.level.rows * TILE_SIZE)) // TILE_SIZE
            if 0 <= col < self.level.cols and 0 <= row < self.level.rows:
                if event.button == 1:  # Left click to place tile
                    self.level.data[row][col] = self.editing_tile
                elif event.button == 3:  # Right click to remove tile
                    self.level.data[row][col] = '0'
        if self.state == STATE_LEVEL_EDITOR and event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_4:
                self.editing_tile = str(event.key - pygame.K_0)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.pause_selected = (self.pause_selected + 1) % len(self.pause_options)
            elif event.key == pygame.K_UP:
                self.pause_selected = (self.pause_selected - 1) % len(self.pause_options)
            elif event.key == pygame.K_RETURN:
                if self.pause_selected == 0:
                    self.state = STATE_LEVEL_SELECTION
                elif self.pause_selected == 1:
                    pygame.quit()
                    sys.exit()

    def start_level(self):
        self.level = Level(reset_level(level_1 if self.selected_level == 1 else level_2))
        self.player.initialize(self.level.data)
        self.state = STATE_LEVEL_EDITOR if self.selected_level == 3 else STATE_GAMEPLAY

# Run Game
TILE_SIZE = 48
colors = {'1': GREEN, '2': YELLOW, '3': RED, '4': PURPLE}
game = Game()
running = True
while running:
    running = game.handle_events()
    screen.fill(BLUE)
    game.level.draw()
    pygame.draw.rect(screen, WHITE, (*game.player.pos, TILE_SIZE, TILE_SIZE))
    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
sys.exit()
