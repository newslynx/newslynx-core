"""
All things related to serialization.
"""

import json
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from inspect import isgenerator
from collections import Counter
import pickle
import gzip
import zlib
import cStringIO
from collections import OrderedDict

import yaml
from flask import Response, request

from newslynx.lib.search import SearchString
from newslynx.lib.regex import RE_TYPE
from newslynx.lib.pkg.crontab import CronTab


def str_to_gz(s):
    """
    string > gzip
    """
    out = cStringIO.StringIO()
    with gzip.GzipFile(fileobj=out, mode="w") as f:
        f.write(s)
    return out.getvalue()


def gz_to_str(s):
    """
    gzip > string
    """
    fileobj = cStringIO.StringIO(s)
    with gzip.GzipFile(fileobj=fileobj, mode="r") as f:
        return f.read()


def json_to_obj(s):
    """
    jsonstring > obj
    """

    return json.loads(s)


def obj_to_json(obj):
    """
    obj > jsonstring
    """
    return jsonify(obj, is_req=False)


def jsongz_to_obj(s):
    """
    json.gz > obj
    """

    return json_to_obj(gz_to_str(s))


def obj_to_jsongz(obj):
    """
    obj > json.gz
    """
    return str_to_gz(obj_to_json(obj))


def pickle_to_obj(s):
    """
    pickle > obj
    """
    return pickle.loads(s)


def obj_to_pickle(obj):
    """
    obj > pickle
    """
    return pickle.dumps(obj)


def picklegz_to_obj(s):
    """
    pickle.gz > obj
    """
    return pickle_to_obj(gz_to_str(s))


def obj_to_picklegz(obj):
    """
    obj > pickle.gz
    """
    return str_to_gz(obj_to_pickle(obj))


def str_to_zip(s):
    """
    string > zip
    """
    return zlib.compress(s)


def zip_to_str(s):
    """
    zip > string
    """
    return zlib.decompress(s)


def obj_to_yaml(obj):
    """
    obj > yamlstring
    """
    return yaml.dumps(obj)


def yaml_to_obj(s):
    """
    yamlstring > obj
    """
    return yaml.safe_load(s)


def yaml_stream_to_obj(stream, Loader=yaml.SafeLoader, object_pairs_hook=OrderedDict):
    """
    Load a yaml file in order.
    """
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return yaml.load(stream, OrderedLoader)


class JSONEncoder(json.JSONEncoder):

    """ This encoder will serialize all entities that have a to_dict
    method by calling that method and serializing the result.
    Taken from: https://github.com/pudo/apikit
    """

    def __init__(self, refs=False):
        self.refs = refs
        super(JSONEncoder, self).__init__()

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, set):
            return list(obj)
        if isgenerator(obj):
            return list(obj)
        if isinstance(obj, Counter):
            return dict(obj)
        if isinstance(obj, SearchString):
            return obj.raw
        if isinstance(obj, RE_TYPE):
            return obj.pattern
        if isinstance(obj, CronTab):
            return obj.raw
        if self.refs and hasattr(obj, 'to_ref'):
            return obj.to_ref()
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        if hasattr(obj, 'to_json'):
            return obj.to_json()
        try:
            from sqlalchemy.orm import Query
            from sqlalchemy.ext.associationproxy import _AssociationList
            if isinstance(obj, Query) or isinstance(obj, _AssociationList):
                return [r for r in obj]
        except ImportError:
            pass

        try:
            from bson.objectid import ObjectId
            if isinstance(obj, ObjectId):
                return str(obj)
        except ImportError:
            pass
        return json.JSONEncoder.default(self, obj)


def jsonify(obj, status=200, headers=None, refs=False, encoder=JSONEncoder, is_req=True):
    """ Custom JSONificaton to support obj.to_dict protocol.
        Taken from: https://github.com/pudo/apikit"""

    if encoder is JSONEncoder:
        data = encoder(refs=refs).encode(obj)
    else:
        data = encoder().encode(obj)

    if not is_req:
        return data

    else:
        # accept callback
        if 'callback' in request.args:
            cb = request.args.get('callback')
            data = '%s && %s(%s)' % (cb, cb, data)

        return Response(data, headers=headers,
                        status=status,
                        mimetype='application/json')
