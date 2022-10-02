"""
Slide info holder
"""


class Slide(object):
    """This class defines a single slide. It operates on mistune's lexed
    tokens from the input markdown
    """

    def __init__(self, tokens, number=0):
        """Create a new Slide instance with the provided tokens

        :param list tokens: A list of mistune tokens
        :param int number: The slide number
        """
        self.tokens = tokens
        self.number = number
