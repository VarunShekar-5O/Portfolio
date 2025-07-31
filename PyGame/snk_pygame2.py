import pygame
import random
import sys

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 720, 480
CELL_SIZE = 20
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
FONT_NAME = 'freesansbold.ttf'

class Snake:
    """
    Represents the snake in the game.

    Attributes:
        body (list of tuple): The list of (x, y) positions making up the snake's segments.
        direction (tuple): The current direction the snake is moving (dx, dy).
    
    Methods:
        move():
            Moves the snake in the current direction by adding a new head and removing the tail.
        
        grow():
            Increases the length of the snake by appending a new segment at the tail.
        
        change_direction(new_direction):
            Updates the snake's direction if the new direction is not directly opposite.
        
        draw(screen):
            Draws the snake on the provided Pygame screen.
        
        check_collision():
            Checks for collisions with walls or self, returns True if a collision is detected.
    """
    
    def __init__(self):
        self.body = [(100, 100), (80, 100), (60, 100)]
        self.direction = (CELL_SIZE, 0)

    def move(self):
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        self.body = [new_head] + self.body[:-1]

    def grow(self):
        self.body.append(self.body[-1])

    def change_direction(self, new_direction):
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.direction = new_direction

    def draw(self, screen):
        # Draw all segments as solid green rectangles
        for segment in self.body:
            x, y = segment
            pygame.draw.rect(screen, GREEN, (x, y, CELL_SIZE, CELL_SIZE))

        
    def check_collision(self):
        head = self.body[0]
        return (head in self.body[1:] or
                head[0] < 0 or head[0] >= WINDOW_WIDTH or
                head[1] < 0 or head[1] >= WINDOW_HEIGHT)
        
class Food:
    """
    Represents the food that the snake eats.

    Attributes:
        position (tuple): The (x, y) coordinate of the food on the grid.
    
    Methods:
        random_position():
            Generates and returns a new random position within the window boundaries.
        
        draw(screen):
            Draws the food on the provided Pygame screen at its current position.
    """
    
    def __init__(self):
        self.position = self.random_position()

    def random_position(self):
        x = random.randint(0, (WINDOW_WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        y = random.randint(0, (WINDOW_HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        return (x, y)

    def draw(self, screen):
        pygame.draw.rect(screen, RED, (*self.position, CELL_SIZE, CELL_SIZE))

class Game:
    """
    Manages the overall Snake game logic, rendering, and user interaction.

    Responsibilities:
        - Initializes Pygame and game components (snake, food, screen, clock, font).
        - Handles the main game loop, including event processing, updating game state,
        drawing, scoring, difficulty, and game over logic.
        - Provides restart and quit functionality after the game ends.

    Attributes:
        screen (pygame.Surface): The main game display surface.
        clock (pygame.time.Clock): Controls the game frame rate.
        font (pygame.font.Font): Font used for rendering text (score, game over, etc.).
        snake (Snake): The Snake object.
        food (Food): The Food object.
        score (int): The current score of the player.
        running (bool): Whether the game is currently active.
        direction_queue (list): Queue of pending direction changes for buffered input.

    Methods:
        reset():
            Resets the game state to start a new game.

        run():
            Runs the main game loop continuously, handling updates and rendering.

        handle_events():
            Processes user input events and adds direction changes to the input buffer.

        update():
            Updates the game state, applies input buffer, moves snake,
            checks for collisions and food consumption, and updates score/speed.

        draw():
            Clears the screen and draws all game elements (snake, food, score).

        draw_score():
            Renders and displays the current score in the top-left corner.

        game_over():
            Displays a game over screen and waits for user input to restart or quit.
    """
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Snake Game')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(FONT_NAME, 24)
        self.state = "menu"  # can be "menu", "playing", or "game_over"
        self.direction_queue = []
        self.reset()

    def reset(self):
        self.snake = Snake()
        self.food = Food()
        self.score = 0
        self.running = True

    def run(self):
        while True:
            if self.state == "menu":
                self.show_main_menu()
            elif self.state == "playing":
                self.handle_events()
                self.update()
                self.draw()
                self.clock.tick(min(15 + self.score//5,30))
            elif self.state == "game_over":
                self.show_game_over_screen()
    
    def show_main_menu(self):
        self.screen.fill(BLACK)
        title = self.font.render("SNAKE GAME", True, GREEN)
        start_msg = self.font.render("Press ENTER to Start", True, WHITE)
        quit_msg = self.font.render("Press Q to Quit", True, WHITE)

        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 120))
        self.screen.blit(start_msg, (WINDOW_WIDTH // 2 - start_msg.get_width() // 2, 180))
        self.screen.blit(quit_msg, (WINDOW_WIDTH // 2 - quit_msg.get_width() // 2, 220))
        pygame.display.flip()

        while self.state == "menu":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.reset()
                        self.state = "playing"
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.direction_queue.append((0, -CELL_SIZE))
                elif event.key == pygame.K_DOWN:
                    self.direction_queue.append((0, CELL_SIZE))
                elif event.key == pygame.K_LEFT:
                    self.direction_queue.append((-CELL_SIZE, 0))
                elif event.key == pygame.K_RIGHT:
                    self.direction_queue.append((CELL_SIZE, 0))

    def update(self):
        
        # Apply next direction from the buffer if valid
        while self.direction_queue:
            next_dir = self.direction_queue.pop(0)
            # Only apply if it's not a 180 turn
            if (next_dir[0] * -1, next_dir[1] * -1) != self.snake.direction:
                self.snake.change_direction(next_dir)
                break  # Apply only one direction per update
            
        self.snake.move()
        
        if self.snake.body[0] == self.food.position:
            self.snake.grow()
            self.food = Food()
            self.score += 1
            
        if self.snake.check_collision():
            self.state = "game_over"

    def draw(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, WHITE, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), 2)
        self.snake.draw(self.screen)
        self.food.draw(self.screen)
        self.draw_score()
        pygame.display.flip()

    def draw_score(self):
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

    def show_game_over_screen(self):
        self.screen.fill(BLACK)
        msg1 = self.font.render("GAME OVER", True, RED)
        msg2 = self.font.render(f"Final Score: {self.score}", True, WHITE)
        msg3 = self.font.render("Press R to Restart", True, WHITE)
        msg4 = self.font.render("Press M for Main Menu", True, WHITE)

        self.screen.blit(msg1, (WINDOW_WIDTH // 2 - msg1.get_width() // 2, 120))
        self.screen.blit(msg2, (WINDOW_WIDTH // 2 - msg2.get_width() // 2, 160))
        self.screen.blit(msg3, (WINDOW_WIDTH // 2 - msg3.get_width() // 2, 200))
        self.screen.blit(msg4, (WINDOW_WIDTH // 2 - msg4.get_width() // 2, 240))
        pygame.display.flip()

        while self.state == "game_over":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset()
                        self.state = "playing"
                    elif event.key == pygame.K_m:
                        self.state = "menu"

if __name__ == "__main__":
    game = Game()
    game.run()