

class ModelPreconditionNotMet(Exception):
    """
    A custom exception indicating that a model precondition was
    not met in trying to save something to couch.
    """
    pass