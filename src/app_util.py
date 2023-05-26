import ast
from functools import wraps
from urllib.parse import parse_qsl, urlparse


def dash_kwarg(inputs, extra_args={}):
    def accept_func(func):
        @wraps(func)
        def wrapper(*args):
            input_names = [item.component_id for item in inputs]
            kwargs_dict = dict(zip(input_names, args))
            kwargs_dict.update(extra_args)
            return func(**kwargs_dict)

        return wrapper

    return accept_func


def apply_default_value(params):
    def wrapper(func):
        def apply_value(*args, **kwargs):
            if "id" in kwargs and kwargs["id"] in params:
                # If raw value as string, otherwise parse as Python object (list etc)
                try:
                    kwargs["value"] = ast.literal_eval(params[kwargs["id"]])
                except Exception:
                    kwargs["value"] = params[kwargs["id"]]

            return func(*args, **kwargs)

        return apply_value

    return wrapper


def parse_state(url):
    parse_result = urlparse(url)
    params = parse_qsl(parse_result.query)
    state = dict(params)
    return state
