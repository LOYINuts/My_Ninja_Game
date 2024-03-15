import sys

import pygame

pygame.init()
# 界面大小
WIDTH = 640
HEIGHT = 480
# 帧数
FPS = 60

pygame.display.set_caption("忍者")
# 设置窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
# 限制程序为60FPS
clock = pygame.time.Clock()

while True:
    # 处理事件
    for event in pygame.event.get():
        # 按窗口上的X
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # 更新窗口上的东西，把东西画出来
    pygame.display.update()
    clock.tick(FPS)
