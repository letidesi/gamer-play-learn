import pygame
import time
import config
from api.word_validation import validate_word
from api.validation_string import validation_name

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
        self.player_count = 0
        self.state = "select_player_count"  # já tem

        # Para votação:
        self.voting_word = None  # palavra a ser votada
        self.votes = []  # lista dos votos (True=sim, False=não)
        self.vote_required = 0  # quantos votos precisam
        self.current_voter = 0  # índice do jogador votando
        self.vote_result = None  # resultado final (True/False)
        self.vote_time_limit = 30  # segundos para votar (opcional)
        self.vote_start_time = None  # hora que começou votação

        self.error_message = ""
        self.error_message_time = 0
        self.error_message_duration = 3000  # 3 segundos
        self.error_alpha = 255  # opacidade inicial (0 transparente, 255 opaco)
        self.error_alpha_direction = -5  # direção do fade (diminuindo)

        self.letter_rects = []

        self.themes = ["Lugar", "Objeto", "Animal", "Comida", "Profissão", "+ Criar nova categoria para a próxima rodada"]
        self.selected_theme_index = 0
        self.current_theme = None
        self.theme_rects = []
        self.custom_theme_input = ""
        self.typing_custom_theme = False

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

            if self.state == "select_player_count":
                self.draw_select_player_count()
            if self.state == "get_names":
                self.draw_name_input()
            elif self.state == "choose_character":
                self.draw_character_selection()
            elif self.state == "select_theme":
                self.draw_theme_selection()
            elif self.state == "roulette":
                self.draw_roulette()
                self.update_timer()
            elif self.state == "letter_reveal":
                self.draw_roulette()  # mostra a letra sorteada
                if time.time() - self.reveal_start_time > 4:  # pode ser 2.5s ou o tempo que quiser
                    self.timer_start = time.time()
                    self.state = "answer_input"
            elif self.state == "answer_input":
                self.draw_answer_input()
                self.update_timer()
            elif self.state == "gameplay":
                self.process_answer()
            elif self.state == "voting":
                self.draw_voting()

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
            elif hasattr(self, 'typing_custom_theme') and self.typing_custom_theme:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        theme = self.custom_theme_input.strip()
                        if validation_name(theme):
                            self.typing_custom_theme = False
                            self.current_theme = theme
                            self.error_message = ""
                            # opcional: mudar estado, ex:
                            self.state = "roulette"
                        else:
                            self.error_message = "Tema inválido! Use letras, acentos, espaços e hífen."
                            self.error_message_time = pygame.time.get_ticks() + self.error_message_duration
                            self.error_alpha = 255
                            self.error_alpha_direction = -5

                    elif event.key == pygame.K_BACKSPACE:
                        self.custom_theme_input = self.custom_theme_input[:-1]

                    elif event.unicode.isprintable():
                        self.custom_theme_input += event.unicode

            elif self.state == "select_player_count":
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_2, pygame.K_3, pygame.K_4]:
                        self.max_players = int(event.unicode)
                        self.input_boxes = ["" for _ in range(self.max_players)]
                        self.scores = [0] * self.max_players
                        self.player_count = self.max_players
                        self.state = "get_names"

            elif self.state == "get_names":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.input_boxes[self.current_input] != "":
                        name = self.input_boxes[self.current_input].strip()
                        if validation_name(name):
                            self.players.append({
                                "name": name,
                                "character": None,
                            })
                            self.current_input += 1

                            if self.current_input == self.max_players:
                                self.current_input = 0
                                self.state = "choose_character"
                        else:
                            self.error_message = "Nome inválido! Use letras e acentos, sem símbolos proibidos."
                            self.error_message_time = pygame.time.get_ticks() + self.error_message_duration
                            self.error_alpha = 255
                            self.error_alpha_direction = -5
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_boxes[self.current_input] = self.input_boxes[self.current_input][:-1]
                    elif len(self.input_boxes[self.current_input]) < 6 and event.unicode.isprintable():
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
                            self.state = "select_theme"
                            self.current_player_turn = 0
                            self.letter_chosen = None
                            self.timer_start = None
                            self.remaining_time = 40
                            self.warning_played = False
                        else:
                            self.selected_character_index = 0



            elif self.state == "select_theme":
                if self.typing_custom_theme:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            tema = self.custom_theme_input.strip()
                            if validation_name(tema):  # ou validation_text
                                self.current_theme = tema
                                self.typing_custom_theme = False
                                self.custom_theme_input = ""
                                self.state = "roulette"
                                self.letter_chosen = None
                                self.timer_start = None
                                self.remaining_time = 40
                                self.warning_played = False
                                self.error_message = ""
                            else:
                                self.error_message = "Tema inválido! Use letras, acentos, espaços e hífen."
                                self.error_message_time = pygame.time.get_ticks() + self.error_message_duration
                                self.error_alpha = 255
                                self.error_alpha_direction = -5


                        elif event.key == pygame.K_BACKSPACE:
                            self.custom_theme_input = self.custom_theme_input[:-1]

                        elif hasattr(event, "unicode") and event.unicode.isprintable():
                            self.custom_theme_input += event.unicode

                else:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_UP:
                            self.selected_theme_index = (self.selected_theme_index - 1) % len(self.themes)

                        elif event.key == pygame.K_DOWN:
                            self.selected_theme_index = (self.selected_theme_index + 1) % len(self.themes)

                        elif event.key == pygame.K_RETURN:
                            if self.themes[self.selected_theme_index] == "+ Criar nova categoria para a próxima rodada":
                                self.typing_custom_theme = True
                                self.custom_theme_input = ""
                            else:
                                self.choose_theme(self.selected_theme_index)

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_pos = event.pos
                        for i, rect in enumerate(self.theme_rects):
                            if rect.collidepoint(mouse_pos):
                                if self.themes[i] == "+ Criar nova categoria para a próxima rodada":
                                    self.typing_custom_theme = True
                                    self.custom_theme_input = ""
                                else:
                                    self.choose_theme(i)
                                break

            elif self.state == "roulette":
                if not self.letter_chosen:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LEFT:
                            self.move_letter_index(-1)
                        elif event.key == pygame.K_RIGHT:
                            self.move_letter_index(1)
                        elif event.key == pygame.K_RETURN:
                            self.select_letter(self.alphabet[self.current_letter_index])
                        elif event.unicode.upper() in self.alphabet:
                            self.select_letter(event.unicode.upper())

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_pos = event.pos
                        for i, (letter, rect) in enumerate(self.letter_rects):
                            if rect.collidepoint(mouse_pos):
                                self.current_letter_index = self.alphabet.index(letter)
                                self.select_letter(letter)
                                break
            elif self.state == "letter_reveal":
                self.draw_roulette()  #
                if time.time() - self.reveal_start_time > 5:
                    self.timer_start = time.time()
                    self.state = "answer_input"


            elif self.state == "answer_input":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        self.current_answer = self.current_answer[:-1]
                    elif event.key == pygame.K_RETURN:
                        is_valid = validate_word(self.current_answer.strip())
                        if is_valid is True:
                            self.timer_start = None
                            self.state = "gameplay"
                        elif is_valid is False:
                            print("Palavra inválida!")
                        else:
                            print("Não foi possível validar. Iniciando votação offline...")
                    elif hasattr(event, 'unicode') and event.unicode.isalpha():
                        self.current_answer += event.unicode.upper()

            elif self.state == "voting":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        self.votes.append(True)
                        self.current_voter += 1
                    elif event.key == pygame.K_n:
                        self.votes.append(False)
                        self.current_voter += 1

                    if self.current_voter >= self.vote_required:
                        self.finish_voting()

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    if self.sim_button_rect.collidepoint(mouse_pos):
                        self.votes.append(True)
                        self.current_voter += 1
                        if self.current_voter >= self.vote_required:
                            self.finish_voting()

                    elif self.nao_button_rect.collidepoint(mouse_pos):
                        self.votes.append(False)
                        self.current_voter += 1
                        if self.current_voter >= self.vote_required:
                            self.finish_voting()

                    elif hasattr(event, "unicode") and event.unicode.isalpha():
                        self.current_answer += event.unicode.upper()

                    if self.current_voter >= self.vote_required:
                        self.finish_voting()


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
        self.play_next_after_warning = True

    def play_choice_sound(self):
        self.channel.play(self.choice_letter)

    def select_letter(self, letter):
        if letter not in self.used_letters:
            self.letter_chosen = letter
            self.used_letters.add(letter)
            self.current_letter = letter
            self.current_answer = ""
            self.reveal_start_time = time.time()
            self.timer_start = time.time()
            self.state = "letter_reveal"
            self.warning_played = False
            self.play_choice_sound()

    def process_answer(self):
        if self.current_answer.strip():
            word = self.current_answer.strip().lower()

            # Valida palavra no dicionário
            is_valid = validate_word(word)
            if is_valid is None:
                print("Não foi possível validar. Iniciando votação offline...")
                self.start_voting(word)
                return

            if not is_valid:
                # Palavra inválida no dicionário, perde pontos e passa a vez
                self.scores[self.current_player_turn] -= 10
                print(
                    f"Palavra '{word}' inválida! Jogador {self.players[self.current_player_turn]['name']} perde 10 pontos.")
                self.next_turn()
                return

            # Palavra válida, inicia votação para validar tema
            self.start_voting(word)

    def finish_voting(self):
        # Se a maioria aprovou
        approved = sum(self.votes) > (self.vote_required / 2)
        player_name = self.players[self.current_player_turn]['name']
        word = self.voting_word

        if approved:
            self.scores[self.current_player_turn] += 10
            print(f"Palavra '{word}' aprovada pelos jogadores! +10 pontos para {player_name}")

            # Jogador pode escolher próxima letra sem perder a vez
            self.letter_chosen = None
            self.current_letter = None
            self.current_answer = ""
            self.timer_start = None
            self.remaining_time = 40
            self.warning_played = False
            self.state = "roulette"
        else:
            print(f"Palavra '{word}' rejeitada pelos jogadores! Vez passa para o próximo jogador.")
            self.scores[self.current_player_turn] -= 10
            self.next_turn()

        self.voting_word = None
        self.votes = []
        self.vote_required = 0
        self.current_voter = 0
        self.vote_result = None
        self.vote_start_time = None

    def next_turn(self):
        self.current_player_turn = (self.current_player_turn + 1) % self.max_players
        self.letter_chosen = None
        self.current_letter = None
        self.current_answer = ""
        self.timer_start = None
        self.remaining_time = 40
        self.warning_played = False
        self.state = "roulette"

    def draw_select_player_count(self):
        title_font = pygame.font.SysFont("comicsansms", 42, bold=True)
        title = title_font.render("Quantos players no squad?", True, (255, 255, 255))
        title_rect = title.get_rect(center=(config.SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        instruction_font = pygame.font.SysFont("comicsansms", 28, bold=True)
        instruction = instruction_font.render("Pressione [2], [3] ou [4] para definir os participantes.",
                                              True, (200, 200, 0))
        instruction_rect = instruction.get_rect(center=(config.SCREEN_WIDTH // 2, 250))
        self.screen.blit(instruction, instruction_rect)

    def draw_name_input(self):
        title_font = pygame.font.SysFont("comicsansms", 40, bold=True)
        game_title = title_font.render("Roda das Letras", True, (255, 255, 255))
        game_title_rect = game_title.get_rect(center=(config.SCREEN_WIDTH // 2, 80))
        self.screen.blit(game_title, game_title_rect)

        prompt_font = pygame.font.SysFont("comicsansms", 28, bold=True)
        prompt_text = prompt_font.render(
            f"{self.current_input + 1}º Jogador, digite seu apelido:", True, (255, 255, 255)
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

        current_time = pygame.time.get_ticks()
        if self.error_message and current_time < self.error_message_time:
            self.error_alpha += self.error_alpha_direction
            if self.error_alpha <= 50 or self.error_alpha >= 255:
                self.error_alpha_direction *= -1
                self.error_alpha = max(50, min(255, self.error_alpha))

            font = pygame.font.SysFont("comicsansms", 28, bold=True)
            text_surface = font.render(self.error_message, True, (255, 50, 50))
            text_surface.set_alpha(self.error_alpha)

            text_rect = text_surface.get_rect(center=(config.SCREEN_WIDTH // 2, 300))
            self.screen.blit(text_surface, text_rect)

    def draw_character_selection(self):
        rect_x, rect_y, rect_w, rect_h = 80, 40, 800, 60
        pygame.draw.rect(self.screen, (20, 20, 60), (rect_x, rect_y, rect_w, rect_h), border_radius=10)

        title_font = pygame.font.SysFont("comicsansms", 42, bold=True)
        player_name = self.players[self.current_input]["name"]
        title_text = f"{player_name}, Quem é o mestre das palavras?"
        title_surface = title_font.render(title_text, True, (255, 255, 255))

        title_rect = title_surface.get_rect()
        title_rect.centery = rect_y + rect_h // 2
        title_rect.x = rect_x + 20

        self.screen.blit(title_surface, title_rect)

        font_comics = pygame.font.SysFont("comicsansms", 28)

        spacing_x = 150
        total_width = self.max_players * spacing_x
        start_x = (config.SCREEN_WIDTH - total_width) // 2

        y_img = 150

        # 1. Desenha as imagens centralizadas horizontalmente
        for i, img in enumerate(self.character_images[:self.max_players]):
            x = start_x + i * spacing_x

            # retângulo amarelo para seleção
            if i == self.selected_character_index:
                pygame.draw.rect(self.screen, (255, 255, 0), (x - 5, y_img - 5, 74, 74), 3)

            self.screen.blit(img, (x, y_img))

        # 2. Define posição do texto como coluna vertical abaixo das imagens, centralizada na tela
        y_text_start = y_img + 100  # distância vertical para começar a lista de nomes
        text_x_center = config.SCREEN_WIDTH // 2  # centro horizontal da tela

        for i in range(len(self.players)):
            player_name = self.players[i]["name"]
            text_str = f"Jogador {i + 1}: {player_name}"
            if self.players[i]["character"] is not None:
                text_str += " ✔"

            text_surface = font_comics.render(text_str, True, (180, 180, 180))

            # Posição Y para cada texto (espacamento 35px)
            y_text = y_text_start + i * 35

            # Centraliza o texto na tela
            text_rect = text_surface.get_rect(center=(text_x_center, y_text))
            self.screen.blit(text_surface, text_rect)

    def draw_theme_selection(self):
        # Fonte padrão
        font_comics = pygame.font.SysFont("comicsansms", 42)

        # --- Fundo da pergunta centralizado no topo ---
        question_rect_x, question_rect_y = 80, 40
        question_rect_w, question_rect_h = 800, 60
        pygame.draw.rect(self.screen, (20, 20, 60),
                         (question_rect_x, question_rect_y, question_rect_w, question_rect_h), border_radius=10)

        # --- Imagem do personagem no canto superior direito ---
        player = self.players[self.current_player_turn]
        player_img = player["character"]
        img_size = 64
        img_scaled = pygame.transform.scale(player_img, (img_size, img_size))

        img_x = self.screen.get_width() - img_size - 20  # 20 de margem da direita
        img_y = 20  # margem superior
        self.screen.blit(img_scaled, (img_x, img_y))

        # Nome do jogador abaixo da imagem, centralizado abaixo da imagem
        name_text = font_comics.render(player["name"], True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(img_x + img_size // 2, img_y + img_size + 20))
        self.screen.blit(name_text, name_rect)

        # --- Texto "Escolha ou digite um tema" centralizado na tela ---
        choose_text = font_comics.render("Qual categoria vamos detonar agora?", True, (255, 255, 255))
        choose_rect = choose_text.get_rect(center=(self.screen.get_width() // 2, question_rect_y + 15))
        self.screen.blit(choose_text, choose_rect)

        # --- Área principal (meio da tela) ---
        center_x = self.screen.get_width() // 2
        base_y = 150  # começa a partir dessa altura

        if self.typing_custom_theme:
            # Mostra prompt e input centralizados
            input_prompt = font_comics.render("Qual o desafio de hoje? Defina o tema!", True, (255, 255, 0))
            prompt_rect = input_prompt.get_rect(center=(center_x, base_y))
            self.screen.blit(input_prompt, prompt_rect)

            input_text = font_comics.render(self.custom_theme_input or " ", True, (255, 255, 255))

            # Define padding e altura fixa
            padding_x = 20
            min_width = 600
            box_height = 60

            # Largura baseada no texto, com mínimo
            text_width = input_text.get_width()
            box_width = max(min_width, text_width + padding_x * 2)

            # Caixa centralizada
            input_box_rect = pygame.Rect(0, 0, box_width, box_height)
            input_box_rect.center = (center_x, base_y + 60)

            pygame.draw.rect(self.screen, (50, 50, 50), input_box_rect)
            pygame.draw.rect(self.screen, (255, 255, 0), input_box_rect, 2)
            self.screen.blit(input_text, (input_box_rect.x + 10, input_box_rect.y + 5))
        else:
            # Lista de temas centralizada
            self.theme_rects = []
            for i, theme in enumerate(self.themes):
                color = (255, 255, 0) if i == self.selected_theme_index else (200, 200, 200)
                theme_text = font_comics.render(theme, True, color)
                theme_rect = theme_text.get_rect(center=(center_x, base_y + i * 50))
                self.screen.blit(theme_text, theme_rect)
                self.theme_rects.append(theme_rect)

        current_time = pygame.time.get_ticks()
        if self.error_message and current_time < self.error_message_time:
            self.error_alpha += self.error_alpha_direction
            if self.error_alpha <= 50 or self.error_alpha >= 255:
                self.error_alpha_direction *= -1
                self.error_alpha = max(50, min(255, self.error_alpha))

            font = pygame.font.SysFont("comicsansms", 28, bold=True)
            text_surface = font.render(self.error_message, True, (255, 50, 50))
            text_surface.set_alpha(self.error_alpha)

            text_rect = text_surface.get_rect(center=(center_x, base_y + 130))
            self.screen.blit(text_surface, text_rect)

    def choose_theme(self, index):
        self.current_theme = self.themes[index]
        self.state = "roulette"
        self.letter_chosen = None
        self.timer_start = None
        self.remaining_time = 40
        self.warning_played = False

    def draw_roulette(self):
        self.letter_rects = []

        # Exibe pontuação de todos os jogadores no topo esquerdo
        font_scores = pygame.font.SysFont("comicsansms", 24)
        x_start = 30
        y_start = 130
        spacing_y = 30

        for i, player in enumerate(self.players):
            score_text = f"{player['name']}: {self.scores[i]} pts"
            color = (255, 255, 0) if i == self.current_player_turn else (200, 200, 200)
            score_surface = font_scores.render(score_text, True, color)
            self.screen.blit(score_surface, (x_start, y_start + i * spacing_y))

        # Fundo de título
        pygame.draw.rect(self.screen, (20, 20, 60), (80, 40, 800, 60), border_radius=10)
        title_font = pygame.font.SysFont("comicsansms", 42, bold=True)
        title_text = "Role a sorte: escolha sua letra"
        title_surface = title_font.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(config.SCREEN_WIDTH // 2, 70))
        self.screen.blit(title_surface, title_rect)

        # Imagem do personagem no canto superior direito
        character_img = self.players[self.current_player_turn]["character"]
        if character_img:
            img_rect = character_img.get_rect(topright=(config.SCREEN_WIDTH - 30, 30))
            self.screen.blit(character_img, img_rect)

            # Nome do jogador abaixo da imagem
            name_surface = self.font.render(self.players[self.current_player_turn]["name"], True, (255, 255, 0))
            name_rect = name_surface.get_rect(topright=(config.SCREEN_WIDTH - 40, img_rect.bottom + 10))
            self.screen.blit(name_surface, name_rect)

        # Letras da roleta
        for i, letter in enumerate(self.alphabet):
            color = (255, 255, 0) if i == self.current_letter_index else (200, 200, 200)
            letter_surface = self.font.render(letter, True, color)
            rect = letter_surface.get_rect(topleft=(50 + (i % 13) * 70, 300 + (i // 13) * 70))
            self.screen.blit(letter_surface, rect)
            self.letter_rects.append((letter, rect))

        if self.letter_chosen:
            screen_center_x = config.SCREEN_WIDTH // 2
            screen_height = config.SCREEN_HEIGHT

            # Mensagem de destaque (mais abaixo)
            msg_font = pygame.font.SysFont("comicsansms", 36)
            msg_text = msg_font.render("Letra sorteada!", True, (255, 255, 255))
            msg_rect = msg_text.get_rect(center=(screen_center_x, screen_height - 260))
            self.screen.blit(msg_text, msg_rect)

            # Letra escolhida grande no centro inferior
            big_font = pygame.font.SysFont("comicsansms", 100, bold=True)
            letter_text = big_font.render(self.letter_chosen, True, (255, 255, 0))
            letter_rect = letter_text.get_rect(center=(screen_center_x, screen_height - 170))
            self.screen.blit(letter_text, letter_rect)

            # Tema atual abaixo da letra
            theme_font = pygame.font.SysFont("comicsansms", 30, bold=True)
            theme_text = theme_font.render(f"Tópico da Rodada: {self.current_theme}", True, (255, 255, 255))
            theme_rect = theme_text.get_rect(center=(screen_center_x, screen_height - 70))
            self.screen.blit(theme_text, theme_rect)

    def draw_answer_input(self):
        screen_center_x = config.SCREEN_WIDTH // 2
        screen_height = config.SCREEN_HEIGHT
        font_comics = pygame.font.SysFont("comicsansms", 32)

        # Tema atual com fundo amarelo destacado
        theme_font = pygame.font.SysFont("comicsansms", 30, bold=True)
        theme_text = theme_font.render(f"Tópico da Rodada: {self.current_theme}", True, (255, 255, 255))  # branco

        padding_x, padding_y = 20, 10
        box_width = theme_text.get_width() + padding_x * 2
        box_height = theme_text.get_height() + padding_y * 2
        box_x = (config.SCREEN_WIDTH - box_width) // 2
        box_y = 30
        theme_box_rect = pygame.Rect(box_x, box_y, box_width, box_height)

        pygame.draw.rect(self.screen, (20, 20, 60), theme_box_rect, border_radius=12)
        self.screen.blit(theme_text, (box_x + padding_x, box_y + padding_y))

        # Espaçamento após o tema
        y_offset = box_y + box_height + 60

        # Frase principal estilizada (nome + letra) — maior, amarela, centralizada mais para baixo
        title_font = pygame.font.SysFont("comicsansms", 40, bold=True)
        title_text = f"{self.players[self.current_player_turn]['name']}, a palavra da vez é com"
        title_surface = title_font.render(title_text, True, (255, 255, 0))  # amarelo
        title_rect = title_surface.get_rect(center=(screen_center_x, y_offset))
        self.screen.blit(title_surface, title_rect)

        # Letra destacada logo abaixo, grande e amarela (igual a parte da letra sorteada)
        big_font = pygame.font.SysFont("comicsansms", 100, bold=True)
        letter_surface = big_font.render(self.current_letter, True, (255, 255, 0))
        letter_rect = letter_surface.get_rect(center=(screen_center_x, y_offset + 80))
        self.screen.blit(letter_surface, letter_rect)

        # Caixa para input (com borda e fundo escuro)
        input_box_width = 600
        input_box_height = 50
        input_box_x = (config.SCREEN_WIDTH - input_box_width) // 2
        input_box_y = y_offset + 180

        input_box_rect = pygame.Rect(input_box_x, input_box_y, input_box_width, input_box_height)
        pygame.draw.rect(self.screen, (30, 30, 30), input_box_rect, border_radius=8)  # fundo escuro
        pygame.draw.rect(self.screen, (255, 255, 0), input_box_rect, 3, border_radius=8)  # borda amarela

        # Texto dentro da caixa (resposta atual)
        answer_surface = self.font.render(self.current_answer, True, (255, 255, 0))
        answer_pos = (input_box_x + 10, input_box_y + (input_box_height - answer_surface.get_height()) // 2)
        self.screen.blit(answer_surface, answer_pos)

        # Cursor piscante (barra vertical)
        # Calcula a posição do cursor após o texto
        cursor_x = answer_pos[0] + answer_surface.get_width() + 2
        cursor_y_top = answer_pos[1]
        cursor_y_bottom = answer_pos[1] + answer_surface.get_height()

        # Pisca a cada meio segundo
        if (time.time() * 2) % 2 > 1:
            pygame.draw.line(self.screen, (255, 255, 0), (cursor_x, cursor_y_top), (cursor_x, cursor_y_bottom), 3)

        # Espaçamento para o timer
        timer_y = input_box_y + input_box_height + 200
        timer_surface = self.font.render(f"Contagem Regressiva: {int(self.remaining_time)}s", True, (255, 100, 100))
        timer_rect = timer_surface.get_rect(center=(screen_center_x, timer_y))
        self.screen.blit(timer_surface, timer_rect)

    def start_voting(self, word):
        self.voting_word = word
        self.votes = []
        self.vote_required = self.max_players - 1  # os outros jogadores votam
        self.current_voter = 0
        self.vote_result = None
        self.vote_start_time = time.time()
        self.state = "voting"

    def draw_voting(self):
        self.screen.fill((0, 0, 0))  # fundo escuro

        font = pygame.font.SysFont("comicsansms", 36)
        word_text = font.render(f"A palavra foi: {self.voting_word}", True, (255, 255, 255))
        word_rect = word_text.get_rect(center=(config.SCREEN_WIDTH // 2, 200))
        self.screen.blit(word_text, word_rect)

        prompt_font = pygame.font.SysFont("comicsansms", 28)
        voter_idx = (self.current_player_turn + self.current_voter + 1) % self.max_players
        voter_name = self.players[voter_idx]["name"]
        prompt_text = prompt_font.render(f"{voter_name}, essa palavra é válida? [S/N]", True, (255, 255, 0))
        prompt_rect = prompt_text.get_rect(center=(config.SCREEN_WIDTH // 2, 300))
        self.screen.blit(prompt_text, prompt_rect)

        votes_text = prompt_font.render(f"Votos: {len(self.votes)} / {self.vote_required}", True, (200, 200, 200))
        votes_rect = votes_text.get_rect(center=(config.SCREEN_WIDTH // 2, 380))
        self.screen.blit(votes_text, votes_rect)

        # --- Botões Sim e Não ---
        button_font = pygame.font.SysFont("comicsansms", 32, bold=True)

        # Define posições e tamanhos
        button_width, button_height = 120, 50
        screen_center_x = config.SCREEN_WIDTH // 2
        button_y = 450

        self.sim_button_rect = pygame.Rect(screen_center_x - button_width - 20, button_y, button_width, button_height)
        self.nao_button_rect = pygame.Rect(screen_center_x + 20, button_y, button_width, button_height)

        # Cor padrão dos botões
        sim_color = (0, 200, 0)
        nao_color = (200, 0, 0)

        # Se quiser, pode fazer efeito de hover (mouse passando por cima)
        mouse_pos = pygame.mouse.get_pos()
        if self.sim_button_rect.collidepoint(mouse_pos):
            sim_color = (0, 255, 0)
        if self.nao_button_rect.collidepoint(mouse_pos):
            nao_color = (255, 0, 0)

        # Desenha botões
        pygame.draw.rect(self.screen, sim_color, self.sim_button_rect, border_radius=8)
        pygame.draw.rect(self.screen, nao_color, self.nao_button_rect, border_radius=8)

        # Texto dos botões
        sim_text = button_font.render("SIM", True, (255, 255, 255))
        nao_text = button_font.render("NÃO", True, (255, 255, 255))

        sim_text_rect = sim_text.get_rect(center=self.sim_button_rect.center)
        nao_text_rect = nao_text.get_rect(center=self.nao_button_rect.center)

        self.screen.blit(sim_text, sim_text_rect)
        self.screen.blit(nao_text, nao_text_rect)

    def validate_word_online(self, word):
        return validate_word(word)





