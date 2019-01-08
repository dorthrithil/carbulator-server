from flask_restful import Api
from jwt import ExpiredSignatureError

from src.messages.messages import UNAUTHORIZED


class ExceptionAwareApi(Api):
    def handle_error(self, e):
        """
        Tries to do custom exception handling for known exceptions. If this failed, the standard error handling routine
        is used.
        :param e: Error Instance.
        :return: Error HTTP response.
        """
        if isinstance(e, ExpiredSignatureError):
            code = 401
            data = {'code': code, 'message': UNAUTHORIZED}
        else:
            # Did not match a custom exception, continue normally
            return super(ExceptionAwareApi, self).handle_error(e)
        return self.make_response(data, code)
