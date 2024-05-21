avoir le type d'un hash
git cat-file -t a21e91b14c870770cf612020a0619a90d987df4c

avoir le contenu d'un fichier
git cat-file -p a21e91b14c870770cf612020a0619a90d987df4c

avoir le contenu d'un arbre
git ls-tree 1aa294f639e9d2515011b2b468fcfde2e0d83c7c

git hash-object file3.txt

print(repo_notgit_dir("./test"))
print(get_object("5fc3a27876f4d94b666562d74b62627d33879aa1"))
print(resolve_ref("HEAD"))
print(resolve_ref("5fc3a27876f4d94b666562d74b62627d33879aa1"))
print(hash_object(Path("./test/test.txt")))
print(parse_commit(resolve_ref("HEAD")))
print_history("HEAD")
print(parse_tree(parse_commit(resolve_ref("HEAD"))["tree"]))commit