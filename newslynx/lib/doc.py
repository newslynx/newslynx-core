"""
All things related to document conversion via pandoc
"""
import os
from traceback import format_exc
from tempfile import NamedTemporaryFile

from flask import Response

from newslynx.lib.pkg.pandoc import Document
from newslynx.exc import RequestError
from newslynx.core import settings

_d = Document()
FILE_FORMATS = ['pdf', 'odt']
INPUT_FORMATS = list(_d.INPUT_FORMATS)
OUTPUT_FORMATS = list(_d.OUTPUT_FORMATS)


# TODO: fill this in.
FORMAT_TO_MIMETYPE = {
    'native': '',
    'html': 'text/html',
    'pdf': 'application/pdf',
    'html+lhs': '',
    's5': '',
    'slidy': '',
    'docbook': '',
    'opendocument': 'application/vnd.oasis.opendocument.text',
    'odt': 'application/vnd.oasis.opendocument.text',
    'latex': '',
    'latex+lhs': '',
    'context': '',
    'texinfo': '',
    'man': '',
    'markdown': 'text/x-markdown; charset=UTF-8',
    'markdown+lhs': 'text/x-markdown; charset=UTF-8',
    'plain': 'text/plain',
    'rst': '',
    'rst+lhs': '',
    'mediawiki': '',
    'rtf': 'text/rtf',
    'markdown_github': 'text/x-markdown; charset=UTF-8'
}


def convert_response(contents, from_, to_):
    """
    Convert a document and return a properly formatted response.
    """
    contents = convert(contents, from_, to_)
    resp = Response(contents)
    resp.headers['Content-Type'] = FORMAT_TO_MIMETYPE.get(to_, 'text/plain')
    return resp


def convert(contents, from_, to_):
    """
    Full interface to pandoc.
    """
    if not os.path.exists(settings.PANDOC_PATH):
        raise RequestError(
            'Pandoc is not installed or `pandoc_path` is improperly configured.')

    # accept long/shorthand
    if from_ == "md":
        from_ = "markdown"

    if to_ == "md":
        to_ = "markdown"

    if to_ == "opendocument":
        to_ = "odt"

    # for mirroring base format.
    if from_ == to_:
        return contents

    d = Document()
    if from_ not in INPUT_FORMATS:
        raise Exception('{} is not an avaliable input format.'.format(from_))
    setattr(d, from_, contents)

    if to_ not in OUTPUT_FORMATS and to_ not in FILE_FORMATS:
        raise Exception('{} is not an available output format.'.format(to_))

    # convert files
    if to_ in FILE_FORMATS:
        contents = None
        contents = convert_file(d, from_, to_)
        if not contents:
            if to_ == "pdf":
                raise Exception('Are you sure you have pdflatex installed?')
            else:
                raise Exception('File conversion failed.')
        return contents

    # convert via pandoc
    contents = None
    try:
        contents = getattr(d, to_)
        if not contents:
            raise Exception('No output from pandoc.')
        return contents
    except Exception as e:
        raise Exception(
            'I/O conversion failed: {}'
            .format(e.message))


def convert_file(d, from_, to_):
    """
    Convert via tempfile. Robust to errors + tempfile leakage.
    """
    tempfile = NamedTemporaryFile(mode="wb",
                                  suffix=".{}".format(to_), delete=False)

    try:
        output_file = d.to_file(tempfile.name)
    except Exception as e:
        try:
            os.remove(tempfile.name)
        except OSError:
            pass
        raise Exception('Conversion failed: {}'.format(e.message))

    if not output_file:
        try:
            os.remove(tempfile.name)
        except OSError:
            pass
        raise Exception('Conversion failed: No output from pandoc')

    contents = open(output_file).read()
    try:
        os.remove(output_file)
    except OSError:
        pass
    return contents
