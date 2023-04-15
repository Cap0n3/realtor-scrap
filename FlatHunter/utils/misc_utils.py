from pathlib import Path

def getPath(param):
    """
    Get project's path.
    Returns
    -------
    _type_
        _description_
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