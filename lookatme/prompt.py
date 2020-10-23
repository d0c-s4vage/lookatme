"""
Basic user-prompting helper functions
"""


def yes(msg):
    """Prompt the user for a yes/no answer. Returns bool
    """
    answer = input("{} (Y/N) ".format(msg))
    return answer.strip().lower() in ["y", "yes"]
