import json
import sys

import pygame.display

from scripts.entities import *
from scripts.utils import *
from scripts.tilemap import TileMap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark
import random

# 界面大小
WIDTH = 1280
HEIGHT = 960
FPS = 60


class Game:
    def __init__(self, width, height, fps):
        pygame.init()
        self.WIDTH = width
        self.HEIGHT = height
        # 帧数
        self.FPS = fps
        pygame.display.set_caption("Ninja_frog")
        pygame.display.set_icon(pygame.image.load("assets/images/icon.png"))
        # 设置窗口
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        # Surface功能创建一个空的图片
        self.displayer = pygame.Surface((640, 480), pygame.SRCALPHA)
        self.displayer_2 = pygame.Surface((640, 480))

        self.clock = pygame.time.Clock()
        self.movement = [False, False]

        self.assets = {
            "player": load_image("entities/player.png"),
            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "large_decor": load_images("tiles/large_decor"),
            "stone": load_images("tiles/stone"),
            "background": load_image("background.png"),
            "clouds": load_images("clouds"),
            "enemy/idle": Animation(load_images("entities/enemy/idle"), img_dur=6),
            "enemy/run": Animation(load_images("entities/enemy/run"), img_dur=4),
            "player/idle": Animation(load_images("entities/ninja_frog/idle"), img_dur=6),
            "player/jump": Animation(load_images("entities/ninja_frog/jump")),
            "player/run": Animation(load_images("entities/ninja_frog/run"), img_dur=4),
            "player/slide": Animation(load_images("entities/player/slide")),
            "player/wall_slide": Animation(load_images("entities/ninja_frog/wall_slide")),
            "player/hit": Animation(load_images("entities/ninja_frog/hit"), loop=False),
            "particle/leaf": Animation(
                load_images("particles/leaf"), img_dur=12, loop=False
            ),
            "particle/particle": Animation(
                load_images("particles/particle"), img_dur=6, loop=False
            ),
            "gun": load_image("gun.png"),
            "projectile": load_image("projectile.png"),
            "heart": load_image("heart.png")
        }
        self.sfx = {
            "jump": pygame.mixer.Sound("assets/sfx/jump.wav"),
            "dash": pygame.mixer.Sound("assets/sfx/dash.wav"),
            "hit": pygame.mixer.Sound("assets/sfx/hit.wav"),
            "shoot": pygame.mixer.Sound("assets/sfx/shoot.wav"),
            "ambience": pygame.mixer.Sound("assets/sfx/ambience.wav"),
        }
        self.music = load_musics("assets/music/")
        # 音量大小
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.5)
        self.clouds = Clouds(self.assets["clouds"], count=16)

        self.player = Player(self, (400, 100), (12, 12))

        self.tilemap = TileMap(self, tile_size=16)
        self.leaf_spawners = []
        self.enemies = []
        self.projectiles = []
        self.particles = []
        self.sparks = []
        self.scroll = [0, 0]
        self.maxlives = 3
        self.lives = self.maxlives
        self.level = 0
        self.total_levels = 2
        self.load_settings()
        self.screen_shake = 0
        self.transition = -30
        self.text_font = pygame.font.Font("assets/font/Uranus_Pixel_11Px.ttf", 30)
        self.game_over = False
        self.game_over_text = self.text_font.render("Thank you for playing!", True, (255, 0, 0))
        self.load_level(self.level)

    def load_settings(self):
        f = open("settings.json", "r")
        game_settings = json.load(f)
        self.total_levels = game_settings['total_levels'] - 1
        self.maxlives = game_settings['lives']

    def load_level(self, map_id):
        pygame.mixer.music.stop()
        music_index = self.level % len(self.music)
        pygame.mixer.music.load(self.music[music_index])
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)
        self.tilemap.load('assets/maps/' + str(map_id) + '.json')
        self.leaf_spawners = []
        for tree in self.tilemap.extract([("large_decor", 2)], keep=True):
            self.leaf_spawners.append(
                pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 13)
            )
        self.enemies = []
        for spawner in self.tilemap.extract([("spawners", 0), ("spawners", 1)], keep=False):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
                self.player.velocity = [0, 0]
                self.player.hit = 0
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

        self.projectiles = []
        self.particles = []
        self.scroll = [0, 0]
        self.lives = self.maxlives
        self.transition = -40

    def run(self):
        # 参数里面是循环次数，
        pygame.mixer.music.play(-1)
        self.sfx["ambience"].play(-1)
        while True:
            self.displayer.fill((0, 0, 0, 0))
            self.displayer_2.blit(
                pygame.transform.scale(
                    self.assets["background"], self.displayer.get_size()
                ),
                (0, 0),
            )
            # 屏幕振动逐渐减少

            self.screen_shake = max(0, self.screen_shake - 1)

            if not len(self.enemies) and self.game_over is False:
                self.transition += 1
                if self.transition > 40:
                    self.level += 1
                    if self.level > self.total_levels:
                        self.game_over = True
                    else:
                        self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1

            if self.lives <= 0 and not self.game_over:
                self.lives -= 1
                self.transition += 1
                # 也相当于一个计时的功能，让玩家看到自己死
                if self.lives < -40:
                    self.load_level(self.level)
            else:
                # 展示剩余的生命值
                for i in range(self.lives):
                    self.displayer_2.blit(self.assets["heart"], (8 + i * 16, 0))
            self.scroll[0] += (
                                      self.player.rect().centerx
                                      - self.displayer.get_width() / 2
                                      - self.scroll[0]
                              ) / 30
            self.scroll[1] += (
                                      self.player.rect().centery
                                      - self.displayer.get_height() / 2
                                      - self.scroll[1]
                              ) / 30

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            for rect in self.leaf_spawners:
                # 不乘以一个大数字，会一直生成叶子，我们不想这样
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (
                        rect.x + random.random() * rect.width,
                        rect.y + random.random() * rect.height,
                    )
                    self.particles.append(
                        Particle(
                            self,
                            "leaf",
                            pos,
                            velocity=[-0.1, 0.3],
                            frame=random.randint(0, 20),
                        )
                    )

            self.clouds.update()
            self.clouds.render(self.displayer, offset=render_scroll)

            self.tilemap.render(self.displayer, offset=render_scroll)
            if self.lives > 0:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.displayer, offset=render_scroll)

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                if kill:
                    self.enemies.remove(enemy)
                enemy.render(self.displayer, offset=render_scroll)

            # projectile的格式： [[x,y],direction,timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.displayer.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0],
                                          projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(
                            Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0),
                                  2 + random.random()))
                elif projectile[2] > 240:
                    self.projectiles.remove(projectile)
                # 只要不是在冲刺过程中就判断是否击中，冲刺时是不会被击中的
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.sfx['hit'].play()
                        self.player.hit = projectile[1]
                        self.screen_shake = max(16, self.screen_shake)
                        self.lives -= 1
                        self.projectiles.remove(projectile)
                        for i in range(15):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center,
                                                           velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                                     math.sin(angle + math.pi) * speed * 0.5],
                                                           frame=random.randint(0, 7)))
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.displayer, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)
            # 把displayer转换成黑白，即2种颜色的图片二进制
            display_mask = pygame.mask.from_surface(self.displayer)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
                self.displayer_2.blit(display_sillhouette, offset)

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.displayer, offset=render_scroll)
                if particle.type == 'leaf':
                    # 模拟左右摇摆
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)

            for event in pygame.event.get():
                # 按窗口上的X
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        if self.player.jump():
                            self.sfx['jump'].play()
                    if event.key == pygame.K_x or event.key == pygame.K_j:
                        self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        self.movement[1] = False

            if self.transition:
                transition_surf = pygame.Surface(self.displayer.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255),
                                   (self.displayer.get_width() // 2, self.displayer.get_height() // 2),
                                   (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.displayer.blit(transition_surf, (0, 0))
            screen_shake_offset = (random.random() * self.screen_shake - self.screen_shake / 2,
                                   random.random() * self.screen_shake - self.screen_shake / 2)
            # 游戏结束打出结束文字
            if self.game_over:
                self.displayer.blit(self.game_over_text,
                                    (self.displayer.get_width() // 2 - self.game_over_text.get_width() // 2,
                                     self.displayer.get_height() // 2 - self.game_over_text.get_height() // 2))
                pygame.display.flip()

            self.displayer_2.blit(self.displayer, (0, 0))

            self.screen.blit(
                pygame.transform.scale(self.displayer_2, self.screen.get_size()), screen_shake_offset
            )
            # 更新窗口上的东西，把东西画出来
            pygame.display.update()
            self.clock.tick(FPS)


def main():
    game = Game(WIDTH, HEIGHT, FPS)
    game.run()


if __name__ == "__main__":
    main()
