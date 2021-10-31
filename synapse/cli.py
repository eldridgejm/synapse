import argparse
import pathlib

from ._network import Network
from . import draw


def cmd_check(args):
    network = Network(args.workdir)
    failures = network.check()
    for failure in failures:
        print(failure)


def cmd_draw(args):
    network = Network(args.workdir)
    draw.topic_graph(network)


def cmd_fix_bidirectional_links(args):
    network = Network(args.workdir)
    network.fix_bidirectional_links()


def _key_from_path(path, root):
    path = str(pathlib.Path(path).relative_to(root))
    parts = path.split('/', 1)

    if len(parts) == 1:
        kind = 'topic'
        key = parts[0]
    else:
        kind = parts[0]
        key = kind + ':' + parts[1]

    if kind in {'topic', 'thought', 'journal', 'project'}:
        key = key[:-3]

    return key


def cmd_rename(args):
    src_key = _key_from_path(args.src, args.workdir)
    dst_key = _key_from_path(args.dst, args.workdir)
    network = Network(args.workdir)
    network[src_key].rekey(dst_key)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', default=pathlib.Path.cwd())

    subparsers = parser.add_subparsers()

    check_parser = subparsers.add_parser('check')
    check_parser.set_defaults(cmd=cmd_check)

    draw_parser = subparsers.add_parser('draw')
    draw_parser.set_defaults(cmd=cmd_draw)

    fix_parser = subparsers.add_parser('fix-bidirectional-links')
    fix_parser.set_defaults(cmd=cmd_fix_bidirectional_links)

    rename_parser = subparsers.add_parser('rename')
    rename_parser.add_argument('src')
    rename_parser.add_argument('dst')
    rename_parser.set_defaults(cmd=cmd_rename)

    args = parser.parse_args()

    args.cmd(args)
