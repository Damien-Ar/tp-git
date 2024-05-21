from read import resolve_ref, read_ref_content, get_object, parse_tree, parse_commit
from common import *

### checkout (wip)

def restore_file(blob_sha1: str, path: Path):
    type, data = get_object(blob_sha1)
    assert type == b"blob"

    path.write_bytes(data)


def restore_tree(tree_sha1: str, path: Path):
    path.mkdir(exist_ok=True)

    tree = parse_tree(tree_sha1)
    for _, type, sha1, name in tree:
        target_path = path / name
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

    restore_tree(tree_ref, repo_root())

    new_head = sha1 if ref == sha1 else f"ref: {ref}"
    (repo_git_dir() / "HEAD").write_text(new_head)