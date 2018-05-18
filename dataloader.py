from queue import Queue
from threading import Thread

import numpy as np
from scipy import misc
from scipy.ndimage import imread
import scipy
import conf
from os import listdir
from os.path import isfile, join
import os
from time import time

class DataLoader():
    def __init__(self):

        self.caption_path = join(conf.ENCODER_TRAINING_PATH, 'captions')
        self.image_path = join(conf.ENCODER_TRAINING_PATH, 'images')
        self._load_meta_data()
        self.sh_idx = [] # shuffled index,
        self.data = None


    def _load_meta_data(self):

        d = {}

        for class_str in listdir(self.caption_path):
            if 'class' not in class_str: continue # garbage
            c = int(class_str.split('_')[1])

            text_path = join(self.caption_path, class_str)

            images = []
            for txt_file in listdir(text_path):
                if 'image' not in txt_file: continue  # garbage
                if txt_file.endswith(".txt"):
                    image_name = txt_file.split('.')[0]
                    images.append(image_name)
            d[c] = images

        self.meta_data = d

    def process_data(self):
        t0 = time()
        print('pre processing data')
        # worker thread
        def work(q: Queue, ret_q: Queue):
            while not q.empty():
                cls, img_name = q.get()
                if q.qsize() % 100 == 0: print('remaining', q.qsize())

                img_fpath = join(self.image_path, img_name + '.jpg')
                im = imread(img_fpath, mode='RGB') # First time for batch
                resized_images = crop_and_flip(im)

                # Load captions for image
                # TODO what to do with multiple captions per text?
                cls_dir = 'class_%05d' % cls
                txt_fpath = join(self.caption_path, cls_dir, img_name + '.txt')
                with open(txt_fpath, 'r') as txt_file:
                    lines = txt_file.readlines()
                    lines = [l.rstrip() for l in lines]
                txt = list(map(self._onehot_encode_text, lines))

                for img in resized_images:
                    for caption in txt:
                        ret_q.put((cls, img, caption))
                q.task_done()

        threads = []
        data = {}
        in_q = Queue()
        out_q = Queue()

        # Fill worker queue
        for i, (cls, image_names) in enumerate(self.meta_data.items()):

            for img_name in image_names:
                in_q.put((cls, img_name))

            #if i > conf.BATCH_SIZE+1: break # TODO Delete me

        # Spawn threads
        for i in range(conf.PRE_PROCESSING_THREADS):
            worker = Thread(target=work, args=(in_q, out_q))
            threads.append(worker)
            worker.start()

        # Blocking for worker threads
        in_q.join()
        while not out_q.empty():
            cls, image, captions = out_q.get()
            if cls not in data:
                data[cls] = []
            data[cls].append((image, captions))

        print('pre processing complete, time:', time() - t0)

        self.data = data

    def _shuffle_idx(self):
        """
        Adds more shuffled index into queue
        :return:
        """
        idx = np.array(list(self.data.keys()))
        np.random.shuffle(idx)
        self.sh_idx += idx.tolist()

    def _onehot_encode_text(self, txt):
        axis1 = conf.ALPHA_SIZE
        axis0 = conf.CHAR_DEPTH
        oh = np.zeros((axis0, axis1))
        for i, c in enumerate(txt):
            if i >= conf.CHAR_DEPTH:
                break # Truncate long text
            char_i = conf.ALPHABET.find(c)
            oh[i, char_i] = 1

        # l = list(map(self._c2i, txt))
        # l += [0] * (conf.CHAR_DEPTH - len(l)) # padding
        return oh

    def _c2i(self, c: str):
        return conf.ALPHABET.find(c)

    def next_batch(self): #TODO modify to comply with TF pipeline?
        '''
        Get batches of data
        :return:
        '''
        if self.data is None:
            raise Exception('Data not preprocessed! Did you call .process_data() beforehand? ')

        batch = []
        classes = []
        images = []
        captions = []
        if len(self.sh_idx) < conf.BATCH_SIZE:
            self._shuffle_idx()

        for i in range(conf.BATCH_SIZE):
            cls = self.sh_idx.pop()
            d = self.data[cls]
            sample_idx = np.random.randint(0, len(d))
            img, caption = self.data[cls][sample_idx]

            #append
            images.append(img)
            captions.append(caption)
            classes.append(cls)


        return (classes, images, captions)



def load_and_process_image_batch(): # TODO add batch support
    """
    Loads images and preprocess them into 3 channel images
    :param bathces:
    :return: batches of images tensor. [Batchsize, width, height, 3]
    """

    images = []

    im = imread('assets/training/4.png', mode='RGB') # First time for batch
    resized_im = resize_image_with_smallest_side(im)

    images.append(resized_im)

    im = imread('assets/training/4.png', mode='RGB') # First time for batch
    resized_im = resize_image_with_smallest_side(im)
    images.append(resized_im)
    npim = np.array(images)
    return npim

def resize_image_with_smallest_side(image, small_size=224):
    """
    Resize single image array with smallest side = small_size and
    keep the original aspect ratio.

    Author: Qian Ge <geqian1001@gmail.com>

    Args:
        image (np.array): 2-D image of shape
            [height, width] or 3-D image of shape
            [height, width, channels] or 4-D of shape
            [1, height, width, channels].
        small_size (int): A 1-D int. The smallest side of resize image.
    """
    im_shape = image.shape
    shape_dim = len(im_shape)
    assert shape_dim <= 4 and shape_dim >= 2,\
        'Wrong format of image!Shape is {}'.format(im_shape)

    if shape_dim == 4:
        image = np.squeeze(image, axis=0)
        height = float(im_shape[1])
        width = float(im_shape[2])
    else:
        height = float(im_shape[0])
        width = float(im_shape[1])

    if height <= width:
        new_height = int(small_size)
        new_width = int(new_height/height * width)
    else:
        new_width = int(small_size)
        new_height = int(new_width/width * height)

    if shape_dim == 2:
        im = misc.imresize(image, (new_height, new_width))
    elif shape_dim == 3:
        im = misc.imresize(image, (new_height, new_width, image.shape[2]))
    else:
        im = misc.imresize(image, (new_height, new_width, im_shape[3]))
        im = np.expand_dims(im, axis=0)

    return im

def crop_and_flip(image,os=224):

    """
    :param image: An image on tensor form, h x w x 3
    :param size: output
    :return:
    """

    h, w, c = image.shape

    scales = [256]

    images = []
    for l in scales:

        im=resize_image_with_smallest_side(image,l)
        h, w, c = im.shape

        im_upperleft = im[:os, :os, :]
        images.append(im_upperleft)
        images.append(np.fliplr(im_upperleft))

        im_upperright = im[:os, w-os:, :]
        images.append(im_upperright)
        images.append(np.fliplr(im_upperright))

        im_lowerleft = im[h-os:, :os, :]
        images.append(im_lowerleft)
        images.append(np.fliplr(im_lowerleft))

        im_lowerright = im[h-os:, w-os:, :]
        images.append(im_lowerright)
        images.append(np.fliplr(im_lowerright))

        im_middle = im[(h - os) // 2:(h + os) // 2, (w - os) // 2:(w + os) // 2, :]
        images.append(im_middle)
        images.append(np.fliplr(im_middle))

    #shuffle(images)

    return images