import sqlite3
import pygame
import random
import time
import os
import sys


pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Звездные Войны Путь Адмирала")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
LIGHT_AQUAMARINE = (64, 224, 208)  # Бирюзовый цвет
TRANSPARENT = (0, 0, 0, 0)
TURQUOISE = (64, 224, 208)

# Путь к папке с изображениями
IMAGE_DIR = "images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# Загрузка изображений из папки
image_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
if not image_files:
    print(f"Ошибка: Нет изображений в папке '{IMAGE_DIR}'")
    pygame.quit()
    sys.exit()

images = [pygame.image.load(os.path.join(IMAGE_DIR, f)) for f in image_files]

# Переменные для смены изображений
current_image_index = 0
timer_event = pygame.USEREVENT + 1
pygame.time.set_timer(timer_event, 5000)

# Размеры и положение меню
MENU_WIDTH = 350
MENU_HEIGHT = 450
MENU_X = (WIDTH - MENU_WIDTH) // 2
MENU_Y = (HEIGHT - MENU_HEIGHT) // 2
menu_rect = pygame.Rect(MENU_X, MENU_Y, MENU_WIDTH, MENU_HEIGHT)

# Кнопка меню
BUTTON_HEIGHT = 40
BUTTON_MARGIN = 15
menu_buttons = ["Играть в историю", "Бортовой журнал и обучение", "Выход"]
button_rects = []
for i, text in enumerate(menu_buttons):
    button_y = MENU_Y + (BUTTON_HEIGHT + BUTTON_MARGIN) * i + BUTTON_MARGIN
    button_rect = pygame.Rect(MENU_X + BUTTON_MARGIN, button_y, MENU_WIDTH - 2 * BUTTON_MARGIN, BUTTON_HEIGHT)
    button_rects.append(button_rect)

# Шрифт для меню
font = pygame.font.Font(None, 30)

# Загрузка иконок
medal_icon_path = "medal_icon.png"
if os.path.exists(medal_icon_path):
    medal_icon = pygame.image.load(medal_icon_path)
    medal_icon = pygame.transform.scale(medal_icon, (18, 30))
else:
    print(f"Иконка медали '{medal_icon_path}' не найдена")
    medal_icon = None

coin_icon_path = "credits_icon.png"
if os.path.exists(coin_icon_path):
    coin_icon = pygame.image.load(coin_icon_path)
    coin_icon = pygame.transform.scale(coin_icon, (30, 30))
else:
    print(f"Иконка монеты '{coin_icon_path}' не найдена")
    coin_icon = None


conn = sqlite3.connect('game_data.db')
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS player_data (credits INTEGER, medals INTEGER)")
cursor.execute("INSERT INTO player_data (credits, medals) SELECT 5000, 1 WHERE NOT EXISTS (SELECT 1 FROM player_data)")
conn.commit()


def get_player_data():
    """Получает данные игрока из базы данных."""
    cursor.execute("SELECT credits, medals FROM player_data")
    data = cursor.fetchone()
    if data:
        return data[0], data[1]
    else:
        return 5000, 1


conn.commit()


# Загрузка и воспроизведение музыки
MUSIC_FILE = "music.mp3"
if os.path.exists(MUSIC_FILE):
    pygame.mixer.music.load(MUSIC_FILE)
    pygame.mixer.music.play(-1)
else:
    print(f"Музыкальный файл '{MUSIC_FILE}' не найден")

# Загрузка изображений
background_img = pygame.image.load("space_background.jpeg").convert()
venator_img = pygame.image.load("venator.png").convert_alpha()
bullet_img = pygame.image.load("bullet.png").convert_alpha()
enemy_bullet_img = pygame.image.load("enemy_bullet.png").convert_alpha()
game_over_img = pygame.image.load("game_over.jpg").convert_alpha()  # Загрузка изображения Game Over

# Параметры игры
BACKGROUND_SPEED = 10
VENATOR_SPEED = 6
BULLET_SPEED = 15
ENEMY_SPEED = 2
ENEMY_RESPAWN_DISTANCE = 20
MAX_BULLETS = 10
RELOAD_TIME = 3
HP_REGEN_TIME = 20
GAME_DURATION = 180
INITIAL_HP_INVULNERABILITY = 10
MAX_ENEMIES_PER_5_SEC = 3
ENEMY_SPAWN_INTERVAL = 5
ENEMY_FOLDER = "enemies"  # каталог для врагов
ENEMY_DESTROYED_FOLDER = "enemies_destroyed"  # каталог для уничтоженных врагов
MAX_ENEMIES_AT_ONCE = 10  # максимальное количество врагов на экране
ENEMY_FIRE_RANGE = 10
ENEMY_FIRE_COOLDOWN = 1  # задержка стрельбы
ENEMY_BULLET_SPEED = -10

