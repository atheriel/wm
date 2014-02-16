class SingletonMetaclass(type):
    """
    This class is intended to be used as a metatype for classes that follow the
    singleton pattern. It maintains a single copy of the object.
    """
    def __init__(cls, name, bases, dict):
        super(SingletonMetaclass, cls).__init__(cls, bases, dict)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SingletonMetaclass, cls).__call__(*args, **kwargs)
        return cls._instance
