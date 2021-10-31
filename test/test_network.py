import pytest

import synapse


# network
# =======

def test_iterator_produces_keys(example):
    # given
    example.make_notes([
        'foo', 'bar', 'thought:baz', 'journal:2021-10-12'
    ])
    example.make_image('foo.png')
    example.make_raw('todo.today')
    example.make_file('something.pdf')

    # when
    network = synapse.Network(example.path)

    # then
    actual = set(network)
    expected = {'foo', 'bar', 'thought:baz', 'journal:2021-10-12',
            'image:foo.png', 'raw:todo.today', 'file:something.pdf'}
    assert actual == expected


def test_topics_attr_produces_only_topics(example):
    # given
    example.make_notes([
        'foo', 'bar', 'thought:baz', 'journal:2021-10-12'
    ])
    example.make_image('foo.png')
    example.make_raw('todo.today')
    example.make_file('something.pdf')

    # when
    network = synapse.Network(example.path)

    # then
    actual = set(x.key for x in network.topics)
    expected = {'bar', 'foo'}
    assert actual == expected


def test_thought_attr_produces_only_thought(example):
    # given
    example.make_notes([
        'foo', 'bar', 'thought:baz', 'journal:2021-10-12'
    ])
    example.make_image('foo.png')
    example.make_raw('todo.today')
    example.make_file('something.pdf')

    # when
    network = synapse.Network(example.path)

    # then
    actual = set(x.key for x in network.thoughts)
    expected = {'thought:baz'}
    assert actual == expected

def test_subscriptable(example):
    # given
    example.make_notes([
        'foo', 'bar', 'thought:baz', 'journal:2021-10-12'
    ])
    example.make_image('foo.png')
    example.make_raw('todo.today')
    example.make_file('something.pdf')

    # when
    network = synapse.Network(example.path)

    # then
    network['bar'].key == 'bar'
    network['thought:baz'].key == 'thought:baz'

def test_allow_images_to_have_slashes_in_key(example):
    # given
    example.make_image('dir/foo.png')

    # when
    network = synapse.Network(example.path)
    node = network['image:dir/foo.png']

    # then
    assert node.path == example.path / 'image/dir/foo.png'
    assert node.path.exists()

def test_allow_files_to_have_slashes_in_key(example):
    # given
    example.make_file('dir/foo.png')

    # when
    network = synapse.Network(example.path)
    node = network['file:dir/foo.png']

    # then
    assert node.path == example.path / 'file/dir/foo.png'
    assert node.path.exists()

def test_allow_raw_to_have_slashes_in_key(example):
    # given
    example.make_raw('dir/foo.png')

    # when
    network = synapse.Network(example.path)
    node = network['raw:dir/foo.png']

    # then
    assert node.path == example.path / 'raw/dir/foo.png'
    assert node.path.exists()

def test_fix_bidirectional_links(example):
    # given
    example.make_note('foo')
    example.make_note('thought:bar', """
            [[foo]]
            """)
    example.make_note('project:baz', """
            [[thought:bar]]
            """)
    example.make_note('journal:2021-10-10', """
            [[thought:bar]]
            """)

    # when
    network = synapse.Network(example.path)
    network.fix_bidirectional_links()

    # then
    assert network['thought:bar'] in network['foo'].neighbors
    assert network['project:baz'] in network['thought:bar'].neighbors
    assert network['journal:2021-10-10'] in network['thought:bar'].neighbors


# checks
# ======

def test_fails_if_link_points_to_nonexisting_file(example):
    # given
    example.make_note('bar', """
        [[baz]]
        [[quux]]
        [[thought:something else]]
    """)

    # when
    network = synapse.Network(example.path)
    failures = network.check()

    assert len(failures) == 3


def test_fails_if_link_between_notes_is_not_bidirectional(example):
    # given
    example.make_note('bar', """
    """)

    example.make_note('thought:foo', """
            [[bar]]
    """)

    # when
    network = synapse.Network(example.path)
    failures = network.check()

    assert len(failures) == 1
    assert 'bidirectional' in failures[0]


def test_fails_if_project_does_not_link_to_topic(example):
    # given
    example.make_note('bar', """
    """)

    example.make_note('project:foo', """
    """)

    # when
    network = synapse.Network(example.path)
    failures = network.check()

    assert len(failures) == 1


def test_fails_if_thought_does_not_link_to_topic_or_project(example):
    # given
    example.make_note('foo', """
            [[project:bar]]
    """)

    example.make_note('project:bar', """
            [[foo]]
    """)

    example.make_note('thought:baz1', """
    """)

    # when
    network = synapse.Network(example.path)
    failures = network.check()

    assert len(failures) == 1


def test_does_not_raise_if_thought_links_to_topic(example):
    # given
    example.make_note('foo', """
            [[project:bar]]
            [[thought:baz]]
    """)

    example.make_note('project:bar', """
            [[foo]]
    """)

    example.make_note('thought:baz', """
            [[foo]]
    """)

    # when
    network = synapse.Network(example.path)
    network.check()


def test_does_not_raise_if_thought_links_to_project(example):
    # given
    example.make_note('foo', """
            [[project:bar]]
    """)

    example.make_note('project:bar', """
            [[foo]]
            [[thought:baz]]
    """)

    example.make_note('thought:baz', """
            [[project:bar]]
    """)

    # when
    network = synapse.Network(example.path)
    network.check()


