from pathlib import Path

def getPath(param):
    """
    Get project's path.

    Parameters
    ----------
    param : string
        Either "project" or "root". "project" will return the path to the project's directory, "root" will return the path to the project's root directory.

    Returns
    -------
    string
        Absolute path to project's root or project directory.
    """
    currentPath = Path(__file__).parent.absolute()
    projectPath = currentPath.parent.absolute()
    rootPath = projectPath.parent.absolute()
    if param == "project":
        return projectPath
    elif param == "root":
        return rootPath
    else:
        raise ValueError("Param must be either 'project' or 'root'")