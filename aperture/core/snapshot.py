from dataclasses import dataclass
from datetime import datetime
import os
import pwd

from pathlib import Path
from aperture.core.file import get_current_filepath, load_file, save_file
from git import Commit, InvalidGitRepositoryError, Repo
import git

@dataclass(eq=True, frozen=True)
class Snapshot():
    commit: Commit

def get_time_string() -> str:
    now = datetime.now()
    return now.strftime("%a %b %-d at %-I:%M%p")

def get_username() -> str:
    try:
        return pwd.getpwuid(os.getuid())[0]
    except ImportError:
        return "Windows User"

def get_or_init_repo() -> Repo | None:
    path = get_current_filepath().parent
    if path is not None:
        try:
            return Repo(path)
        except InvalidGitRepositoryError:
            return Repo.init(path)
    else:
        return None

def create_snapshot(repo: Repo, filepath: Path, message: str | None = None) -> Snapshot:
    if message is None:
        message = f"Snapshot: {get_username()} at {get_time_string()}"
    repo.index.add(filepath)
    commit = repo.index.commit(message)
    return Snapshot(commit)

def get_snapshots() -> list[Snapshot]:
    repo = get_or_init_repo()
    if repo is None:
        return []
    if repo.head.is_valid() is False:
        return []
    return [Snapshot(commit) for commit in repo.iter_commits()]

def save_and_snapshot(message: str | None) -> Snapshot | None:
    save_file()
    current_file = get_current_filepath()
    repo = get_or_init_repo()
    if current_file and repo:
        return create_snapshot(repo, current_file, message)

def restore_snapshot(snapshot: Snapshot):
    repo = get_or_init_repo()
    repo.git.checkout(snapshot.commit.hexsha, "--", get_current_filepath())

def load_snapshot(snapshot: Snapshot):
    restore_snapshot(snapshot)
    load_file(get_current_filepath())