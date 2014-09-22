import logging

from django.db import connection


logger = logging.getLogger('survey-sql')


class SqlLoggingMiddleware(object):
    @staticmethod
    def process_response(request, response):
        """Log all queries executed in the current request.

        :param request:
        :param response:
        :return:
        """
        for query in connection.queries:
            message = '({}) {}'.format(query['time'], query['sql'])
            logger.debug(message)
        return response