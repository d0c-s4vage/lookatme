"""
Slide info holder
""" 


import mistune


class Slide(object):
    """This class defines a single slide. It operates on mistune's lexed
    tokens from the input markdown
    """

    def __init__(self, tokens, md=None, number=0):
        """Create a new Slide instance with the provided tokens

        :param list tokens: A list of mistune tokens
        :param mistune.Markdown md: The markdown instance to use
        :param int number: The slide number
        """
        self.tokens = tokens
        self.md = md or mistune.Markdown()
        self.number = number
