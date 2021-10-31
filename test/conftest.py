import pytest
import pathlib
import textwrap
from typing import List


def ensure_directory_exists(path):
    if not path.is_dir():
        path = path.parent
    path.mkdir(parents=True, exist_ok=True)


class Example:

    def __init__(self, path):
        self.path = pathlib.Path(path)

        for subdir in {'image', 'thought', 'journal', 'project', 'file', 'raw'}:
            (self.path / subdir).mkdir()

    def make_notes(self, keys: List[str]):
        for key in keys:
            self.make_note(key)

    def make_note(self, key, contents=''):
        contents = textwrap.dedent(contents)
        parts = key.split(':')
        if len(parts) > 2:
            raise ValueError("Nested directories not permitted.")

        if len(parts) == 2:
            filepath = (self.path / parts[0] / parts[1])
        else:
            filepath = (self.path / parts[0])

        with filepath.with_suffix('.md').open('w') as fileobj:
            fileobj.write(contents)

    def make_image(self, filename):
        ensure_directory_exists(self.path / 'image' / filename)
        with open(self.path / 'image' / filename, 'w') as fileobj:
            pass

    def make_file(self, filename):
        ensure_directory_exists(self.path / 'file' / filename)
        with open(self.path / 'file' / filename, 'w') as fileobj:
            pass

    def make_raw(self, filename):
        ensure_directory_exists(self.path / 'raw' / filename)
        with open(self.path / 'raw' / filename, 'w') as fileobj:
            pass


@pytest.fixture
def example(tmpdir):
    return Example(tmpdir)
