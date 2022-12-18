import logging
import argparse
from tba_types_generator import generate

HARMONY_VERSIONS = [15, 16, 17, 20, 21, 22]
SBPRO_VERSIONS = [6, 7, 20, 22]


def generate_all():
    for version_num in HARMONY_VERSIONS:
        host = 'harmony'
        generate(host, version_num)

    for version_num in SBPRO_VERSIONS:
        host = 'storyboardpro'
        generate(host, version_num)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # option that takes a value
    parser.add_argument(
        '--host', choices=['harmony', 'storyboardpro'])
    parser.add_argument('--version', type=int)
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    # generate_all()
    if args.host and args.version:
        generate(args.host, args.version)
    elif not (args.host or args.version):
        generate_all()
