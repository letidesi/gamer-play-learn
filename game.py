import pygame
import time
import config


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        )
        self.background = pygame.image.load(config.BACKGROUND_IMG)
        self.background = pygame.transform.scale(
            self.background, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        )

        self.warning_sound = pygame.mixer.Sound("assets/warning.wav")
        self.next_sound = pygame.mixer.Sound("assets/next_sound.wav")
        self.choice_letter = pygame.mixer.Sound("assets/choice_letter.wav")

        self.play_next_after_warning = False

        self.channel = pygame.mixer.Channel(0)
        self.channel.set_endevent(pygame.USEREVENT + 1)

        pygame.display.set_caption("Jogo da Roda de Letras")

        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.SysFont("arial", 30)

        self.max_players = 4
        self.players = []
        self.input_boxes = ["" for _ in range(self.max_players)]
        self.current_input = 0

        self.character_images = [
            pygame.transform.scale(
                pygame.image.load(f"assets/char{i}.jpg").convert_alpha(),
                (64, 64)
            )
            for i in range(1, 5)
        ]
        self.selected_character_index = 0

        self.scores = [0] * self.max_players
        self.used_letters = set()
        self.alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.current_letter_index = 0

        self.state = "get_names"
        self.current_player_turn = 0
        self.letter_chosen = None
        self.current_letter = None
        self.current_answer = ""
        self.timer_start = None
        self.remaining_time = 40
        self.warning_played = False

    def run(self):
        while self.running:
            self.screen.blit(self.background, (0, 0))
            self.handle_events()

            if self.state == "get_names":
                self.draw_name_input()
            elif self.state == "choose_character":
                self.draw_character_selection()
            elif self.state == "roulette":
                self.draw_roulette()
                self.update_timer()
            elif self.state == "answer_input":
                self.draw_answer_input()
                self.update_timer()
            elif self.state == "gameplay":
                self.process_answer()
                self.next_turn()

            pygame.display.flip()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT + 1:
                if self.play_next_after_warning:
                    self.play_next_after_warning = False
                    self.channel.play(self.next_sound)

            elif event.type == pygame.QUIT:
                self.running = False

            elif self.state == "get_names":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.input_boxes[self.current_input] != "":
                        self.players.append({
                            "name": self.input_boxes[self.current_input],
                            "character": None,
                        })
                        self.current_input += 1
                        if self.current_input == self.max_players:
                            self.current_input = 0
                            self.state = "choose_character"
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_boxes[self.current_input] = (
                            self.input_boxes[self.current_input][:-1]
                        )
                    else:
                        self.input_boxes[self.current_input] += event.unicode

            elif self.state == "choose_character":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.selected_character_index = (self.selected_character_index - 1) % len(self.character_images)
                    elif event.key == pygame.K_RIGHT:
                        self.selected_character_index = (self.selected_character_index + 1) % len(self.character_images)
                    elif event.key == pygame.K_RETURN:
                        self.players[self.current_input]["character"] = self.character_images[self.selected_character_index]
                        self.current_input += 1
                        if self.current_input == self.max_players:
                            self.state = "roulette"
                            self.current_player_turn = 0
                            self.letter_chosen = None
                            self.timer_start = None
                            self.remaining_time = 40
                            self.warning_played = False
                        else:
                            self.selected_character_index = 0

            elif self.state == "roulette":
                if not self.letter_chosen and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.move_letter_index(-1)
                    elif event.key == pygame.K_RIGHT:
                        self.move_letter_index(1)
                    elif event.key == pygame.K_RETURN:
                        chosen_letter = self.alphabet[self.current_letter_index]
                        if chosen_letter not in self.used_letters:
                            self.letter_chosen = chosen_letter
                            self.used_letters.add(chosen_letter)
                            self.current_letter = chosen_letter
                            self.current_answer = ""
                            self.timer_start = time.time()
                            self.state = "answer_input"
                            self.warning_played = False
                            self.play_choice_sound()

            elif self.state == "answer_input":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        self.current_answer = self.current_answer[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.timer_start = None
                        self.state = "gameplay"
                    elif event.unicode.isalpha():
                        self.current_answer += event.unicode.upper()

    def move_letter_index(self, direction):
        self.current_letter_index = (self.current_letter_index + direction) % len(self.alphabet)

    def update_timer(self):
        if self.letter_chosen and self.timer_start:
            elapsed = time.time() - self.timer_start
            self.remaining_time = max(0, 40 - elapsed)

            if self.remaining_time <= 5 and not self.warning_played:
                self.play_warning_sound()
                self.warning_played = True

            if self.remaining_time <= 0:
                self.next_turn()

    def play_warning_sound(self):
        self.channel.play(self.warning_sound)
        self.play_next_after_warning = True  # sinaliza que o próximo som deve vir depois

    def play_choice_sound(self):
        self.channel.play(self.choice_letter)

    def process_answer(self):
        if self.current_answer.strip():
            self.scores[self.current_player_turn] += 1

    def next_turn(self):
        self.current_player_turn = (self.current_player_turn + 1) % self.max_players
        self.letter_chosen = None
        self.current_letter = None
        self.current_answer = ""
        self.timer_start = None
        self.remaining_time = 40
        self.warning_played = False
        self.state = "roulette"

    def draw_name_input(self):
        title_font = pygame.font.SysFont("arial", 40, bold=True)
        game_title = title_font.render("🎡 Roda das Letras 🎡", True, (255, 255, 255))
        game_title_rect = game_title.get_rect(center=(config.SCREEN_WIDTH // 2, 80))
        self.screen.blit(game_title, game_title_rect)

        prompt_text = self.font.render(
            f"{self.current_input + 1}º Jogador, digite seu nome:", True, (255, 255, 255)
        )
        prompt_rect = prompt_text.get_rect(center=(config.SCREEN_WIDTH // 2, 180))
        self.screen.blit(prompt_text, prompt_rect)

        box_width, box_height = 400, 50
        input_box_rect = pygame.Rect(
            (config.SCREEN_WIDTH - box_width) // 2, 230, box_width, box_height
        )

        pygame.draw.rect(self.screen, (50, 50, 50), input_box_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 0), input_box_rect, 3, border_radius=8)

        input_text = self.font.render(self.input_boxes[self.current_input], True, (255, 255, 0))
        input_text_rect = input_text.get_rect(center=input_box_rect.center)
        self.screen.blit(input_text, input_text_rect)

        list_title = self.font.render("Jogadores cadastrados:", True, (200, 200, 200))
        self.screen.blit(list_title, (50, 330))

        y = 370
        for idx, player in enumerate(self.players):
            player_text = self.font.render(f"{idx + 1}. {player['name']}", True, (180, 180, 180))
            self.screen.blit(player_text, (70, y))
            y += 30

    def draw_character_selection(self):
        title = self.font.render(
            f"Jogador {self.current_input + 1}, escolha seu personagem:", True, (255, 255, 255)
        )
        self.screen.blit(title, (100, 50))

        for i, img in enumerate(self.character_images):
            x = 100 + i * 100
            y = 150
            if i == self.selected_character_index:
                pygame.draw.rect(self.screen, (255, 255, 0), (x - 5, y - 5, 74, 74), 3)
            self.screen.blit(img, (x, y))

        y = 250
        for idx, player in enumerate(self.players):
            text_str = f"Jogador {idx + 1}: {player['name']}"
            if player["character"] is not None:
                text_str += " ✔"
            text = self.font.render(text_str, True, (180, 180, 180))
            self.screen.blit(text, (50, y))
            y += 30

    def draw_roulette(self):
        title = self.font.render(
            f"{self.players[self.current_player_turn]['name']}, escolha uma letra:", True, (255, 255, 255)
        )
        self.screen.blit(title, (100, 50))

        for i, letter in enumerate(self.alphabet):
            color = (255, 255, 0) if i == self.current_letter_index else (200, 200, 200)
            letter_surface = self.font.render(letter, True, color)
            self.screen.blit(letter_surface, (50 + (i % 13) * 70, 150 + (i // 13) * 70))

        if self.letter_chosen:
            time_text = self.font.render(
                f"Tempo restante: {int(self.remaining_time)}s", True, (255, 100, 100)
            )
            self.screen.blit(time_text, (100, 350))

    def draw_answer_input(self):
        title = self.font.render(
            f"{self.players[self.current_player_turn]['name']}, digite uma palavra com '{self.current_letter}':",
            True,
            (255, 255, 255)
        )
        self.screen.blit(title, (100, 50))

        answer_surface = self.font.render(self.current_answer, True, (255, 255, 0))
        self.screen.blit(answer_surface, (100, 150))

        timer_surface = self.font.render(f"Tempo restante: {int(self.remaining_time)}s", True, (255, 100, 100))
        self.screen.blit(timer_surface, (100, 220))