# Масштабирование изображений
VENATOR_SCALE = 0.15
BULLET_SCALE = 0.10
ENEMY_SCALE = 0.12
ENEMY_DESTROYED_SCALE = 0.12
ICON_SIZE = 16

# Масштабирование иконок
credits_icon = pygame.transform.scale(coin_icon, (ICON_SIZE, ICON_SIZE))
hp_icon = pygame.image.load("hp_icon.png").convert_alpha()
hp_icon = pygame.transform.scale(hp_icon, (ICON_SIZE, ICON_SIZE))
medal_icon = pygame.transform.scale(medal_icon, (ICON_SIZE, 32))

venator_img = pygame.transform.scale(venator_img, (
    int(venator_img.get_width() * VENATOR_SCALE), int(venator_img.get_height() * VENATOR_SCALE)))
bullet_img = pygame.transform.scale(bullet_img, (
    int(bullet_img.get_width() * BULLET_SCALE), int(bullet_img.get_height() * BULLET_SCALE)))
enemy_bullet_img = pygame.transform.scale(enemy_bullet_img, (
    int(enemy_bullet_img.get_width() * 0.10), int(enemy_bullet_img.get_height() * 0.10)))
game_over_img = pygame.transform.scale(game_over_img,
                                       (int(game_over_img.get_width() * 0.75), int(game_over_img.get_height() * 0.75)))

# Загрузка врагов из каталога
enemy_images = {}
for filename in os.listdir(ENEMY_FOLDER):
    if filename.endswith(".png"):
        enemy_image = pygame.image.load(os.path.join(ENEMY_FOLDER, filename)).convert_alpha()
        enemy_image = pygame.transform.scale(enemy_image, (
            int(enemy_image.get_width() * ENEMY_SCALE), int(enemy_image.get_height() * ENEMY_SCALE)))

        destroyed_filename = os.path.splitext(filename)[0] + ".png"
        destroyed_path = os.path.join(ENEMY_DESTROYED_FOLDER, destroyed_filename)

        destroyed_image = None
        if os.path.exists(destroyed_path):
            destroyed_image = pygame.image.load(destroyed_path).convert_alpha()
            destroyed_image = pygame.transform.scale(destroyed_image, (
                int(destroyed_image.get_width() * ENEMY_DESTROYED_SCALE),
                int(destroyed_image.get_height() * ENEMY_DESTROYED_SCALE)))
        else:
            destroyed_image = pygame.transform.scale(enemy_image,
                                                     (int(enemy_image.get_width() * ENEMY_DESTROYED_SCALE),
                                                      int(enemy_image.get_height() * ENEMY_DESTROYED_SCALE)))

        enemy_images[filename] = (enemy_image, destroyed_image)
# Загрузка звуков
shoot_sound = pygame.mixer.Sound("shoot.mp3")
enemy_hit_sound = pygame.mixer.Sound("enemy_hit.mp3")
player_hit_sound = pygame.mixer.Sound("player_hit.mp3")

# Игровые переменные
game_state = "menu"  # Состояние игры (menu, game, log)
hero_image = None
hero_text = ""
game_background = None
game_bottom_background = None
log_text = ""
current_log_page = 0
log_font = pygame.font.Font(None, 24)
log_page_lines = []


