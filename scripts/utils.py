import os

import pygame

BASE_IMG_PATH = 'assets/images/'


def load_musics(path):
    music_list = []
    for music_name in sorted(os.listdir(path)):
        music_list.append(path + music_name)
    return music_list


def load_image(path):
    # convert能让图片更好粘贴，提高性能
    """

    :param path: 文件路径
    :return: 图片
    """
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img


def load_images(path):
    images = []
    # listdir会返回那个目录所有的文件
    # Windows系统自动排序文件为字典序，但是LINUX可能不同，所以使用sorted来排个序
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name))

    return images


class Animation:
    def __init__(self, images: list, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.frame = 0
        # 如果loop不为True就要done来判断动画是否放完
        self.done = False

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            # 这里不同因为这是要取特定的某一个动画，数组，而上面取模会重置为0，所以不用管
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        return self.images[int(self.frame / self.img_duration)]
