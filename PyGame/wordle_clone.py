import pygame
import sys
import random
import os

# Constants
WIDTH, HEIGHT = 400, 700
ROWS, COLS = 6, 5
TILE_SIZE = 50
MARGIN = 8
FONT_SIZE = 36
BG_COLOR = (18, 18, 19)
TILE_COLOR = (58, 58, 60)
TEXT_COLOR = (255, 255, 255)
GREEN = (83, 141, 78)
YELLOW = (181, 159, 59)
GRAY = (58, 58, 60)
LIGHT_GRAY = (120, 124, 126)  # like Wordle's unused key color

def load_words(filename):
    base_path = os.path.dirname(__file__)  # directory where the script is
    file_path = os.path.join(base_path, filename)
    with open(file_path, 'r') as f:
        words = [line.strip().upper() for line in f if len(line.strip()) == 5 and line.strip().isalpha()]
    return words

class Tile:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.letter = ""
        self.color = TILE_COLOR

    def draw(self, surface, font):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)
        if self.letter:
            text = font.render(self.letter, True, TEXT_COLOR)
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)

    def set_letter(self, letter):
        self.letter = letter.upper()

    def set_color(self, color):
        self.color = color


class Board:
    def __init__(self, target_word, word_list, keyboard):
        self.rows = ROWS
        self.cols = COLS
        self.tiles = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.current_row = 0
        self.current_col = 0
        self.word_list = word_list
        self.target = target_word
        self.guesses = []
        self.keyboard = keyboard

        for row in range(self.rows):
            for col in range(self.cols):
                x = MARGIN + col * (TILE_SIZE + MARGIN)
                y = MARGIN + row * (TILE_SIZE + MARGIN)
                self.tiles[row][col] = Tile(x, y, TILE_SIZE)
    
    def handle_key(self, key):
        if key == pygame.K_RETURN:
            self.check_guess()
        elif key == pygame.K_BACKSPACE:
            if self.current_col > 0:
                self.current_col -= 1
                self.tiles[self.current_row][self.current_col].set_letter("")
        elif pygame.K_a <= key <= pygame.K_z:
            if self.current_col < self.cols:
                letter = chr(key).upper()
                self.tiles[self.current_row][self.current_col].set_letter(letter)
                self.current_col += 1
                
    def handle_virtual_key(self, letter):
        if self.current_col < self.cols:
            self.tiles[self.current_row][self.current_col].set_letter(letter)
            self.current_col += 1

    def check_guess(self):
        if self.current_col != self.cols:
            return

        guess = "".join([self.tiles[self.current_row][col].letter for col in range(self.cols)])
        guess = guess.upper()
        self.guesses.append(guess)

        for idx, letter in enumerate(guess):
            if letter == self.target[idx]:
                color = GREEN
            elif letter in self.target:
                color = YELLOW
            else:
                color = GRAY
            self.tiles[self.current_row][idx].set_color(color)
            game.keyboard.update_key_color(letter, color)

        if guess not in self.word_list:
            print("Not a valid word")
            return
        
        if guess == self.target or self.current_row == self.rows - 1:
            print("Game Over! Word was:", self.target)
            pygame.time.delay(2000)
            pygame.quit()
            sys.exit()

        self.current_row += 1
        self.current_col = 0

    def draw(self, surface, font):
        for row in self.tiles:
            for tile in row:
                tile.draw(surface, font)

class Key:
    def __init__(self, letter, x, y, w, h):
        self.letter = letter
        self.rect = pygame.Rect(x, y, w, h)
        self.color = LIGHT_GRAY 

    def draw(self, surface, font):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=4)
        text = font.render(self.letter, True, TEXT_COLOR)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def set_color(self, color):
        self.color = color

class Keyboard:
    def __init__(self):
        self.rows = [
            list("QWERTYUIOP"),
            list("ASDFGHJKL"),
            list("ZXCVBNM")
        ]
        self.keys = []
        self.layout()

    def layout(self):
        key_w = 36
        key_h = 48
        spacing = 6
        offset_y = HEIGHT - 3 * (key_h + spacing) - 40  # raise it up a bit

        for i, row in enumerate(self.rows):
            row_keys = []
            offset_x = (WIDTH - (len(row) * (key_w + spacing))) // 2
            for j, letter in enumerate(row):
                x = offset_x + j * (key_w + spacing)
                y = offset_y + i * (key_h + spacing)
                self.keys.append(Key(letter, x, y, key_w, key_h))

    def draw(self, surface, font):
        for key in self.keys:
            key.draw(surface, font)

    def handle_click(self, pos):
        for key in self.keys:
            if key.is_clicked(pos):
                return key.letter
        return None

    def update_key_color(self, letter, color):
        for key in self.keys:
            if key.letter == letter:
                # Priority: Green > Yellow > Gray
                if key.color == GREEN:
                    return  # Don't overwrite green
                if key.color == YELLOW and color == GRAY:
                    return  # Don't downgrade yellow to gray
                key.set_color(color)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Wordle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", FONT_SIZE)
        self.words = load_words("wordle_list.txt")
        self.target_word = random.choice(self.words)
        self.keyboard = Keyboard()
        self.board = Board(self.target_word, self.words, self.keyboard)

    def run(self):
        running = True
        title_font = pygame.font.SysFont("Arial", 32, bold=True)
        title_text = title_font.render("WORDLE", True, (255, 255, 255))
        self.screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 20))
        while running:
            self.screen.fill(BG_COLOR)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.board.handle_key(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    letter = self.keyboard.handle_click(event.pos)
                    if letter:
                        self.board.handle_virtual_key(letter)

            self.board.draw(self.screen, self.font)
            self.keyboard.draw(self.screen, self.font)
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
