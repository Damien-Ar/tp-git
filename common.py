from pathlib import Path

from Committer import Committer

DEFAUT_GIT_DIR = ".git"
DEFAUT_NOTGIT_DIR = ".notgit"
GIT_DIR = ".notgit"
GIT_OBJECTS_DIR = "objects"
GIT_REFS_HEAD_DIR = "refs/heads"
GIT_REFS_TAGS_DIR = "refs/tags"
GIT_HEAD_FILE = "HEAD"
GIT_DEFAULT_BRANCH_NAME = "main"
GIT_DATA_FOLDERS = [
  GIT_OBJECTS_DIR,
  GIT_REFS_HEAD_DIR,
  GIT_REFS_TAGS_DIR
]
GIT_COMMITTER = Committer("Damien-Ar", "damien.aranda42@gmail.com")


def repo_root(path: str = None) -> Path:
  # Get current directory if unspecified
  path = Path.cwd() if path is None else Path(path).resolve()

  while True:
    ## look for git subdir
    if (path / GIT_DIR).is_dir():
      return path  # found Root

    if (parent := path.parent) == path:
      raise Exception("fatal : Not a git repository")

    path = parent

def repo_git_dir(path: str = None) -> Path:
  return repo_root(path) / GIT_DIR

def is_hex(s: str) -> bool:
  try:
    int(s, 16)
    return True
  except:
    return False

def is_sha1(s: str) -> bool:
  return len(s) == 40 and is_hex(s)

def object_path(sha1: str) -> Path:
  assert is_sha1(sha1), "Invalid sha1"

  return repo_git_dir() / GIT_OBJECTS_DIR / sha1[:2] / sha1[2:]