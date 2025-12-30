from typing import cast
from pathlib import Path
import maya.cmds as cmds

def get_current_filepath() -> Path | None:
    """
    Returns the full path of the currently open Maya scene as a Path object,
    or None if the scene has not been saved yet.
    """
    filename = cast(str, cmds.file(query=True, sceneName=True))
    if filename == "":
        return None
    return Path(filename)


def is_file_modified() -> bool:
    """
    Checks if the current Maya scene has unsaved modifications.

    Returns:
        bool: True if the scene has unsaved changes, False otherwise.
    """
    file_query = cast(bool, cmds.file(query=True, modified=True))
    return file_query

def save_file():
    cmds.file(save=True, force=True)

def load_file(path: Path):
    if is_file_modified():
        result = cmds.confirmDialog(
            title='Unsaved Changes',
            message='The current scene has unsaved changes.\nContinue without making a snapshot?',
            button=['Yes', 'No'],
            defaultButton='No',
            cancelButton='No',
            dismissString='No'
        )
        if result == 'No':
            return
    cmds.file(str(path), open=True, force=True)
    print(f"loading {path}")