class Venator(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = venator_img
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = 0
        self.speed_x = 0
        self.hitbox = self.rect  # Хитбокс для столкновений

    def update(self):
        self.rect.y += self.speed_y
        self.rect.x += self.speed_x
        self.hitbox.x = self.rect.x  # Обновляем хитбокс
        self.hitbox.y = self.rect.y

        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

    def move_up(self):
        self.speed_y = -VENATOR_SPEED

    def move_down(self):
        self.speed_y = VENATOR_SPEED

    def move_left(self):
        self.speed_x = -VENATOR_SPEED

    def move_right(self):
        self.speed_x = VENATOR_SPEED

    def stop(self):
        self.speed_y = 0
        self.speed_x = 0


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, image, speed):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = self.rect
        self.speed = speed
        self.player_bullet = True  # Флаг, определяющий, является ли пуля игрока

    def update(self):
        self.rect.x += self.speed
        self.hitbox.x = self.rect.x
        self.hitbox.y = self.rect.y

        if self.rect.left > WIDTH or self.rect.right < 0 or self.rect.top < 0 or self.rect.bottom > HEIGHT:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_image, destroyed_image):
        super().__init__()
        self.image = enemy_image
        self.rect = self.image.get_rect(topright=(WIDTH + ENEMY_RESPAWN_DISTANCE, random.randint(50, HEIGHT - 50)))
        self.hitbox = self.rect  # Хитбокс для столкновений
        self.destroyed = False
        self.destruction_time = None
        self.hp_removed = False  # Для избежания многократного вычитания hp
        self.destroyed_image = destroyed_image
        self.last_fire_time = 0  # время последнего выстрела

    def update(self, venator, bullets, all_sprites):
        if not self.destroyed:
            self.rect.x -= ENEMY_SPEED
            self.hitbox.x = self.rect.x  # Обновляем хитбокс
            self.hitbox.y = self.rect.y

            if self.rect.right < 0:
                self.kill()
            if abs(self.rect.centery - venator.rect.centery) <= ENEMY_FIRE_RANGE and \
                    time.time() - self.last_fire_time >= ENEMY_FIRE_COOLDOWN:
                bullet = Bullet(self.rect.left, self.rect.centery, enemy_bullet_img, ENEMY_BULLET_SPEED)
                bullet.player_bullet = False  # Устанавливаем, что это пуля врага
                bullets.add(bullet)
                all_sprites.add(bullet)
                self.last_fire_time = time.time()

        else:
            if time.time() - self.destruction_time >= 3:
                self.kill()

    def destroy(self, hp_operations_enabled, hp):
        if not self.hp_removed and hp_operations_enabled:
            hp -= 500
            self.hp_removed = True
        self.image = self.destroyed_image
        self.destroyed = True
        self.destruction_time = time.time()
        return hp


# Игровые объекты
venator = Venator(100, HEIGHT // 2)
all_sprites = pygame.sprite.Group()
all_sprites.add(venator)

bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
#  Игровые переменные
hp = 1000
reload_counter = 0
bullets_shot = 0
game_start_time = time.time()
last_hp_regen = time.time()
font = pygame.font.Font(None, 30)
reloading = False
reload_start_time = 0
hp_operations_enabled = False
credits = 5000
medals = 0
last_enemy_spawn_time = time.time()
enemy_spawn_count = 0
enemy_last_spawn = time.time()
game_over = False  # Флаг для проверки Game Over
# Кнопка
button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50)  # Координаты и размер кнопки
button_color = LIGHT_AQUAMARINE  # Бирюзовый цвет
button_hover_color = RED
button_text = "Играть снова"
running = True
background_x = 0


def load_game_assets():
    global hero_image, hero_text, game_background, game_bottom_background

    hero_image_path = os.path.join(IMAGE_DIR, "hero.png")  # Файл с картинкой героя в папке images
    if os.path.exists(hero_image_path):
        hero_image = pygame.image.load(hero_image_path)
        hero_image = pygame.transform.scale(hero_image, (200, 200))
    else:
        print(f"Картинка героя '{hero_image_path}' не найдена")

    hero_text = "Я готов к бою!"  # Текст, который говорит герой

    game_background_path = os.path.join(IMAGE_DIR, "game_bg.png")  # Файл с фоном игры в папке images
    if os.path.exists(game_background_path):
        game_background = pygame.image.load(game_background_path)
        game_background = pygame.transform.scale(game_background, (WIDTH, HEIGHT))
    else:
        print(f"Фон '{game_background_path}' не найден")

    game_bottom_bg_path = os.path.join(IMAGE_DIR, "bottom_bg.png")  # Нижний фон
    if os.path.exists(game_bottom_bg_path):
        game_bottom_background = pygame.image.load(game_bottom_bg_path)
        game_bottom_background = pygame.transform.scale(game_bottom_background, (WIDTH, 100))
    else:
        print(f"Фон  '{game_bottom_bg_path}' не найден")


