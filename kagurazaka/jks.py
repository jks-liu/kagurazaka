#!/usr/bin/env python3
"""
Contain useful utils
"""

import decorator


def final_close(close, *arguments):
    """Decorator for make sure close is called finally"""
    @decorator.decorator
    def final_colse_decorator(f, *args, **kws):
        try:
            return f(*args, **kws)
        finally:
            close(*arguments)
    return final_colse_decorator


def force_arguments_type(*types):
    """Decorator which try to convert arguments type"""
    @decorator.decorator
    def force_arguments_type_decorator(f, *args, **kws):
        return f(*[typ(arg) for (typ, arg) in zip(types, args)], **kws)
    return force_arguments_type_decorator


def unit(anything):
    """Do nothing type converter

    Used for force_arguments_type"""
    return anything
