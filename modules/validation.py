def validate_not_none(param, paramName='parameter'):
    if param is None:
        return False, f'{paramName} is not set'
    return True, ""

def validate_name(name):
    if not name or len(name) == 0:
        return False, "Name is required"
    return True, ""

def validate_col_val(df, col_name, val):
    if df[col_name] == val:
        return True, ""
    return False, "Column {col_name} has incorrect value."

def validate_key_is_not_null(df, col):
    if df[col] is None:
        return False, f"{col} is None"
    return True, ""
