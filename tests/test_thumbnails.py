import unittest

from newslynx.lib import image
from newslynx.logs import log

jpeg_url = 'https://scontent-iad3-1.xx.fbcdn.net/hphotos-xtf1/t31.0-8/11538144_10102217138613259_5735598036491513465_o.jpg'
gif_url = 'http://www.reactiongifs.com/r/psycrs.gif'
png_url = "http://vignette3.wikia.nocookie.net/fantendo/images/e/eb/Mario_SM3DW.png/revision/latest?cb=20120122014152"


class TestThumbnail(unittest.TestCase):

    def test_jpeg(self):
        b64 = image.b64_thumbnail_from_url(jpeg_url)
        data = b64.split(';')[0]
        assert('jpg' in data or 'jpeg' in data)

    def test_gif(self):
        b64 = image.b64_thumbnail_from_url(gif_url)
        data = b64.split(';')[0]
        assert('gif' in data)

    def test_png_mimetype(self):
        b64 = image.b64_thumbnail_from_url(png_url)
        data = b64.split(';')[0]
        assert('png' in data)


if __name__ == '__main__':
    unittest.main()
