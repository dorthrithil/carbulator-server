from flask_restful import fields


class TimedeltaDays(fields.Raw):
    """
    Marshalling class for timedaltas. Returns the timedelta as numver of days.
    """

    def format(self, value):
        """
        Format's the value that should get marshalled.
        :param value: Value for format.
        :return: Formatted value (Number of days).
        """
        return value.days
