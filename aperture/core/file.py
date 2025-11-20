from pathlib import Path
import maya.cmds as cmds

def get_current_filepath() -> Path | None:
    """
    Returns the full path of the currently open Maya scene as a Path object,
    or None if the scene has not been saved yet.
    """
    filename: str = cmds.file(q=True, sn=True)
    if filename == "":
        return None
    return Path(filename)