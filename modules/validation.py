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


class Validation:
    def __init__(self, message=""):
        self.message = message

    @staticmethod
    def validation_func():
        return True

    def set_message(self, message):
        self.message = message
        return self.message

    def validate(self, *args, **kwargs):
        valid =  self.validation_func(*args, **kwargs)

        if not valid:
            raise ValidationError(self.message)

        return True

    def is_valid(self, *args, **kwargs):
        return self.validation_func(*args, **kwargs)


class NameValidation(Validation):
    def __init__(self, pname="Parameter"):
        self.message = f"{pname} is required"
        super().__init__(self.message)

    @staticmethod
    def validation_func(name):
        if not name or len(name) == 0:
            return False
        return True


class NotNoneValidation(Validation):
    def __init__(self, pname="Parameter"):
        self.message = f"{pname} is not set"
        super().__init__(self.message)

    @staticmethod
    def validation_func(param):
        if param is None:
            return False
        return True


class KeyValueValidation(Validation):
    def __init__(self, pname="Parameter"):
        self.message = f"{pname} has incorrect value"
        super().__init__(self.message)

    @staticmethod
    def validation_func(map, key, value):
        return map[key] == value


class KeyInValuesValidation(Validation):
    def __init__(self, pname="Parameter"):
        self.message = f"{pname} has incorrect value"
        super().__init__(self.message)

    @staticmethod
    def validation_func(map, key, value_list):
        return map[key] in value_list


class ValidationGroup:
    def __init__(self, validations=None, args=None):
        if validations is None:
            validations = []
        if args is None:
            args = []

        self.validation_stack = validations
        self.arg_stack = args
        self.message = ""

    def validate(self):
        for validation, val_args in zip(self.validation_stack, self.arg_stack):
            validation.validate(val_args)
        return True

    def is_valid(self):
        for validation, val_args in zip(self.validation_stack, self.arg_stack):
            if not validation.is_valid(*val_args[0], **val_args[1]):
                self.message = validation.message
                return False
        return True

    def add_validation(self, validation, *args, **kwargs):
        self.validation_stack.append(validation)
        self.arg_stack.append((args, kwargs))
        return self


class ValidationError(Exception):
    """
    Custom exception class for validation errors.

    Attributes
    ----------
        message: explanation of error
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
