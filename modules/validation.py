def validate_not_none(param, paramName='parameter'):
    if param is None:
        return False, f'{paramName} is not set'
    return True, ""

def validate_name(name):
    if not name or len(name) == 0:
        return False, "Name is required"
    return True, ""
