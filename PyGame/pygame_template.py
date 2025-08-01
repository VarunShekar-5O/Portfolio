import pygame
import sys

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

'''
Program starts
    ↓
Game.__init__ sets up everything
    ↓
Game.run() begins infinite loop
    ↓
Initial state: "menu"
    ↓
User presses ENTER
    ↓
State changes to "playing"
    ↓
User presses ESC or dies
    ↓
State changes to "game_over"
    ↓
User presses R or M
    ↓
Loop continues with new state
'''

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pygame State Engine Template")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.state = "menu"  # Available states: menu, playing, paused, game_over

    def run(self):
        '''
        This is the main loop of the program, and it's always running. It checks the current state and calls the appropriate method
        '''
        while True:
            if self.state == "menu":
                self.main_menu()
            elif self.state == "playing":
                self.playing()
            elif self.state == "paused":
                self.pause_screen()
            elif self.state == "game_over":
                self.game_over()

    def handle_quit(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def main_menu(self):
        '''What happens:
                Background is black
                Title and instructions are shown
                Waits for:
                    ENTER → changes state to "playing"
                    Q → exits game
                When ENTER is pressed:
                    The main menu loop ends
                    Control returns to run()
                    "playing" state is detected → calls playing()
        '''
        while self.state == "menu":
            self.handle_quit()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_RETURN]:
                self.state = "playing"
            elif keys[pygame.K_q]:
                pygame.quit()
                sys.exit()

            self.screen.fill(BLACK)
            self.draw_text("MAIN MENU", 100)
            self.draw_text("Press ENTER to Start", 200)
            self.draw_text("Press Q to Quit", 250)
            pygame.display.flip()
            self.clock.tick(FPS)

    def playing(self):
        '''
        This is where your actual game logic would go.
        
        What happens:
            A blank game scene is drawn
            Input handling inside the event loop:
                P → pause the game (self.state = "paused")
                ESCAPE → simulate game over (self.state = "game_over")
                
            When state changes:
                The playing() loop exits
                Control returns to run(), which now checks the updated state
        '''
        while self.state == "playing":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.state = "paused"
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "game_over"

            self.screen.fill((30, 30, 30))
            self.draw_text("Playing... Press P to Pause, ESC for Game Over", 20)
            pygame.display.flip()
            self.clock.tick(FPS)

    def pause_screen(self):
        '''What happens:
            Screen turns gray
            Displays "Paused"
            Waits for:
                R → resume game (self.state = "playing")
                M → go to main menu (self.state = "menu")'''
        while self.state == "paused":
            self.handle_quit()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                self.state = "playing"
            elif keys[pygame.K_m]:
                self.state = "menu"

            self.screen.fill((50, 50, 50))
            self.draw_text("PAUSED", 100)
            self.draw_text("Press R to Resume", 200)
            self.draw_text("Press M for Menu", 250)
            pygame.display.flip()
            self.clock.tick(FPS)

    def game_over(self):
        '''What happens:
            Red background
            Shows "Game Over" and options
            Waits for:
                R → retry game (self.state = "playing")
                M → return to main menu (self.state = "menu")
        '''
        while self.state == "game_over":
            self.handle_quit()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                self.state = "playing"
            elif keys[pygame.K_m]:
                self.state = "menu"

            self.screen.fill((80, 0, 0))
            self.draw_text("GAME OVER", 100)
            self.draw_text("Press R to Retry", 200)
            self.draw_text("Press M for Menu", 250)
            pygame.display.flip()
            self.clock.tick(FPS)

    def draw_text(self, text, y, color=WHITE):
        surface = self.font.render(text, True, color)
        rect = surface.get_rect(center=(WINDOW_WIDTH // 2, y))
        self.screen.blit(surface, rect)

if __name__ == "__main__":
    Game().run()
