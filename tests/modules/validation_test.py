"""
Test file for modules/validation.py.
"""
from modules.validation import IsNoneValidation, KeyInValuesValidation, KeyValueValidation, LenValidation, NameValidation, NotNoneValidation, ValidationError, ValidationGroup
import pytest

class TestBuiltinValidations:
    def test_name_validation(self):
        validation = NameValidation(pname="TestParam")

        isvalid = validation.is_valid(None)
        assert not isvalid
        assert validation.get_message() == 'TestParam is required'

        with pytest.raises(ValidationError):
            validation.validate(None)

        isvalid = validation.is_valid('')
        assert not isvalid
        assert validation.get_message() == 'TestParam is required'

        isvalid = validation.is_valid('Test')
        assert isvalid
        assert validation.get_message() is None

    def test_not_none_validation(self):
        validation = NotNoneValidation(pname="TestParam")

        isvalid = validation.is_valid(None)
        assert not isvalid
        assert validation.get_message() == "TestParam is not set"

        isvalid = validation.is_valid(True)
        assert isvalid
        assert validation.get_message() is None

    def test_is_none_validation(self):
        validation = IsNoneValidation(pname="TestParam")

        isvalid = validation.is_valid(True)
        assert not isvalid
        assert validation.get_message() == "TestParam is set"

        isvalid = validation.is_valid(None)
        assert isvalid
        assert validation.get_message() is None

    def test_key_value_validation(self):
        validation = KeyValueValidation(pname="TestParam")

        isvalid = validation.is_valid({'test': 1}, 'test', 1)
        assert isvalid

        isvalid = validation.is_valid({'test': 2}, 'test', 1)
        assert not isvalid
        assert validation.get_message() == "TestParam has incorrect value"

    def test_key_in_value_validation(self):
        validation = KeyInValuesValidation(pname="TestParam")

        isvalid = validation.is_valid({'test': 1}, 'test', [1, 2, 3, 4])
        assert isvalid

        isvalid = validation.is_valid({'test': 5}, 'test', [1, 2, 3, 4])
        assert not isvalid
        assert validation.get_message() == "TestParam has incorrect value"

    def test_len_validation(self):
        validation = LenValidation(pname="TestParam")

        isvalid = validation.is_valid([0, 1, 2, 3], 4)
        assert isvalid

        isvalid = validation.is_valid([0, 1, 2, 3], 5)
        assert not isvalid
        assert validation.get_message() == "TestParam is incorrect size"


testParams = [
    ({'test': 1}, True, None),
    (None, False, "TestParam is not set"),
    ({'test': 5}, False, "TestParam has incorrect value")
]

@pytest.mark.parametrize("param,valid,msg", testParams)
def test_validation_group(param, valid, msg):
    validations = ValidationGroup()
    validations.add_validation(NotNoneValidation('TestParam'), param)
    validations.add_validation(KeyInValuesValidation('TestParam'), param, 'test', [1, 2, 3, 4])

    isvalid = validations.is_valid()
    output_msg = validations.get_message()

    assert isvalid == valid
    assert msg == output_msg