def load_log():
    global log_text, log_page_lines, current_log_page
    log_file_path = "log.txt"  # Файл с бортовым журналом
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as file:
            log_text = file.read()
    else:
        log_text = "Файл бортового журнала не найден"

    log_lines = log_text.split('\n')  # Разбить на строки
    lines_per_page = 10  # Строк на страницу
    log_page_lines = [log_lines[i:i + lines_per_page] for i in
                      range(0, len(log_lines), lines_per_page)]  # Разбить на страницы
    current_log_page = 0  # Начать с первой страницы


def handle_log_input(event):
    global current_log_page
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_LEFT:
            if current_log_page > 0:
                current_log_page -= 1
        elif event.key == pygame.K_RIGHT:
            if current_log_page < len(log_page_lines) - 1:
                current_log_page += 1


def spawn_enemies(enemies, enemy_images, all_sprites):
    for _ in range(MAX_ENEMIES_PER_5_SEC):
        if len(enemies) < MAX_ENEMIES_AT_ONCE:

            valid_spawn = False
            while not valid_spawn:
                filename = random.choice(list(enemy_images.keys()))
                enemy_image, destroyed_image = enemy_images[filename]
                new_enemy = Enemy(enemy_image, destroyed_image)
                valid_spawn = True

                # Проверка столкновений с другими врагами
                for existing_enemy in enemies:
                    if new_enemy.hitbox.colliderect(existing_enemy.hitbox):
                        valid_spawn = False
                        break  # Повторить создание, если есть столкновение

            enemies.add(new_enemy)
            all_sprites.add(new_enemy)


