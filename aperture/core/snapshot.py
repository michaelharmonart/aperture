from dataclasses import dataclass
from datetime import datetime
import os
import pwd

from pathlib import Path
from aperture.core.file import get_current_filepath, is_file_modified, load_file, save_file
from git import Commit, InvalidGitRepositoryError, Repo

@dataclass(eq=True, frozen=True)
class Snapshot():
    commit: Commit

def get_or_create_snapshot_folder(filepath : Path) -> Path | None:
    snapshots_path: Path = filepath.parent / ".snapshots"
    if not snapshots_path.exists():
        snapshots_path.mkdir()
    return snapshots_path

def get_time_string() -> str:
    now = datetime.now()
    return now.strftime("%a %b %-d at %-I:%M%p")

def get_username() -> str:
    try:
        return pwd.getpwuid(os.getuid())[0]
    except ImportError:
        return "Windows User"

def get_or_init_repo() -> Repo | None:
    path = get_current_filepath()
    if path is not None:
        try:
            return Repo(path.parent)
        except InvalidGitRepositoryError:
            return Repo.init(path.parent)
    else:
        return None

def create_snapshot(repo: Repo, filepaths: Path | list[Path], message: str | None = None, autosave: bool = False) -> Snapshot:
    if message is None:
        if autosave:
            message = f"Autosave: {get_time_string()}"
        else:
            message = f"Snapshot: {get_time_string()}"
    repo.index.add(filepaths)
    commit = repo.index.commit(message)
    return Snapshot(commit)

def get_snapshots() -> list[Snapshot]:
    repo = get_or_init_repo()
    if repo is None:
        return []
    if repo.head.is_valid() is False:
        return []
    return [Snapshot(commit) for commit in repo.iter_commits()]

def save_and_snapshot(message: str | None = None, autosave: bool = False) -> Snapshot | None:
    current_file = get_current_filepath()
    if autosave and not is_file_modified():
        return
    save_file()
    repo = get_or_init_repo()
    if current_file and repo:
        return create_snapshot(repo=repo, filepaths=current_file, message=message, autosave=autosave)

def restore_snapshot(snapshot: Snapshot):
    repo = get_or_init_repo()
    if repo is not None:
        repo.git.checkout(snapshot.commit.hexsha, "--", get_current_filepath())

def load_snapshot(snapshot: Snapshot):
    restore_snapshot(snapshot)
    load_file(get_current_filepath())