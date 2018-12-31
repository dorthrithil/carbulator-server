from dateutil import parser


def float_or_null(s):
    if s == '':
        return None
    return float(s)


def moment(s):
    parsed = parser.parse(s)
    if not parsed:
        raise ValueError('Could not parse datetime')
    return parsed
