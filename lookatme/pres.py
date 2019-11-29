"""
Defines Presentation specific objects
"""


import mistune


class Presentation(object):
    """Defines a presentation
    """
    def __init__(self, meta, slides):
        """Creates a new Presentation
        """
        self.meta = meta
        self.slides = slides


class PresentationMeta(object):
    """Metadata for the presentation. This holds the parsed YAML header.
    """
    def __init__(self, title=None, author=None, date=None, options=None):
        """Create a new PresentationMeta instance
        """
        self.title = title
        self.author = author
        self.date = date
        self.options = options


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
