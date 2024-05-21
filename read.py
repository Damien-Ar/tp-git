from zlib import decompress

from common import *

### Commun, lecture de fichier compressé
def object_content(sha1: str) -> bytes:
  try:
    with object_path(sha1).open(mode="rb") as f:
      return decompress(f.read())
  except IOError:
    raise Exception(f"fatal : {sha1}  is not a git object")


def get_object(sha1 : str) :
  header, data = object_content(sha1).split(b"\x00", maxsplit=1)
  type, size = header.split()
  assert len(data) == int(size), "Unexpected object length"

  return type, data

### Lecture des arbres

def parse_tree_entry(raw_bytes: bytes) -> tuple:
  # Entry : "mode raw_name\x00sha1"
  info, bin_sha1 = raw_bytes.split(b"\x00", maxsplit= 1)
  mode, raw_name = info.split(b" ")
  sha1 = bin_sha1.hex()
  type, _ = get_object(sha1)
  name = raw_name.decode("utf-8")
  return mode.decode(), type.decode(), sha1, name

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

### Lecture du contenu des ref
def read_ref_content(ref_path: str)-> str:
  try:
    with(repo_git_dir()/ref_path).open() as f:
      return f.readline().strip()
  except:
    raise Exception(f"fatal : can not read ref {ref_path}")


def resolve_ref(ref: str) -> str:
    if is_sha1(ref):
        return ref

    content = read_ref_content(ref)
    next_name = content.split()[1] if "ref:" in content else content

    return resolve_ref(next_name)

### Lecture des commits

def parse_commit_header(raw: str) -> dict:
  # Lignes séparées par \n
  # Données séparées par un espace : Author Damien Aranda date
  # Hash de la racine, hash du commit parent, auteur, commiter
  lines = raw.split("\n")

  header_split = [line.split(maxsplit = 1) for line in lines]
  return {name: value for name, value in header_split}

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