def draw_game_over_screen(screen, font, credits, medals):
    screen.blit(game_over_img, (WIDTH // 2 - game_over_img.get_width() // 2,
                                HEIGHT // 2 - game_over_img.get_height() // 2 - 50))  # отрисовка game over картинки
    pygame.draw.rect(screen, button_color, button_rect)
    text_surface = font.render(button_text, True, WHITE)
    text_rect = text_surface.get_rect(center=button_rect.center)
    screen.blit(text_surface, text_rect)

    credits_text = font.render(f"Credits: {credits}", True, WHITE)
    screen.blit(credits_text, (WIDTH // 2 - credits_text.get_width() // 2, HEIGHT // 2 + 100))

    medals_text = font.render(f"Medals: {medals}", True, WHITE)
    screen.blit(medals_text, (WIDTH // 2 - medals_text.get_width() // 2, HEIGHT // 2 + 130))


coin_count, medal_count = get_player_data()


def reset_game(credits, medals):
    global hp, game_start_time, last_hp_regen, reloading, reload_start_time, bullets_shot, enemies, enemy_bullets, \
        all_sprites, game_over
    hp = 1000
    game_start_time = time.time()
    last_hp_regen = time.time()
    reloading = False
    reload_start_time = 0
    bullets_shot = 0

    enemies.empty()
    enemy_bullets.empty()
    all_sprites.empty()
    all_sprites.add(venator)
    game_over = False
    return credits, medals


while running:
    cursor.execute("UPDATE player_data SET credits=?, medals=?", (credits, medals))
    conn.commit()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == timer_event:
            current_image_index = (current_image_index + 1) % len(images)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                for i, rect in enumerate(button_rects):
                    if rect.collidepoint(mouse_pos):
                        if i == 0 and game_state == "menu":
                            game_state = "game"
                            load_game_assets()
                        elif i == 1 and game_state == "menu":
                            game_state = "log"
                            load_log()
                        elif i == 2 and game_state == "menu":
                            pygame.quit()
                            sys.exit()
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.size
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

            MENU_X = (WIDTH - MENU_WIDTH) // 2  # Обновляем положение по центру
            MENU_Y = (HEIGHT - MENU_HEIGHT) // 2
            menu_rect = pygame.Rect(MENU_X, MENU_Y, MENU_WIDTH, MENU_HEIGHT)

            button_rects = []
            for i, text in enumerate(menu_buttons):
                button_y = MENU_Y + (BUTTON_HEIGHT + BUTTON_MARGIN) * i + BUTTON_MARGIN
                button_rect = pygame.Rect(MENU_X + BUTTON_MARGIN, button_y, MENU_WIDTH - 2 * BUTTON_MARGIN,
                                          BUTTON_HEIGHT)
                button_rects.append(button_rect)
        if game_state == "log":
            handle_log_input(event)
        if game_state == "game":
            if not game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        venator.move_up()
                    if event.key == pygame.K_DOWN:
                        venator.move_down()
                    if event.key == pygame.K_LEFT:
                        venator.move_left()
                    if event.key == pygame.K_RIGHT:
                        venator.move_right()
                    if event.key == pygame.K_SPACE and not reloading:
                        if bullets_shot < MAX_BULLETS:
                            bullet = Bullet(venator.rect.right, venator.rect.centery, bullet_img, BULLET_SPEED)
                            bullets.add(bullet)
                            all_sprites.add(bullet)
                            shoot_sound.play()  # Воспроизведение звука выстрела игрока
                            bullets_shot += 1
                        if bullets_shot == MAX_BULLETS:
                            reloading = True
                            reload_start_time = time.time()
                            bullets_shot = 0
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN or event.key == pygame.K_LEFT \
                            or event.key == pygame.K_RIGHT:
                        venator.stop()

            else:  # обрабатываем только нажатие на кнопку если игра закончена
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if button_rect.collidepoint(mouse_pos):
                        credits, medals = reset_game(credits, medals)
                        venator.rect.center = (100, HEIGHT // 2)
                        game_state = "game"

    # Отрисовка экрана
    screen.fill(BLACK)

    if game_state == "menu":
        # Отображение текущего изображения
        image = images[current_image_index]
        image_rect = image.get_rect(center=(WIDTH / 2, HEIGHT / 2))
        screen.blit(image, image_rect)

        # Прозрачный прямоугольник для меню
        menu_surface = pygame.Surface((MENU_WIDTH, MENU_HEIGHT), pygame.SRCALPHA)
        screen.blit(menu_surface, (MENU_X, MENU_Y))

        for i, rect in enumerate(button_rects):
            pygame.draw.rect(screen, TURQUOISE, rect)
            text_surface = font.render(menu_buttons[i], True, BLACK)
            text_rect = text_surface.get_rect(center=rect.center)
            screen.blit(text_surface, text_rect)

        # Счетчики
        counter_font = pygame.font.Font(None, 30)

        # Медаль
        medal_text = counter_font.render(str(medal_count), True, WHITE)
        medal_text_rect = medal_text.get_rect(topleft=(10, 10))
        screen.blit(medal_text, medal_text_rect)
        if medal_icon:
            screen.blit(medal_icon, (medal_text_rect.right + 5, 10))

        # Монета
        coin_text = counter_font.render(str(coin_count), True, WHITE)
        coin_text_rect = coin_text.get_rect(topleft=(10, 50))
        screen.blit(coin_text, coin_text_rect)
        if coin_icon:
            screen.blit(coin_icon, (coin_text_rect.right + 5, 50))

    elif game_state == "game":
        # Обновление фона
        if not game_over:
            background_x -= BACKGROUND_SPEED
            if background_x < -background_img.get_width():
                background_x = 0
        # Отображение фона
        screen.blit(background_img, (background_x, 0))
        screen.blit(background_img, (background_x + background_img.get_width(), 0))
        #  Обновление перезарядки
        if not game_over:
            if reloading:
                if time.time() - reload_start_time >= RELOAD_TIME:
                    reloading = False

            # Включение операций с HP через 10 секунд
            if not hp_operations_enabled and time.time() - game_start_time >= INITIAL_HP_INVULNERABILITY:
                hp_operations_enabled = True

            # Обновление HP
            if hp_operations_enabled:
                if time.time() - last_hp_regen >= HP_REGEN_TIME:
                    hp += 400
                    last_hp_regen = time.time()

            # Спавн врагов каждые 5 секунд
            if time.time() - enemy_last_spawn >= ENEMY_SPAWN_INTERVAL:
                spawn_enemies(enemies, enemy_images, all_sprites)
                enemy_last_spawn = time.time()
            # Обновление игровых объектов
            for bullet in bullets:
                bullet.update()
            for bullet in enemy_bullets:
                bullet.update()
            venator.update()

            for enemy in enemies:
                enemy.update(venator, enemy_bullets, all_sprites)

            # Проверка коллизий пули с врагами
            for bullet in list(
                    bullets):  # Используем list(bullets) для безопасного удаления элементов во время итерации
                for enemy in enemies:
                    if bullet.hitbox.colliderect(enemy.hitbox):
                        bullets.remove(bullet)
                        bullet.kill()
                        if not enemy.destroyed:
                            enemy.destroy(hp_operations_enabled, hp)
                            if hp_operations_enabled:
                                credits += 500
                                enemy_hit_sound.play()  # Воспроизведение звука попадания по врагу
                        break
            # Проверка коллизий врагов с венатором
            if hp_operations_enabled:
                for enemy in enemies:
                    if venator.hitbox.colliderect(enemy.hitbox):
                        if not enemy.destroyed:
                            hp = enemy.destroy(hp_operations_enabled, hp)
                            player_hit_sound.play()  # Воспроизведение звука попадания по игроку
            # Проверка коллизий вражеских пуль с венатором
            if hp_operations_enabled:
                for bullet in list(enemy_bullets):  # Проверка вражеских пуль с игроком
                    if bullet.hitbox.colliderect(venator.hitbox):
                        enemy_bullets.remove(bullet)
                        bullet.kill()
                        hp -= 200
                        player_hit_sound.play()  # Воспроизведение звука попадания по игроку

            # Проверка на проигрыш
            if hp <= 0:
                game_over = True

            # Проверка на выигрыш по времени
            game_time_elapsed = time.time() - game_start_time
            if game_time_elapsed >= GAME_DURATION:
                medals += 1
                game_over = True

        # Отображение фона
        if game_background:
            screen.blit(game_background, (0, 0))

        if game_bottom_background:
            screen.blit(game_bottom_background, (0, HEIGHT - game_bottom_background.get_height()))

        # Отображение героя
        if hero_image:
            hero_rect = hero_image.get_rect(topleft=(50, HEIGHT - 300))
            screen.blit(hero_image, hero_rect)
            text_font = pygame.font.Font(None, 40)
            text_surface = text_font.render(hero_text, True, WHITE)
            text_rect = text_surface.get_rect(topleft=(hero_rect.right + 20, hero_rect.top + 20))
            screen.blit(text_surface, text_rect)
        all_sprites.draw(screen)
        if not game_over:  # отрисовка интерфейса если игра не закончена
            # Отрисовка счетчиков с иконками
            icon_x = 10
            text_x = 40
            y_offset = 10
            spacing = 40

            # Кредиты
            screen.blit(credits_icon, (icon_x, y_offset))
            credits_text = font.render(f"{credits}", True, WHITE)
            screen.blit(credits_text, (text_x, y_offset))

            # HP
            screen.blit(hp_icon, (icon_x, y_offset + spacing))
            hp_text = font.render(f"{hp}", True, WHITE)
            screen.blit(hp_text, (text_x, y_offset + spacing))

            # Медали
            screen.blit(medal_icon, (icon_x, y_offset + 2 * spacing))
            medals_text = font.render(f"{medals}", True, WHITE)
            screen.blit(medals_text, (text_x, y_offset + 2 * spacing))

            # перезарядка
            if not reloading:
                bullets_text = font.render(f"{bullets_shot}/{MAX_BULLETS}", True, WHITE)
                pygame.draw.circle(screen, BLACK, (30, HEIGHT - 30), 20)
                screen.blit(bullets_text, (15, HEIGHT - 40))
            else:
                reload_text = font.render(f"{int(RELOAD_TIME - (time.time() - reload_start_time))}", True, WHITE)
                pygame.draw.circle(screen, BLACK, (WIDTH - 30, HEIGHT - 30), 20)
                screen.blit(reload_text, (WIDTH - 38, HEIGHT - 40))
        else:  # отрисовка экрана game over
            draw_game_over_screen(screen, font, credits, medals)

    elif game_state == "log":
        text_y = 50
        if log_page_lines:
            for line in log_page_lines[current_log_page]:
                text_surface = log_font.render(line, True, WHITE)
                text_rect = text_surface.get_rect(topleft=(50, text_y))
                screen.blit(text_surface, text_rect)
                text_y += 30

        page_text = log_font.render(f"Страница {current_log_page + 1} / {len(log_page_lines)}", True, WHITE)
        page_rect = page_text.get_rect(center=(WIDTH / 2, HEIGHT - 50))
        screen.blit(page_text, page_rect)
    pygame.display.flip()
    # Задержка
    pygame.time.delay(30)
conn.close()
pygame.quit()
sys.exit()
