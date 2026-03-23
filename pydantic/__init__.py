from __future__ import annotations

from copy import deepcopy
from typing import Any, get_args, get_origin, get_type_hints

class FieldInfo:
    def __init__(self, default=..., default_factory=None, gt=None, ge=None):
        self.default = default
        self.default_factory = default_factory
        self.gt = gt
        self.ge = ge


def Field(default=..., **kwargs):
    return FieldInfo(default=default, **kwargs)


def model_validator(*, mode='after'):
    def decorator(func):
        func.__model_validator__ = True
        return func
    return decorator


class BaseModel:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        validators = []
        for name, value in cls.__dict__.items():
            if getattr(value, '__model_validator__', False):
                validators.append(value)
        cls.__validators__ = validators

    def __init__(self, **data):
        annotations = {}
        for base in reversed(self.__class__.mro()):
            try:
                annotations.update(get_type_hints(base))
            except Exception:
                annotations.update(getattr(base, '__annotations__', {}))
        for field, annotation in annotations.items():
            if field in data:
                value = data[field]
            else:
                default = getattr(self.__class__, field, ...)
                if isinstance(default, FieldInfo):
                    if default.default_factory is not None:
                        value = default.default_factory()
                    elif default.default is not ...:
                        value = deepcopy(default.default)
                    else:
                        raise TypeError(f'Missing field: {field}')
                elif default is not ...:
                    value = deepcopy(default)
                else:
                    raise TypeError(f'Missing field: {field}')
            setattr(self, field, self._convert(annotation, value))
            self._validate_field(field, getattr(self.__class__, field, None), getattr(self, field))
        for validator in getattr(self.__class__, '__validators__', []):
            result = validator(self)
            if result is not None:
                self = result

    @classmethod
    def _convert(cls, annotation, value):
        origin = get_origin(annotation)
        args = get_args(annotation)
        if value is None:
            return value
        if origin in (list, list[Any]):
            inner = args[0] if args else Any
            return [cls._convert(inner, item) for item in value]
        if origin is dict:
            key_t, val_t = args if len(args) == 2 else (Any, Any)
            return {cls._convert(key_t, k): cls._convert(val_t, v) for k, v in value.items()}
        if origin is tuple:
            inner = args[0] if args else Any
            return tuple(cls._convert(inner, item) for item in value)
        if origin is not None and type(None) in args:
            non_none = [arg for arg in args if arg is not type(None)]
            if non_none:
                return cls._convert(non_none[0], value)
            return value
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            if isinstance(value, annotation):
                return value
            return annotation(**value)
        return value

    def _validate_field(self, field, field_def, value):
        if isinstance(field_def, FieldInfo):
            if field_def.gt is not None and not (value > field_def.gt):
                raise ValueError(f'{field} must be > {field_def.gt}')
            if field_def.ge is not None and not (value >= field_def.ge):
                raise ValueError(f'{field} must be >= {field_def.ge}')

    def model_dump(self, mode=None):
        result = {}
        annotations = {}
        for base in reversed(self.__class__.mro()):
            try:
                annotations.update(get_type_hints(base))
            except Exception:
                annotations.update(getattr(base, '__annotations__', {}))
        for field in annotations:
            result[field] = self._dump_value(getattr(self, field), mode)
        return result

    @classmethod
    def _dump_value(cls, value, mode=None):
        if isinstance(value, BaseModel):
            return value.model_dump(mode=mode)
        if isinstance(value, list):
            return [cls._dump_value(item, mode=mode) for item in value]
        if isinstance(value, dict):
            return {k: cls._dump_value(v, mode=mode) for k, v in value.items()}
        if mode == 'json' and hasattr(value, 'isoformat'):
            return value.isoformat()
        return value
