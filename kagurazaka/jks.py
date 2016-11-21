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
            f(*args, **kws)
        finally:
            close(*arguments)
    return final_colse_decorator
