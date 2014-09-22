from django.db import models

from survey.utils import get_first_value


class DefaultPageManager(models.Manager):
    def get_next_page(self, survey_id, page_num):
        """Returns the next page number for a survey that is bigger than the current one.

        :param survey_id:
        :param page_num:
        :return: int or None
        """
        query = self.filter(survey=survey_id, page_num__gt=page_num).order_by('page_num')
        page = get_first_value(query)
        return page.page_num if page else None


class DefaultAnswerManager(models.Manager):
    def get_score_sum(self, answer_ids):
        """Sum over a bunch of answers' score.

        :param answer_ids:
        :return:
        """
        q = self.filter(id__in=answer_ids).aggregate(total=models.Sum('score'))
        return q['total']


class DefaultResultManager(models.Manager):
    def get_result(self, survey_id, score):
        """Returns the result object (or None if not found) for a specific score and survey.

        :param survey_id:
        :param score:
        :return:
        """
        q = self.filter(survey=survey_id, max_score__gt=score, min_score__lte=score)
        return get_first_value(q)

    def get_result_above(self, survey_id, score):
        """Returns the first result which has min_score bigger that the current user score.

        :param survey_id:
        :param score:
        :return:
        """
        q = self.filter(survey=survey_id, min_score__gt=score).order_by('min_score')
        return get_first_value(q)

    def get_result_below(self, survey_id, score):
        """Returns the first result which has max_score smaller that the current user score.

        :param survey_id:
        :param score:
        :return:
        """
        q = self.filter(survey=survey_id, max_score__lt=score).order_by('-min_score')
        return get_first_value(q)