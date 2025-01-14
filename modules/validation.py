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

class Validator:
    def __init__(self, valid_func, error_func=None):
        self.vfunc = valid_func
        self.message = ""

        if error_func is None:
            self.error_func = lambda _:  "Validation Failed"

    def validate(self, val_args=None, error_args=None):
        valid =  self.vfunc(**val_args)

        if not valid:
            self.message = self.error_func(error_args)

        return valid


class GroupValidation:
    def __init__(self, validations=[], val_args=[], err_args=[]):
        self.validations = validations
        self.val_args = val_args
        self.err_args = err_args
        self.message = ""
        # Group validations + args into a stack?

    def validate(self):
        for validation, val_arg, err_arg in zip(self.validations, self.val_args, self.err_args):
            valid = validation.validate(val_arg, err_arg)
            if not valid:
                self.message = validation.message
                return False
        return True

    def add_validation(validation, val_arg=None, err_arg=None):
        # Method to add a validation to the group
        pass
