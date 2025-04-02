import os
import json5
import typing
from pathlib import Path

from .typescript_builder import write_ts_from_class, write_ts_from_interface
import subprocess
from .parser.tba_parser import get_classes as get_core_classes
from .parser.tba_extended_parser import get_classes as get_extended_classes
from .parser.tba_extended_parser import get_globals as get_extended_globals
import logging

logger = logging.getLogger(__name__)
SKIP_CLASSES = [
    "QObject",
    "BAPP_SpecialFolders",
    "QScriptable",
    "Labeled",
    "QLineEdit",
    "SCRIPT_QSWidget",
    "QProcess",
    "SCR_BaseInterface",
]


DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "dist" / "tba-types"


def _get_output_dir():
    return Path(os.environ.get("TBA_TYPES_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))


def _load_extra_ts_files():
    override_dir = "./override"
    data = {}
    for filename in os.listdir(override_dir):
        root, ext = os.path.splitext(filename)
        if ext == ".ts":
            filepath = os.path.join(override_dir, filename)
            with open(filepath, "r") as f:
                data[root] = f.read()
    return data


def prettify(filename):
    import sys

    logger.info(f"Prettifying {filename}")
    if sys.platform == "win32":
        npx_bin = "C:\\Program Files\\nodejs\\npx.cmd"
    else:
        npx_bin = "npx"
    subprocess.call(
        [
            npx_bin,
            "prettier",
            "--object-wrap",
            "collapse",
            "--trailing-comma",
            "none",
            "--write",
            filename,
        ]
    )


def prettify_alt(filename):
    import jsbeautifier

    logger.info(f"Prettifying {filename}")
    with open(filename, "r") as f:
        old_js = f.read()
    new_js = jsbeautifier.beautify(old_js)
    with open(filename, "w") as f:
        f.write(new_js)


def _generate_ts_from_data(
    host: str,
    version_num: str,
    all_classes: typing.Iterator[dict],
    all_globals: typing.Iterator[dict],
):
    extra_file_data = _load_extra_ts_files()

    ts_dir = _get_output_dir() / host / str(version_num)
    ts_dir.mkdir(parents=True, exist_ok=True)
    ts_filename = os.path.join(ts_dir, "index.d.ts")
    logger.info(f"Writing to {ts_filename}")
    with open(ts_filename, "w") as ts_file:
        ts_file.write(extra_file_data["preamble"])
        if host == "harmony":
            if version_num >= 16:
                logger.debug(f"Writing Harmony addons for >= 16")
                ts_file.write("\n")
                ts_file.write(extra_file_data["preamble_harmony16up"])
            if version_num >= 24:
                logger.debug(f"Writing Harmony addons for >= 24")
                ts_file.write("\n")
                ts_file.write(extra_file_data["preamble_harmony24up"])
        if host == "storyboardpro":
            logger.debug(f"Writing addons for Storyboard Pro")
            ts_file.write("\n")
            ts_file.write(extra_file_data["preamble_sbpro"])
        ts_file.write("\n\n\n")

        for class_data in all_classes:
            if class_data["name"] in SKIP_CLASSES:
                continue
            logger.debug(f"Writing class: {class_data['name']}")
            write_ts_from_class(class_data, ts_file)

        for global_data in all_globals:
            write_ts_from_interface(global_data, ts_file)

        ts_file.write("\n\n\n")
        if host == "harmony":
            logger.debug("Writing harmony-specific add-ons")
            ts_file.write(extra_file_data["harmony_post"])

            if version_num >= 20:
                ts_file.write(extra_file_data["preamble_harmony_extended"])

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


def get_all_classes_with_overrides(host, version_num):
    with open("./override/override.jsonc", "rb") as f:
        override_data = json5.load(f)

    for data in get_all_classes(host, version_num):
        if data["name"] in override_data["classes"]:
            override = override_data["classes"][data["name"]]
            if "skip" in override:
                continue
            for key, val in override.items():
                if key == "add_slots":
                    for slot in val:
                        data["slots"].append(slot)
                else:
                    data[key] = val
            logger.debug(f"Applying override: {override}")

        for slot in data["slots"]:
            if slot["name"] in override_data["slots"]:
                slot_override = override_data["slots"][slot["name"]]
                if "class_name" in slot_override and slot_override["class_name"] != data["name"]:
                    continue
                for key in slot_override:
                    if key not in ("params"):
                        logger.debug("Overriding slot: {0}".format(slot_override))
                        slot[key] = slot_override[key]
                if "params" in slot_override:
                    if slot_override.get("replace_params", False):
                        slot["params"] = slot_override["params"]
                    else:
                        for param in slot["params"]:
                            param_override = next(
                                (p for p in slot_override["params"] if p["name"] == param["name"]),
                                None,
                            )
                            if param_override:
                                logger.debug("Overriding param: {}:{}".format(slot["name"], param_override))
                                param.update(param_override)
        yield data


def get_all_classes(host, version_num):
    yield from get_core_classes(host, version_num)
    if host == "harmony" and version_num >= 20:
        yield from get_extended_classes(version_num)


def get_all_globals(host, version_num):
    if host == "harmony" and version_num >= 20:
        return get_extended_globals(version_num)
    return []


def generate(host, version_num):
    logger.info(f"Generating Typescript for {host}:{version_num}")
    _generate_ts_from_data(
        host,
        version_num,
        get_all_classes_with_overrides(host, version_num),
        get_all_globals(host, version_num),
    )


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
