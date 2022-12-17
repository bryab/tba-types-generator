import urllib.request
import urllib.error
import os
import re
import json

cache_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "doc-parser-cache")
if not os.path.isdir(cache_dir):
    os.mkdir(cache_dir)


def get_url(url):
    a = url.split("/")
    cache_name = "_".join(a[-5:])
    old_cache_filename = cache_filename = os.path.join(cache_dir, "{}.html".format(cache_name))
    if os.path.isfile(old_cache_filename):
        cache_filename = old_cache_filename
    else:
        cache_filename = os.path.join(cache_dir, cache_name)
    if os.path.isfile(cache_filename):
        with open(cache_filename, "r") as f:
            return f.read()
    print("Requesting: {}".format(url))
    try:
        html = urllib.request.urlopen(url).read().decode()
    except urllib.error.HTTPError:
        return None
    with open(cache_filename, "w") as f:
        f.write(html)
    return html
