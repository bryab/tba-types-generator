import logging
import argparse
import os
from pathlib import Path
from tba_types_generator import generate, DEFAULT_OUTPUT_DIR

HARMONY_VERSIONS = [15, 16, 17, 20, 21, 22]
SBPRO_VERSIONS = [6, 7, 20, 22]


def generate_all():
    generate_host("harmony")
    generate_host("storyboardpro")


def generate_host(host):
    if host == "harmony":
        version_nums = HARMONY_VERSIONS
    else:
        version_nums = SBPRO_VERSIONS

    for version_num in version_nums:
        generate(host, version_num)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # option that takes a value
    parser.add_argument("--host", choices=["harmony", "storyboardpro"])
    parser.add_argument("--version", type=int)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
    args = parser.parse_args()
    os.environ["TBA_TYPES_OUTPUT_DIR"] = str(args.output_dir)
    logging.basicConfig(level=logging.DEBUG)
    # generate_all()
    if args.host:
        if args.version:
            generate(args.host, args.version)
        else:
            generate_host(args.host)
    elif not (args.host or args.version):
        generate_all()
