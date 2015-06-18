import cStringIO
import base64
import mimetypes

import requests
from PIL import Image, ImageOps

from newslynx.lib import network
from newslynx.lib.url import get_filetype
from newslynx import settings


def b64_thumbnail_from_url(img_url, **kw):
    """
    Download an image and create a base64 thumbnail.
    """

    size = kw.get('size', settings.THUMBNAIL_SIZE)
    default_fmt = kw.get('format', settings.THUMBNAIL_DEFAULT_FORMAT)
    fmt = None

    # override fmt with default fmt
    fmt = get_filetype(img_url)

    # get the image
    data, mime_fmt = get_url(img_url)
    if not data:
        return None

    # override fmt with format from mimetype
    if not fmt:
        fmt = mime_fmt

    # if we still don't have a format, fall back on default
    if not fmt:
        fmt = default_fmt

    # PIL doesn't like JPG
    if fmt.lower() == 'jpg':
        fmt = "jpeg"

    # turn into Pillow object
    file = cStringIO.StringIO(data)
    image = Image.open(file)

    # fit to a thumbnail
    thumb = ImageOps.fit(image, size, Image.ANTIALIAS)

    # convert to base64
    img_buffer = cStringIO.StringIO()
    thumb.save(img_buffer, format=fmt)
    img_str = base64.b64encode(img_buffer.getvalue())

    # format + return
    return "data:image/{};base64,{}".format(fmt, img_str)


def get_url(img_url):
    fmt = None
    r = requests.get(img_url, **network.get_request_kwargs())
    mimetype = r.headers.get('content-type', None)
    if mimetype:
        fmt = extension_from_mimetype(mimetype)
    return r.content, fmt


def extension_from_mimetype(mimetype):
    """
    Guess a image's extension from it's mimetype.
    """
    ext = mimetypes.guess_extension(mimetype)
    if ext.startswith('.'):
        ext = ext[1:]
    # this is a bug in mimetypes
    if ext == 'jpe':
        return 'jpeg'
    return ext
