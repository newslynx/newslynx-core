"""
All things related to creating embeds. Just videos for now.
In all cases we're assuming that the url has been canonicalized
already.
"""

from newslynx.lib import url
from newslynx.lib.network import get_json

VIDEO_EMBED_FORMAT = '<iframe src="{src}" width="{width}" height="{height}" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen> </iframe>'


def youtube(u, **kw):
    """
    Given a canonical youtube url, generate it's embed code.
    """
    kw.setdefault('width', 320)
    kw.setdefault('height', 160)

    id = url.get_query_param(u, 'v')
    if not id:
        return None

    kw['src'] = "//www.youtube.com/embed/" + id
    return VIDEO_EMBED_FORMAT.format(**kw)


def vimeo(u, **kw):
    """
    Given a canonical vimeo url, generate it's embed code.
    """
    kw.setdefault('width', 320)
    kw.setdefault('height', 160)

    id = u.split('/')[-1]
    kw['src'] = "//player.vimeo.com/video/" + id
    return VIDEO_EMBED_FORMAT.format(**kw)


def dailymotion(u, **kw):
    """
    Given a canonical dailymotion url, generate it's embed code.
    """
    kw.setdefault('width', 320)
    kw.setdefault('height', 160)

    try:
        id = u.split('/')[-1].split('_')[0].strip()
    except IndexError:
        return None
    kw['src'] = '//www.dailymotion.com/embed/video/' + id
    return VIDEO_EMBED_FORMAT.format(**kw)


def twitter(u, **kw):
    """
    Given a canonical twitter status url, generate it's embed code.
    """
    endpoint = 'https://api.twitter.com/1/statuses/oembed.json'
    params = {
        'url': u,
        'hide_media': kw.get('hide_media', True)
    }
    embed_data = get_json(endpoint, **params)
    return embed_data['html']
