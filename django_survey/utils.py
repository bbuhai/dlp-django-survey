

def get_first_value(q_set):
    """Get the first value from a dict, or None if empty.

    :param q_set:
    :return:
    """
    try:
        return q_set[0]
    except IndexError:
        return None