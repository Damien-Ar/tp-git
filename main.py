from pathlib import Path
import zlib
import hashlib
from time import time, strftime

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

class Committer:
  def __init__(self, name, email) -> None:
    self.name = name
    self.email = email
  
  def __str__(self) -> str:
    return f"{self.name} <{self.email}>"
  
GIT_COMMITTER = Committer("Damien-Ar", "damien.aranda42@gmail.com")

def repo_root(path: str = None) -> Path:
  # Get current directory if unspecified
  path = Path.cwd() if path is None else Path(path).resolve()

  while True:
    ## look for git subdir
    if (path / GIT_DIR).is_dir():
      return path # found Root
    
    if (parent := path.parent) == path:
      raise Exception("fatal : Not a notgit repository")
    
    path = parent

def repo_notgit_dir(path: str = None) -> Path:
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

  return repo_notgit_dir() / GIT_OBJECTS_DIR / sha1[:2] / sha1[2:]

def object_content(sha1: str) -> bytes:
  try:
    with object_path(sha1).open(mode="rb") as f:
      return zlib.decompress(f.read())
  except IOError:
    raise Exception("fatal : Not a notGit object")
  
def get_object(sha1 : str) :
  header, data = object_content(sha1).split(b"\x00", maxsplit=1)
  type, size = header.split()
  assert len(data) == int(size), "Unexpected object length"

  return type, data

def read_ref_content(ref_path: str)-> str:
  try: 
    with(repo_notgit_dir()/ref_path).open() as f:
      return f.readline().strip()
  except:
    raise Exception(f"fatal : can not read ref {ref_path}")

def resolve_ref(ref : str) -> str:
  if is_sha1(ref):
    return ref
  
  content = read_ref_content(ref)
  next_name = content.split()[1] if "ref:" in content else content

  return resolve_ref(next_name)

def hash_object(path: Path, object_type: str = "blob", write: bool = False) -> str:
  user_data = path.read_bytes()
  return hash_content(user_data, object_type=object_type, write=write)

def hash_content(value: bytes, object_type: str = "tree", write: bool = False) -> str:
  raw_content = f"{object_type} {len(value)}\x00".encode() + value
  sha1 = hashlib.sha1(raw_content).hexdigest()

  if write:
    obj_path = object_path(sha1)
    obj_path.parent.mkdir(exist_ok = True)

    obj_path.write_bytes(zlib.compress(raw_content))
  
  return sha1

def parse_commit_header(raw: str) -> dict:
  #lines séparéses par \n
  #données séparée par un espace
  #hash de la racine, hash du commit parent, auteur, commiter
  lines = raw.split("\n")

  splitted = [line.split(maxsplit = 1) for line in lines]
  return {name: value for name, value in splitted}

def encode_commit_header(metadata: dict) -> bytes:
  header = "\n".join([key + " " + value for key, value in metadata.items()])
  return header.encode()

def encode_commit(metadata, message) -> bytes:
  raw_header = encode_commit_header(metadata)
  raw_message = message.encode()
  return raw_header + b"\n\n" + raw_message

def get_commit_metadata():
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
  return hash_content(raw_commit, object_type="commit", write=write)

def parse_commit(sha1: str) -> dict:
  # forme header\n\nmessage
  type, data = get_object(sha1)
  assert type == b"commit"

  raw_header, message = data.decode("utf-8").split("\n\n")
  commit = parse_commit_header(raw_header)
  commit["message"] = message
  return commit

def print_history(_from: str) -> None:
  sha1 = resolve_ref(_from)
  while True:
    commit = parse_commit(sha1)
    print(f"{sha1} : {commit['message']}")

    try:
      sha1 = commit["parent"]
    except KeyError:
      break

def parse_tree_entry(raw_bytes: bytes) -> tuple:
  ### Entry : "mode raw_name\x00sha1"
  info, bin_sha1 = raw_bytes.split(b"\x00", maxsplit= 1)
  mode, raw_name = info.split(b" ")
  sha1 = bin_sha1.hex()
  type, _ = get_object(sha1)
  name = raw_name.decode("utf-8")
  return mode.decode(), type.decode(), sha1, name

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

def parse_tree(sha1 : str) -> list:
  type, data = get_object(sha1)
  assert type == b"tree"
  print(data)
  entries = []
  start = 0
  while True:
    try:
      sep_index = data.index(b"\x00", start)
      end = sep_index + 1 + 20
    except ValueError:
      break
#    print(f"start={start}, end={end}, data ={data[start:end]}")
    entries.append(parse_tree_entry(data[start:end]))
    start = end + 1

  return entries

def should_ignore_path(path: Path) -> bool:
  path_string = str(path)
  return DEFAUT_GIT_DIR in path_string or DEFAUT_NOTGIT_DIR in path_string 

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
  return b"\x00".join(entries)

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

def restore_file(blob_sha1 : str, path: Path):
  type, data = get_object(blob_sha1)
  assert type == b"blob"

  path.write_bytes(data)

def restore_tree(tree_sha1: str, path: Path):
  path.mkdir(exist_ok = True)

  tree = parse_tree(tree_sha1)
  for _, type, sha1, name in tree:
    target_path = path/name
    if type == b"blob":
      restore_file(sha1, target_path)
    elif type == b"tree":
      restore_tree(sha1, target_path)

def switch(ref: str) -> None:
  if ref in read_ref_content("HEAD"):
    print(f"Already on {ref}")
    return

  sha1 = resolve_ref(ref)
  commit = parse_commit(ref)
  tree_ref = commit["tree"]

  restore_tree(tree_ref, repo_root)

  new_head = sha1 if ref == sha1 else f"ref: {ref}"
  (repo_notgit_dir() / "HEAD").write_text(new_head)  

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



# print(repo_notgit_dir("./test"))
# print(get_object("5fc3a27876f4d94b666562d74b62627d33879aa1"))
# print(resolve_ref("HEAD"))
# print(resolve_ref("5fc3a27876f4d94b666562d74b62627d33879aa1"))
# print(hash_object(Path("./test/test.txt")))
# print(parse_commit(resolve_ref("HEAD")))
# print_history("HEAD")
# print(parse_tree(parse_commit(resolve_ref("HEAD"))["tree"]))commit