import random

from scripts.particle import *
from scripts.spark import *


class PhysicsEntity:

    # 使用game作为参数好与game的变量互动，pos是指物体生成的位置，size大小
    def __init__(self, game, e_type, pos, size):
        """
        :param game: Game instance，为了更好的与game中的元素交互
        :param e_type: 实体类型
        :param pos: 实体生成的位置
        :param size: 大小
        """

        self.game = game
        self.type = e_type
        # 不用元组是因为元组不好更改
        self.pos = list(pos)
        self.size = size
        # 位置的改变速度
        self.velocity = [0.0, 0.0]
        self.collisions = {"up": False, "down": False, "left": False, "right": False}
        self.action = ""
        self.anim_offset = (0, 0)
        self.flip = False
        self.set_action("idle")
        self.animation = self.game.assets[self.type + "/" + self.action].copy()
        self.last_movement = [0, 0]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + "/" + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        """
        更新物体的位置
        :param movement:强制移动的距离
        :param tilemap:地图
        :return:
        """
        # 物体的移动取决于强制移动和自身的速度

        self.collisions = {"up": False, "down": False, "left": False, "right": False}
        frame_movement = (
            movement[0] + self.velocity[0],
            movement[1] + self.velocity[1],
        )

        self.pos[0] += frame_movement[0]

        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions["right"] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions["left"] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]

        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions["down"] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions["up"] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        self.velocity[1] = min(3.5, self.velocity[1] + 0.1)

        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        surf.blit(
            pygame.transform.flip(self.animation.img(), self.flip, False),
            (
                self.pos[0] - offset[0] + self.anim_offset[0],
                self.pos[1] - offset[1] + self.anim_offset[1],
            ),
        )
        # surf.blit(self.game.assets['player'], (self.pos[0] - offset[0], self.pos[1] - offset[1]))


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)
        self.walking = 0
        self.anim_offset = (-3, -3)

    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            # 往前后看7个像素，就是判断前方还有没有路，有就继续走，没有就得转向了，敌人
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if self.collisions['right'] or self.collisions['left']:
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                # 如果在差不多同一行
                if abs(dis[1]) < 16:
                    # 敌人朝左边，玩家也在敌人左边
                    if self.flip and dis[0] < 0:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi,
                                                          2 + random.random()))
                    if not self.flip and dis[0] > 0:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5,
                                                          2 + random.random()))

        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)

        super().update(tilemap, movement=movement)

        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.sfx['hit'].play()
                self.game.screen_shake = max(16, self.game.screen_shake)
                for i in range(15):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center,
                                                        velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                                  math.sin(angle + math.pi) * speed * 0.5],
                                                        frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                return True

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)

        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (
                self.rect().centerx - 2 - self.game.assets['gun'].get_width() - offset[0],
                self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 2 - offset[0], self.rect().centery - offset[1]))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "player", pos, size)
        # 在空中的时间
        self.air_time = 0
        # 跳跃剩余次数
        self.jumps = 1
        # 墙上滑行
        self.wall_slide = False
        # 冲刺攻击
        self.dashing = 0
        self.hit = 0

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)
        if self.flip:
            self.anim_offset = (-3, -3)
        else:
            self.anim_offset = (0, -3)
        self.air_time += 1
        if self.air_time > 180:
            self.game.lives = 0
            self.game.sfx['hit'].play()
            if not self.game.game_over:
                self.game.screen_shake = max(16, self.game.screen_shake)
        if self.collisions["down"]:
            self.air_time = 0
            self.jumps = 1

        self.wall_slide = False
        # 左右碰撞且在空中
        if self.hit == 0:
            if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
                self.wall_slide = True
                self.air_time = 20
                self.velocity[1] = min(self.velocity[1], 0.5)
                if self.collisions['right']:
                    self.flip = False
                else:
                    self.flip = True
                self.set_action("wall_slide")
            if not self.wall_slide:
                if self.air_time > 4:
                    self.set_action("jump")
                elif movement[0] != 0:
                    self.set_action("run")
                else:
                    self.set_action("idle")
        else:
            self.set_action('hit')
            if self.animation.done:
                self.hit = 0
            if self.hit > 0:
                self.velocity[0] = 2.5
            elif self.hit < 0:
                self.velocity[0] = -2.5
        # 产生开始和结束的爆炸粒子效果
        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * 2 * math.pi
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(
                    Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        if abs(self.dashing) > 50:
            # 用除法取方向然后乘8
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            # 当冲刺前十帧播放完迅速把速度减下来
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(
                Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)

        # 因为写的蹬墙跳代码给了一个x速度，如果不写一个空气阻力的代码，会一直往那边移动
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def jump(self):
        if self.wall_slide:

            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif (not self.flip) and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True

        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            # 确保跳跃就是jump动画，否则要过4帧才是jump
            self.air_time = 5
            return True

    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
        else:
            pass

    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60
