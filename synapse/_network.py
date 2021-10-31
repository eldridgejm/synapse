import pathlib
import collections
import itertools
import re
from typing import Union, List, Callable

from .exceptions import NetworkKeyError
from .util import get_key_parts


NOTE_TYPES = {'topic', 'project', 'thought', 'journal'}

Checker = Callable[["Network", List[str]], None]


class Network:

    CHECKS: List[Checker] = []

    def __init__(self, path: Union[str, pathlib.Path]):
        self.root = pathlib.Path(path)

    def __iter__(self):
        chain = itertools.chain(
            self.topics, self.thoughts, self.journal, self.projects,
            self.images, self.files, self.raw
            )
        return (x.key for x in chain)

    def __contains__(self, key):
        return Node(self, key).path.exists()

    def __getitem__(self, key):
        parts = key.split(':')
        if len(parts) == 1 or parts[0] in NOTE_TYPES:
            node = NoteNode(self, key)
        else:
            node = Node(self, key)

        if not node.path.exists():
            raise NetworkKeyError(node.key)

        return node

    @property
    def notes(self):
        yield from itertools.chain(
            self.topics, self.thoughts, self.journal, self.projects
            )

    @property
    def topics(self):
        yield from self._iter_notes()

    @property
    def thoughts(self):
        yield from self._iter_notes('thought')

    @property
    def journal(self):
        yield from self._iter_notes('journal')

    @property
    def projects(self):
        yield from self._iter_notes('project')

    @property
    def images(self):
        yield from self._iter_files('image')

    @property
    def files(self):
        yield from self._iter_files('file')

    @property
    def raw(self):
        yield from self._iter_files('raw')

    def _iter_notes(self, subdir=None):
        """Yield the keys of notes in the optional subdir"""
        to_key = lambda p: str(p.with_suffix('')).replace('/', ':')
        yield from self._iter_files(subdir, NodeClass=NoteNode, to_key=to_key)

    def _iter_files(self, subdir, NodeClass=None, to_key=None):
        """Yield the keys of files in the subdir."""
        if to_key is None:
            to_key = lambda p: str(p).replace('/', ':')

        if NodeClass is None:
            NodeClass = Node

        if subdir is not None:
            root_of_search = self.root / subdir
        else:
            root_of_search = self.root

        if root_of_search.is_dir():
            for subpath in root_of_search.iterdir():
                if subpath.is_file():
                    key = to_key(subpath.relative_to(self.root))
                    yield NodeClass(self, key)

    def fix_bidirectional_links(self):
        for u in self.notes:
            note_neighbors = (v for v in u.neighbors if isinstance(v, NoteNode))
            for v in note_neighbors:
                if u not in v.neighbors:
                    v.add_link(u)

    def check(self):
        failures = []
        for checker in Network.CHECKS:
            try:
                checker(self, failures)
            except FatalFailure:
                break

        return failures


class FatalFailure(Exception):
    """A failed check that may prevent other checks from running."""


@Network.CHECKS.append
def _all_links_are_existing(network, failures):
    for note in network.notes:
        for key in note.links:
            if key not in network:
                msg = f'Link to nonexistant "{key}" in "{note.key}"'
                failures.append(msg)

    if failures:
        raise FatalFailure('Some links did not exist.')


@Network.CHECKS.append
def _links_between_notes_are_bidirectional(network, failures):
    for u in network.notes:
        note_neighbors = [n for n in u.neighbors if n.type in NOTE_TYPES]
        for v in note_neighbors:
            if u not in v.neighbors:
                msg = f'Link from "{u.key}" to "{v.key}" is not bidirectional.'
                failures.append(msg)



@Network.CHECKS.append
def _projects_link_to_topics(network, failures):
    for project in network.projects:
        linked_topics = [p for p in project.neighbors if p.type == 'topic']

        if not linked_topics:
            failures.append(f'No topics linked in "{project.key}".')


@Network.CHECKS.append
def _thoughts_link_to_topics_or_projects(network, failures):
    for thought in network.thoughts:
        linked = [p for p in thought.neighbors if (p.type == 'topic') or (p.type == 'project')]

        if not linked:
            failures.append(f'No topics or projects linked in "{thought.key}".')


@Network.CHECKS.append
def _non_notes_must_have_predecessor(network, failures):
    chain = itertools.chain(network.images, network.files, network.raw)
    for node in chain:
        if not list(node.predecessors):
            msg = f'"{node.key}" has no predecessor.'
            failures.append(msg)


