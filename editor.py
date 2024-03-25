import sys
from tkinter import messagebox

import pygame
from scripts.utils import load_images
from scripts.tilemap import TileMap

RENDER_SCALE = 2.0

# 界面大小
WIDTH = 1280
HEIGHT = 960
FPS = 60


class Editor:
    def __init__(self, width, height, fps):
        pygame.init()
        self.WIDTH = width
        self.HEIGHT = height
        # 帧数
        self.FPS = fps
        pygame.display.set_caption("编辑器")
        # 设置窗口
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        # Surface功能创建一个空的图片
        self.displayer = pygame.Surface((640, 480))
        self.clock = pygame.time.Clock()
        self.assets = {
            'decor': load_images("tiles/decor"),
            'grass': load_images("tiles/grass"),
            'large_decor': load_images("tiles/large_decor"),
            'stone': load_images("tiles/stone"),
            'spawners': load_images("tiles/spawners")
        }
        # 移动相机，上下左右
        self.movement = [False, False, False, False]

        self.tilemap = TileMap(self, tile_size=16)

        try:
            self.tilemap.load('map.json')
            messagebox.showinfo(title="提示", message="成功读取map.json")
        except FileNotFoundError:
            messagebox.showinfo(title="提示", message="未找到map.json，已重新创建(map.json应该放在与执行文件同目录下)")
            pass

        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        # 使用的是哪一组，草，石头还是什么
        self.tile_group = 0
        # 这一组的哪一张图片
        self.tile_variant = 0
        # 左键为1，右键为3，中键按下为2，滚轮向上为4，向下为5
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True

    def run(self):
        while True:
            self.displayer.fill((0, 0, 0))
            # 左右，乘2为了移动的更快
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            # 上下
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.displayer, offset=render_scroll)

            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)

            mpos = pygame.mouse.get_pos()
            # 因为实际上都是放大了两倍，所以实际的坐标要转换一下
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                        int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
            if self.ongrid:
                self.displayer.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                                                       tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.displayer.blit(current_tile_img, mpos)

            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {
                    'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': tile_pos}

            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                # 特殊删除off_grid_tile
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1],
                                         tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)

            self.displayer.blit(current_tile_img, (5, 5))

            for event in pygame.event.get():
                # 按窗口上的X
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append(
                                {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant,
                                 'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(
                                self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(
                                self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0

                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:
                        self.tilemap.auto_tile()
                    if event.key == pygame.K_o:
                        self.tilemap.save('map.json')
                        msg = messagebox.showinfo(title="提示", message="保存成功")
                        print(msg)
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        self.movement[1] = False
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False

            self.screen.blit(pygame.transform.scale(self.displayer, self.screen.get_size()), (0, 0))
            # 更新窗口上的东西，把东西画出来
            pygame.display.update()
            self.clock.tick(FPS)


def main():
    editor = Editor(WIDTH, HEIGHT, FPS)
    editor.run()


if __name__ == "__main__":
    main()
