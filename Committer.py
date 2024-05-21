class Committer:
  def __init__(self, name, email) -> None:
    self.name = name
    self.email = email

  def __str__(self) -> str:
    return f"{self.name} <{self.email}>"