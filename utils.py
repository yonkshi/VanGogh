import numpy as np
from scipy import misc
from scipy.ndimage import imread
from random import shuffle


def crop_and_flip(image):

    """

    :param image: An image on tensor form, h x w x 3
    :param size: output
    :return:
    """

    h, w, c = image.shape

    scales = (256, 384, 480)

    images = []
    for l in scales:
        im_upperleft = image[:l, :l, :]
        images.append(im_upperleft)
        images.append(np.fliplr(im_upperleft))

        im_upperright = image[:l, w-l:, :]
        images.append(im_upperright)
        images.append(np.fliplr(im_lowerright))

        im_lowerleft = image[h-l:, :l, :]
        images.append(im_lowerleft)
        images.append(np.fliplr(im_lowerleft))

        im_lowerright = image[h-l:, w-l:, :]
        images.append(im_lowerright)
        images.append(np.flilr(im_lowerright))

        im_middle = image[(h-l)/2:(h+l)/2, (w-l)/2:(w+l)/2, :]
        images.append(im_middle)
        images.append(np.fliplr(im_middle))

    shuffle(images)

    return images


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


image = imread('implementation/result.png', mode='RGB')
a = 0