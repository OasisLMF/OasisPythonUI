def validate_not_none(param, paramName='parameter'):
    if param is None:
        return False, f'{paramName} is not set.'
    return True, ""

def validate_name(name, paramName="Name"):
    if not name or len(name) == 0:
        return False, f"{paramName} is required."
    return True, ""

def validate_key_vals(df, key, vals):
    if df is not None and df[key] in vals:
        return True, ""
    return False, f"{key} has incorrect value."

def validate_key_is_not_null(df, col):
    if df[col] is None:
        return False, f"{col} is None."
    return True, ""

def process_validations(validations):
    valid = True
    msg = ''

    for validation in validations:
        vfunc, vargs = validation
        status, msg = vfunc(*vargs)
        if not status:
            valid = False
            break
    return valid, msg
