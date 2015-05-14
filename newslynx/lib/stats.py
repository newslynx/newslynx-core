
def parse_number(n):
    """
    Parse a number
    """
    try:
        return float(n)
    except ValueError:
        try:
            return int(n)
        except ValueError:
            raise ValueError
