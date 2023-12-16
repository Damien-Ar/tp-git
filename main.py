from pathlib import Path
import zlib
import hashlib

GIT_DIR = ".git"

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

  return repo_notgit_dir() / "objects" / sha1[:2] / sha1[2:]

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

def hash_object(path: str, write:bool = False) -> str:
  user_data = (repo_root() / path).read_bytes()
  raw_content = f"blob {len(user_data)}\x00".encode() + user_data
  sha1 = hashlib.sha1(raw_content).hexdigest()

  if write:
    obj_path = object_path(sha1)
    obj_path.parent.mkdir(exist_ok = True)

    obj_path.write_bytes(zlib.compress(raw_content))
  
  return sha1

def parse_commit_header(raw: str) -> dict:
  lines = raw.split("\n")

  splitted = [line.split(maxsplit = 1) for line in lines]
  return {name: value for name, value in splitted}

def parse_commit(sha1: str) -> dict:
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

def parse_tree_entry(raw_bytes: str) -> tuple:
  info, bin_sha1 = raw_bytes.split(b"\x00", maxsplit= 1)
  mode, raw_name = info.split(b" ")
  sha1 = bin_sha1.hex()
  type, _ = get_object(sha1)
  name = raw_name.decode("utf-8")
  return mode, type, sha1, name

def parse_tree(sha1 : str) -> list:
  type, data = get_object(sha1)
  assert type == b"tree"
  entries = []
  start = 0
  while True:
    try:
      sep_index = data.index(b"\x00", start)
      end = sep_index + 1 + 20
    except ValueError:
      break

    entries.append(parse_tree_entry(data[start:end]))
    start = end

  return entries

print(repo_notgit_dir("./test"))
print(get_object("5fc3a27876f4d94b666562d74b62627d33879aa1"))
print(resolve_ref("HEAD"))
print(resolve_ref("5fc3a27876f4d94b666562d74b62627d33879aa1"))
print(hash_object("./test.txt"))
print(parse_commit(resolve_ref("HEAD")))
print_history("HEAD")
print(parse_tree(parse_commit(resolve_ref("HEAD"))["tree"]))