def test_fails_if_image_has_no_predecessor(example):
    # given
    example.make_note('foo')
    example.make_image('foo.png')

    # when
    network = synapse.Network(example.path)
    failures = network.check()

    assert len(failures) == 1
    assert 'predecessor' in failures[0]

def test_allows_image_keys_to_have_slashes(example):
    # given
    example.make_note('foo', """
            [[image:a/b/c/foo.pdf]]
            """)
    example.make_image('a/b/c/foo.pdf')

    # when
    network = synapse.Network(example.path)
    failures = network.check()

    assert len(failures) == 0

def test_fails_if_file_has_no_predecessor(example):
    # given
    example.make_note('foo')
    example.make_file('foo.pdf')

    # when
    network = synapse.Network(example.path)
    failures = network.check()

    assert len(failures) == 1
    assert 'predecessor' in failures[0]


def test_allows_file_keys_to_have_slashes(example):
    # given
    example.make_note('foo', """
            [[file:a/b/c/foo.pdf]]
            """)
    example.make_file('a/b/c/foo.pdf')

    # when
    network = synapse.Network(example.path)
    failures = network.check()

    assert len(failures) == 0


def test_fails_if_raw_has_no_predecessor(example):
    # given
    example.make_note('foo')
    example.make_raw('foo.today')

    # when
    network = synapse.Network(example.path)
    failures = network.check()

    assert len(failures) == 1
    assert 'predecessor' in failures[0]

def test_allows_raw_keys_to_have_slashes(example):
    # given
    example.make_note('foo', """
            [[raw:a/b/c/foo.pdf]]
            """)
    example.make_raw('a/b/c/foo.pdf')

    # when
    network = synapse.Network(example.path)
    failures = network.check()

    assert len(failures) == 0

def test_fails_if_topics_are_disconnected(example):
    # given
    example.make_note('foo', """
            [[bar]]
    """)

    example.make_note('bar', """
            [[foo]]
    """)

    example.make_note('baz', """
    """)

    # when
    network = synapse.Network(example.path)
    failures = network.check()

    assert len(failures) == 1
    assert 'connected' in failures[0]


# nodes
# =====

def test_neighbors_produces_all_edges_in_file(example):
    # given
    example.make_note('bar', """
        [[baz]]
        [[quux]]
        [[thought:something else]]
    """)

    example.make_note('baz', """
        [[bar]]
    """)

    example.make_note('quux', """
        [[bar]]
    """)

    example.make_note('thought:something else', """
        [[bar]]
    """)

    # when
    network = synapse.Network(example.path)
    bar = network['bar']

    # then
    actual = set(x.key for x in bar.neighbors)
    expected = {'baz', 'quux', 'thought:something else'}
    assert actual == expected


def test_predecessors_for_note(example):
    # given
    example.make_note('thought:something else')

    example.make_note('bar', """
        [[thought:something else]]
    """)

    example.make_note('baz', """
        [[thought:something else]]
    """)

    example.make_note('project:my new project', """
        [[thought:something else]]
    """)

    # when
    network = synapse.Network(example.path)
    node = network['thought:something else']

    # then
    actual = set(x.key for x in node.predecessors)
    expected = {'baz', 'bar', 'project:my new project'}
    assert actual == expected


def test_predecessor_for_image(example):
    # given
    example.make_image('foo.png')

    example.make_note('bar', """
            [[image:foo.png]]
    """)

    example.make_note('baz', """
            [[image:foo.png]]
    """)

    example.make_note('project:my new project', """
            [[image:foo.png]]
    """)

    # when
    network = synapse.Network(example.path)
    node = network['image:foo.png']

    # then
    actual = set(x.key for x in node.predecessors)
    expected = {'baz', 'bar', 'project:my new project'}
    assert actual == expected

def test_add_link_to_note_node(example):
    # given
    example.make_note('bar', """
        [[image:foo.png]]
    """)

    example.make_note('thought:foo')
    example.make_image('foo.png')
    network = synapse.Network(example.path)
    node = network['bar']

    # when
    node.add_link('thought:foo')

    # then
    assert '## :Thoughts:' in node.contents
    assert '- [[thought:foo]]' in node.contents


def test_add_link_adds_to_beginning_of_section(example):
    # given
    example.make_note('bar', """
        ## :Thoughts:
        - [[thought:foo]]
    """)

    example.make_note('thought:baz')
    example.make_note('thought:foo')

    network = synapse.Network(example.path)
    node = network['bar']

    # when
    node.add_link('thought:baz')

    # then
    lines = node.contents.split('\n')
    assert '## :Thoughts:' in node.contents
    lines.index('- [[thought:baz]]') < lines.index('- [[thought:foo]]')


def test_add_link_between_notes_is_bidirectional(example):
    # given
    example.make_note('foo')
    example.make_note('bar')

    # when
    network = synapse.Network(example.path)
    network['foo'].add_link('bar')

    # then
    assert network['bar'] in network['foo'].neighbors
    assert network['foo'] in network['bar'].neighbors


def test_add_link_is_directional_if_one_node_is_not_a_note(example):
    # given
    example.make_note('foo')
    example.make_image('bar.png')

    # when
    network = synapse.Network(example.path)
    network['foo'].add_link('image:bar.png')

    # then
    assert network['image:bar.png'] in network['foo'].neighbors


def test_rename_note_updates_links_in_other_files(example):
    # given
    example.make_note('foo')
    example.make_note('bar', """
            [[foo]]
            """)

    network = synapse.Network(example.path)

    # when
    network['foo'].rename('baz')

    # then
    assert 'foo' not in network
    network['baz'] in network['bar'].neighbors
