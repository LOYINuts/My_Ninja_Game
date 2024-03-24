import sys
import math

import pygame
from scripts.entities import *
from scripts.utils import *
from scripts.tilemap import TileMap
from scripts.clouds import Clouds
from scripts.particle import Particle
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
        pygame.display.set_caption("忍者")
        # 设置窗口
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        # Surface功能创建一个空的图片
        self.displayer = pygame.Surface((640, 480))

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
        }
        self.clouds = Clouds(self.assets["clouds"], count=16)

        self.player = Player(self, (400, 100), (12, 12))

        self.tilemap = TileMap(self, tile_size=16)
        self.leaf_spawners = []
        self.enemies = []
        self.projectiles = []
        self.particles = []
        self.sparks = []
        self.scroll = [0, 0]
        self.load_level(0)

    def load_level(self, map_id):
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
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

        self.projectiles = []
        self.particles = []
        self.scroll = [0, 0]

    def run(self):
        while True:
            self.displayer.blit(
                pygame.transform.scale(
                    self.assets["background"], self.displayer.get_size()
                ),
                (0, 0),
            )

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

            self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
            self.player.render(self.displayer, offset=render_scroll)

            for enemy in self.enemies.copy():
                enemy.update(self.tilemap, (0, 0))
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
                elif projectile[2] > 240:
                    self.projectiles.remove(projectile)
                # 只要不是在冲刺过程中就判断是否击中，冲刺时是不会被击中的
                elif abs(self.player.dashing < 20):
                    if self.player.rect().collidepoint(projectile[0]):
                        self.player.hit = projectile[1]
                        self.projectiles.remove(projectile)

            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.displayer,offset=render_scroll)
                if self.kill:
                    self.sparks.remove(spark)

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
                        self.player.jump()
                    if event.key == pygame.K_x or event.key == pygame.K_j:
                        self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        self.movement[1] = False

            self.screen.blit(
                pygame.transform.scale(self.displayer, self.screen.get_size()), (0, 0)
            )
            # 更新窗口上的东西，把东西画出来
            pygame.display.update()
            self.clock.tick(FPS)


def main():
    game = Game(WIDTH, HEIGHT, FPS)
    game.run()


if __name__ == "__main__":
    main()
