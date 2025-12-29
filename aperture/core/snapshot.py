import getpass
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from git import Commit, GitCommandError, InvalidGitRepositoryError, Repo
from git.repo.base import NoSuchPathError

from aperture.core.file import get_current_filepath, is_file_modified, load_file, save_file


@dataclass(eq=True, frozen=True)
class Snapshot:
    commit: Commit


def get_or_create_snapshot_folder(filepath: Path) -> Path | None:
    snapshots_path: Path = filepath.parent / ".snapshots"
    if not snapshots_path.exists():
        snapshots_path.mkdir()
    return snapshots_path


def get_time_string() -> str:
    now = datetime.now()
    weekday_str = now.strftime("%a")
    month_str = now.strftime("%b")
    day = now.day
    hour = now.hour % 12 or 12
    minute = now.minute
    am_pm_str = now.strftime("%p")
    return f"{weekday_str} {month_str} {day} at {hour}:{minute:02d}{am_pm_str}"


def get_username() -> str:
    return getpass.getuser()


def repo_from_filepath(filepath: Path) -> Repo | None:
    try:
        return Repo(filepath.parent)
    except InvalidGitRepositoryError:
        return Repo.init(filepath.parent)
    except NoSuchPathError:
        return None


def is_repo_safe(repo: Repo) -> bool:
    try:
        repo.git.status()
        return True
    except GitCommandError as e:
        return False

def make_repo_safe(repo: Repo):
    path = repo.working_tree_dir
    if path is not None:
        repo.git.config("--global", "--add", "safe.directory", path)

def get_or_init_repo() -> Repo | None:
    path = get_current_filepath()
    if path is not None:
        repo = repo_from_filepath(path)
        if repo is None:
            return None
        if not is_repo_safe(repo):
            make_repo_safe(repo)
        return repo
    else:
        return None


def create_snapshot(
    repo: Repo, filepaths: Path | list[Path], message: str | None = None, autosave: bool = False
) -> Snapshot:
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
    current_file = get_current_filepath()
    if current_file is None:
        return []
    repo_root = Path(repo.working_dir)
    return [
        Snapshot(commit) for commit in repo.iter_commits(paths=current_file.relative_to(repo_root))
    ]


def save_and_snapshot(message: str | None = None, autosave: bool = False) -> Snapshot | None:
    current_file = get_current_filepath()
    if current_file is None:
        return
    if autosave and not is_file_modified():
        return
    save_file()
    repo = get_or_init_repo()
    if current_file and repo:
        return create_snapshot(
            repo=repo, filepaths=current_file, message=message, autosave=autosave
        )


def restore_snapshot(snapshot: Snapshot):
    repo = get_or_init_repo()
    if repo is not None:
        repo.git.checkout(snapshot.commit.hexsha, "--", get_current_filepath())


def load_snapshot(snapshot: Snapshot):
    restore_snapshot(snapshot)
    load_file(get_current_filepath())
