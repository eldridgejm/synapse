import argparse
import pathlib

from ._network import Network, NetworkKeyError
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


def cmd_rekey(args):
    network = Network(args.workdir)
    network[args.src].rekey(args.dst)


def cmd_link(args):
    network = Network(args.workdir)
    network[args.u].add_link(args.v)


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

    rekey_parser = subparsers.add_parser('rekey')
    rekey_parser.add_argument('src')
    rekey_parser.add_argument('dst')
    rekey_parser.set_defaults(cmd=cmd_rekey)

    link_parser = subparsers.add_parser('link')
    link_parser.add_argument('u')
    link_parser.add_argument('v')
    link_parser.set_defaults(cmd=cmd_link)

    args = parser.parse_args()

    args.cmd(args)
