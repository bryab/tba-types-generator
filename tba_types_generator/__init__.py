import os
import json
import typing
from .typescript_builder import write_ts_from_class
import subprocess
from .parser.tba_parser import get_classes as get_core_classes
from .parser.tba_extended_parser import get_classes as get_extended_classes
import logging

logger = logging.getLogger(__name__)
SKIP_CLASSES = ['QObject', 'BAPP_SpecialFolders', 'QScriptable', 'Labeled',
                'QLineEdit', 'SCRIPT_QSWidget', 'QProcess', 'SCR_BaseInterface']


def _load_extra_ts_files():
    override_dir = './override'
    data = {}
    for filename in os.listdir(override_dir):
        root, ext = os.path.splitext(filename)
        if ext == '.ts':
            filepath = os.path.join(override_dir, filename)
            with open(filepath, 'r') as f:
                data[root] = f.read()
    return data


def prettify(filename):
    logger.info(f"Prettifying {filename}")
    subprocess.call(['prettier', '--write', filename])


def _generate_ts_from_data(host: str, version_num: str, all_classes: typing.Iterator[dict]):
    extra_file_data = _load_extra_ts_files()

    ts_dir = os.path.join(os.path.expanduser(
        '~/dev/harmony/tba-types/'), host, str(version_num))
    if not os.path.isdir(ts_dir):
        os.makedirs(ts_dir)
    ts_filename = os.path.join(ts_dir, 'index.d.ts')
    logger.info(f"Writing to {ts_filename}")
    with open(ts_filename, 'w') as ts_file:
        ts_file.write(extra_file_data['preamble'])
        if host == 'harmony' and version_num >= 16:
            logger.debug(f"Writing Harmony addons for >= 16")
            ts_file.write('\n')
            ts_file.write(extra_file_data['preamble_harmony16up'])
        if host == 'storyboardpro':
            logger.debug(f"Writing addons for Storyboard Pro")
            ts_file.write('\n')
            ts_file.write(extra_file_data['preamble_sbpro'])
        ts_file.write('\n\n\n')

        for class_data in all_classes:
            if class_data['name'] in SKIP_CLASSES:
                continue
            logger.debug(f"Writing class: {class_data['name']}")
            write_ts_from_class(class_data, ts_file)

        ts_file.write('\n\n\n')
        if host == 'harmony':
            logger.debug("Writing harmony-specific add-ons")
            ts_file.write(extra_file_data['harmony_post'])

    prettify(ts_filename)


# def _iter_class_jsons(version):
#     export_dir = os.path.join('./export/', version)
#     for filename in sorted(os.listdir(export_dir)):
#         root, ext = os.path.splitext(filename)
#         if not ext == '.json':
#             continue
#         if root.startswith('.'):
#             continue
#         filepath = os.path.join(export_dir, filename)
#         logger.debug(filepath)
#         with open(filepath, 'rb') as f:
#             yield json.load(f)

def get_all_classes(host, version_num):
    yield from get_core_classes(host, version_num)
    if host == "harmony":
        yield from get_extended_classes(version_num)


def generate(host, version_num):
    logger.info(f"Generating Typescript for {host}:{version_num}")
    _generate_ts_from_data(
        host, version_num, get_all_classes(host, version_num))

# def generate_from_json():
#     versions = ["harmony15","harmony16","harmony17","harmony20","harmony21","harmony22","sbpro7","sbpro20","sbpro22"]

#     for version in versions:
#         if 'harmony' in version:
#             host = 'harmony'
#         if 'sbpro' in version:
#             host = 'storyboardpro'
#         version_num = re.search(r"(\d+)", version).group(1)

#         _generate_ts_from_data(host, version_num, _iter_class_jsons(version))
#         sys.exit(1)

# if __name__ == "__main__":
#     _generate_from_html()
