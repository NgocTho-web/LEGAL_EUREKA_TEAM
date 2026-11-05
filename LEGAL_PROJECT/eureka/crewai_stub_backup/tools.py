def tool(*args, **kwargs):
    def decorator(func):
        return func

    if args and callable(args[0]) and len(args) == 1 and not kwargs:
        return args[0]
    return decorator


__all__ = ["tool"]
