import strictyaml as sy
from strictyaml import constants
from strictyaml.exceptions import YAMLSerializationError


def __bool_is_true_false():
    # make to_yaml write true, false instead yes, no
    def bool_to_yaml(_, data):
        if not isinstance(data, bool):
            if str(data).lower() in constants.BOOL_VALUES:
                return data
            else:
                raise YAMLSerializationError("Not a boolean")
        else:
            return "true" if data else "false"

    sy.Bool.to_yaml = bool_to_yaml


__bool_is_true_false()
