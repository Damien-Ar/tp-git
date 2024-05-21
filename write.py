from zlib import compress
from hashlib import sha1 as hash_sha1
from time import time, strftime

from read import resolve_ref, read_ref_content
from common import *


### Écrire les fichiers

def hash_object(path: Path, object_type: str = "blob", write: bool = False) -> str:
  file_data = path.read_bytes()
  return hash_content(file_data, object_type=object_type, write=write)


def hash_content(value: bytes, object_type: str = "tree", write: bool = False) -> str:
    raw_content = f"{object_type} {len(value)}\x00".encode() + value
    sha1 = hash_sha1(raw_content).hexdigest()

    if write:
        obj_path = object_path(sha1)
        obj_path.parent.mkdir(exist_ok=True)

        obj_path.write_bytes(compress(raw_content))

    return sha1

### Écrire les tree

def encode_tree_entry(file: Path) -> bytes:
  # folder test : fe34e09301aab87fcbe2c323a9fd6abb9d709c0d
  sha1 = hash_object(file)
  mode = "100644".encode()
  raw_name = file.name.encode()
  info = mode + b" " + raw_name
  return info + b"\x00" + bytes.fromhex(sha1)

def encode_tree_entry_tree(path: Path, value: bytes) -> bytes:
  sha1 = hash_content(value)
  mode = "040000".encode()
  raw_name = path.name.encode()
  info = mode + b" " + raw_name
  return info + b"\x00" + bytes.fromhex(sha1)

def should_ignore_path(path: Path) -> bool:
  # TODO .gitignore
  return path.match(DEFAUT_GIT_DIR) or path.match(DEFAUT_NOTGIT_DIR)

def encode_tree(path: Path) -> bytes:
  entries = []
  for child in path.iterdir():
    if should_ignore_path(child):
      print(f"ignore {child}")
      continue
    if(child.is_file()):
      entries.append(encode_tree_entry(child))
    else:
      entries.append(encode_tree_entry_tree(child, encode_tree(child)))
  return b"".join(entries)

def write_tree(path: Path) -> str:
  tree_content = encode_tree(path)
  return hash_content(tree_content, write=True)

def write_dir(path: Path):
  for child in path.iterdir():
    if should_ignore_path(child):
      print(f"ignore {child}")
      continue
    if(child.is_file()):
      hash = hash_object(child, write=True)
      print(f"Objet écrit : {hash}")
    else:
      write_dir(child)
  hash_courant = write_tree(path)
  print(f"écriture du dossier: {hash_courant}")

### Écrire les commits

def encode_commit_header(metadata: dict) -> bytes:
  header = "\n".join([key + " " + value for key, value in metadata.items()])
  return header.encode()

def encode_commit(metadata, message) -> bytes:
  raw_header = encode_commit_header(metadata)
  raw_message = message.encode()
  return raw_header + b"\n\n" + raw_message

def get_commit_metadata() -> dict:
  metadata = {}
  metadata["tree"] = hash_content(encode_tree(repo_root()))
  try:
    metadata["parent"] = resolve_ref(GIT_HEAD_FILE)
  except:
    pass
  metadata_author = f"{GIT_COMMITTER} {int(time())} {strftime('%z')}"
  metadata["author"] =  metadata_author
  metadata["committer"] = metadata_author
  return metadata

def commit(message: str, write: bool = False):
  metadata = get_commit_metadata()
  raw_commit = encode_commit(metadata, message)
  hash = hash_content(raw_commit, object_type="commit", write=write)
  if write:
    write_ref(hash)
  print(hash)

def write_ref(hash: str) -> None:
  head_content = read_ref_content(GIT_HEAD_FILE)
  if not "ref:" in head_content:
    raise Exception("Contenue de HEAD corrompu")
  branch_ref = repo_git_dir() / head_content.split()[1]
  branch_ref.write_text(hash)

### Initialisation du répo

def initialise_repo(path: str=None) -> None :
  base_path = Path.cwd() if path is None else Path(path).resolve()
  repo_path = base_path / GIT_DIR
  try:
    repo_path.mkdir()
    for dir in GIT_DATA_FOLDERS:
      (repo_path / dir).mkdir(parents=True)
    (repo_path / GIT_HEAD_FILE).write_text(f"ref: {GIT_REFS_HEAD_DIR}/{GIT_DEFAULT_BRANCH_NAME}")
  except:
    print("There is already a repository")