import unittest

from newslynx.lib import url
from newslynx.logs import log


class TestURL(unittest.TestCase):

    def test_reconcile_embed(self):
        u = '//cdn.embedly.com/'
        assert(url.reconcile_embed(u).startswith('http://'))

    def test_redirect_back(self):
        source = 'https://www.revealnews.org/article/a-brief-history-of-the-modern-strawberry/'
        u = '//cdn.embedly.com/widgets/media.html?url=http%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DfPxUIz5GHAE&src=http%3A%2F%2Fwww.youtube.com%2Fembed%2FfPxUIz5GHAE&type=text%2Fhtml&key=1b74e47c9db441f8a998fb6138abca72&schema=youtube'
        out = url.redirect_back(u, source)
        assert(out == 'http://www.youtube.com/watch?v=fPxUIz5GHAE')

    def test_prepare_with_redirect_back(self):
        source = 'https://www.revealnews.org/article/a-brief-history-of-the-modern-strawberry/'
        u = '//cdn.embedly.com/widgets/media.html?url=http%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DfPxUIz5GHAE&src=http%3A%2F%2Fwww.youtube.com%2Fembed%2FfPxUIz5GHAE&type=text%2Fhtml&key=1b74e47c9db441f8a998fb6138abca72&schema=youtube'
        out = url.prepare(u, source)
        assert(out == 'http://www.youtube.com/watch?v=fPxUIz5GHAE')

    def test_from_html_with_embed_redirect(self):
        htmlstring = """
            <div id="content_body" itemprop="articleBody">
            <div id="dropped_media_355_84" class="mceNonEditable embedded_content embedded_full_width basic-caption">
            <figure>
            <div class="flex-video"><iframe class="embedly-embed" src="//cdn.embedly.com/widgets/media.html?url=http%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DfPxUIz5GHAE&amp;src=http%3A%2F%2Fwww.youtube.com%2Fembed%2FfPxUIz5GHAE&amp;type=text%2Fhtml&amp;key=1b74e47c9db441f8a998fb6138abca72&amp;schema=youtube" width="854" height="480" frameborder="0" scrolling="no" allowfullscreen="allowfullscreen"></iframe></div>
            </figure>
            </div>
            <p>From cereal to ice cream to cocktails, it seems that strawberries are served with&nbsp;just about&nbsp;everything. But it wasn't always&nbsp;this&nbsp;way. Today, Americans eat four times as many strawberries as they did 40 years ago. This short&nbsp;stop-motion&nbsp;animation explains how clever advertising tactics and certain pesticides helped make the juicy red fruit cheaply and widely available. There are, however, hidden costs to using these chemicals.</p>
            <div class="edit-credits">
                <p>Director and Producer:&nbsp;Ariane Wu<br>
            </div>
            </div>
        """
        source = 'https://www.revealnews.org/article/a-brief-history-of-the-modern-strawberry/'
        out = url.from_html(htmlstring, source=source)
        assert('http://www.youtube.com/watch?v=fPxUIz5GHAE' in out)

    def test_from_html_with_iframe_src(self):
        htmlstring = """
            <div id="content_body" itemprop="articleBody">
            <div id="dropped_media_355_84" class="mceNonEditable embedded_content embedded_full_width basic-caption">
            <figure>
            <div class="flex-video"><iframe class="embedly-embed" src="http://www.youtube.com/watch?v=fPxUIz5GHAE" width="854" height="480" frameborder="0" scrolling="no" allowfullscreen="allowfullscreen"></iframe></div>
            </figure>
            </div>
            </div>
            </div>
        """
        source = 'https://www.revealnews.org/article/a-brief-history-of-the-modern-strawberry/'
        out = url.from_html(htmlstring, source=source)
        assert('http://www.youtube.com/watch?v=fPxUIz5GHAE' in out)

    def test_from_string(self):
        string = "fasfdaf ewrawekljf jslkfdjas https://www.revealnews.org/article/a-brief-history-of-the-modern-strawberry/ fjasl;fkdjasl;kfdjasf"
        out = url.from_string(string, dedupe=False)
        assert(
            "https://www.revealnews.org/article/a-brief-history-of-the-modern-strawberry/" in out)
        assert(len(out) == 1)

    def test_from_string_short_url(self):
        string = "fasf bit.ly/342fdasfa fdjasf http://bit.ly/3fs24dsfa sub.bit.ly/342fs4dsfa! foo.bit.ly/342fs4dsfa"
        out = url.from_string(string)
        assert(
            'bit.ly/342fdasfa' in out and 'http://bit.ly/3fs24dsfa' in out and 'sub.bit.ly/342fs4dsfa' in out and 'foo.bit.ly/342fs4dsfa' in out)

    def test_domain_rm_www(self):
        u = 'http://www.nytimes.com'
        assert(url.get_domain(u) == 'nytimes.com')

    def test_from_any_html(self):
        u = 'fds;lfjdlskafjsldak <a href="http://www.nytimes.com"></a> asdlifjkasdlkfj '
        assert('http://www.nytimes.com' in url.from_any(u))

    def test_get_simple_domain(self):
        case = 'http://www.nytimes.com/2014/06/06/business/gm-ignition-switch-internal-recall-investigation-report.html?hp&_r=0'
        assert(url.get_simple_domain(case) == 'nytimes')

    def test_is_short_url(self):
        cases = [
            '1.usa.gov/1kEeAcb',
            'bit.ly/1kzIQWw',
            'http://1.usa.gov/1kEeAcb'
        ]
        for c in cases:
            assert(url.is_shortened(c))

    def test_unshorten_url(self):

        cases = [
            ('http://nyti.ms/1oxYm3e',
             'http://www.nytimes.com/video/movies/100000002920951/anatomy-8216the-fault-in-our-stars8217.html'),
            ('nyti.ms/1oxYm3e',
             'http://www.nytimes.com/video/movies/100000002920951/anatomy-8216the-fault-in-our-stars8217.html'),
            ('http://bit.ly/1kzIQWw',
             'http://www.fromscratchradio.com/show/marc-dacosta'),
            ('bit.ly/aaaaaa', 'http://bit.ly/aaaaaa'),
            ('http://ow.ly/i/5OTms', 'http://ow.ly/i/5OTms'),
            # ('http://j.mp/1jBOKo1', 'http://earthfix.info/portables')
        ]
        for c in cases:
            test, truth = c
            try:
                test = url.prepare(test)
                assert(test == truth)
            except AssertionError:
                print "failed on %s" % test
                raise


if __name__ == '__main__':
    unittest.main()
