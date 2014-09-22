import datetime

from django.test import TestCase

from survey.tests.factories import SurveyFactory
from survey.models import Survey, Result, Question, Answer, Page


def create_surveys(num=5):
    return (SurveyFactory() for i in xrange(1, num+1))


class SurveyTest(TestCase):
    fixtures = ['survey.json']

    def test_shorten_description(self):
        s = Survey.objects.get(pk=1)
        description = s.shorten_description(6)

        self.assertEqual(description, 'Thi...')

    def test_shorten_description_smaller(self):
        s = Survey.objects.get(pk=1)
        s.description = 'Short'
        description = s.shorten_description(6)

        self.assertEqual(description, 'Short')

    def test_save_modified_time(self):
        s = Survey(name='Survey')
        minute_slice = slice(0, 17)
        time = str(datetime.datetime.now())
        s.save()
        saved_time = str(s.created_at)
        self.assertEqual(saved_time[minute_slice], time[minute_slice])


class PageTest(TestCase):
    fixtures = ['survey.json']

    def test_get_next_page(self):
        next_page = Page.objects.get_next_page(1, 1)
        self.assertEqual(2, next_page)

    def test_get_next_page_last(self):
        next_page = Page.objects.get_next_page(1, 2)
        self.assertIsNone(next_page)


class AnswerTest(TestCase):
    fixtures = ['survey.json']

    def test_get_score_sum(self):
        # 1->-5, 4->0, 8->10, 9->1, 13->0
        score = Answer.objects.get_score_sum([1, 4, 8, 9, 13])
        self.assertEqual(score, 6)


class ResultTest(TestCase):
    fixtures = ['survey.json']

    def test_get_result(self):
        result = Result.objects.get_result(survey_id=1, score=-5)

        self.assertIsInstance(result, Result)
        self.assertEqual(result.min_score, -9)
        self.assertEqual(result.max_score, 0)

    def test_get_result_limit(self):
        result = Result.objects.get_result(survey_id=1, score=0)

        self.assertIsInstance(result, Result)
        self.assertEqual(result.min_score, 0)
        self.assertEqual(result.max_score, 14)

    def test_get_result_above(self):
        result = Result.objects.get_result_above(survey_id=1, score=10)

        self.assertIsInstance(result, Result)
        self.assertEqual(result.max_score, 34)
        self.assertEqual(result.min_score, 14)

    def test_get_result_above_none(self):
        result = Result.objects.get_result_above(survey_id=1, score=40)

        self.assertIsNone(result)

    def test_get_result_below(self):
        result = Result.objects.get_result_below(survey_id=1, score=1)

        self.assertIsInstance(result, Result)
        self.assertEqual(result.max_score, 0)
        self.assertEqual(result.min_score, -9)

    def test_get_result_below_none(self):
        result = Result.objects.get_result_below(1, score=0)

        self.assertIsNone(result)