@Network.CHECKS.append
def _topics_must_be_connected(network, failures):
    root = next(network.topics)
    visited = set()
    all_topics = set(n.key for n in network.topics)

    def only_topics(node):
        return (u for u in node.neighbors if u.type == 'topic')

    bfs(root, neighbors=only_topics, callback=lambda node: visited.add(node.key))

    if len(visited) != len(all_topics):
        unvisited = all_topics - visited
        failures.append(f'Topic "{unvisited.pop()}" not connected to "{root.key}"')


class Node:

    def __init__(self, network: Network, key: str):
        self.network = network
        self.key = key

    def __eq__(self, other):
        return self.key == other.key

    @property
    def type(self):
        parts = self.key.split(':')
        if len(parts) > 1:
            return parts[0]
        else:
            return 'topic'

    @property
    def path(self):
        path = self.network.root / self.key.replace(':', '/')
        if path.suffix == '':
            path = path.with_suffix('.md')
        return path

    @property
    def contents(self):
        try:
            with self.path.open() as fileobj:
                return fileobj.read()
        except Exception as exc:
            raise RuntimeError(f'Could not read "{self.key}".') from exc

    @property
    def predecessors(self):
        for note in self.network.notes:
            if self in note.successors:
                yield note

    def rekey(self, new_key):
        key_parts = _get_key_parts(new_key)

        if key_parts.type != self.type:
            raise ValueError("Cannot change type with rekey.")

        dir = self.network.root / key_parts.type

        for predecessor in self.predecessors:
            predecessor._update_link(self.key, new_key)

        new_path = (dir / key_parts.name).with_suffix(self.path.suffix)
        _ensure_directory_exists(new_path)
        self.path.rename(new_path)

        self.key = new_key


def _insert_into_section(lines: List[str], section_name: str, link_text: str):
    header = f'## :{section_name}:'
    try:
        ix = lines.index(header) + 1
    except ValueError:
        ix = len(lines) + 2
        lines.append('')
        lines.append(header)
    lines.insert(ix, link_text)

def _ensure_directory_exists(path):
    if not path.is_dir():
        path = path.parent
    path.mkdir(parents=True, exist_ok=True)

class NoteNode(Node):

    @property
    def links(self):
        matches = re.findall(r'\[\[.*?\]\]', self.contents)
        return (x.strip('[]') for x in matches)

    @property
    def successors(self):
        for key in self.links:
            yield self.network[key]

    neighbors = successors

    def add_link(self, node_or_key: Union[Node, str]):
        """Make a link to the other node in the appropriate section."""
        if isinstance(node_or_key, str):
            other_node = self.network[node_or_key]
        else:
            other_node = node_or_key

        lines = self.contents.split('\n')
        section_name = other_node.type.capitalize() + 's'
        link_text = f'- [[{other_node.key}]]'
        _insert_into_section(lines, section_name, link_text)

        with self.path.open('w') as fileobj:
            fileobj.write('\n'.join(lines))

        if (other_node.type in NOTE_TYPES) and (self not in other_node.neighbors):
            other_node.add_link(self)

    def rekey(self, new_key: str):
        """Rename the note and update links in other files."""
        key_parts = get_key_parts(new_key)
        if key_parts.type == 'topic':
            dir = self.network.root
        else:
            dir = self.network.root / key_parts.type

        if key_parts.type not in NOTE_TYPES:
            raise ValueError("Cannot re-key a note to be a non-note.")

        for predecessor in self.predecessors:
            predecessor._update_link(self.key, new_key)

        new_path = (dir / key_parts.name).with_suffix('.md')
        self.path.rename(new_path)

        self.key = new_key

    def _update_link(self, old_key, new_key):
        new_contents = self.contents.replace(f'[[{old_key}]]', f'[[{new_key}]]')
        with self.path.open('w') as fileobj:
            fileobj.write(new_contents)

def bfs(root: NoteNode, neighbors=None, callback=None):
    if neighbors is None:
        neighbors = lambda node: node.neighbors

    if callback is None:
        callback = lambda node: None

    visited = set()
    queue = collections.deque([root])

    while queue:
        u = queue.pop()
        callback(u)

        for neighbor in neighbors(u):
            if neighbor.key not in visited:
                visited.add(neighbor.key)
                queue.append(neighbor)
