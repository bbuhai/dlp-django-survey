from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore

from survey.models import Result


class ListViewTest(TestCase):
    fixtures = ['survey.json']

    def setUp(self):
        self.client = Client()

    def test_home(self):
        response = self.client.get('/survey/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.context['surveys']),
            3
        )

    def test_list_page_limit(self):
        response = self.client.get('/survey/?page=2')
        num_surveys = len(response.context['surveys'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(num_surveys, 2)

    def test_list_default_first_page(self):
        response = self.client.get('/survey/?page=notanumber')
        num_surveys = len(response.context['surveys'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(num_surveys, 3)

    def test_list_empty_page_replaced_with_last(self):
        response = self.client.get('/survey/?page=10')
        num_surveys = len(response.context['surveys'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(num_surveys, 2)


class SurveyViewTest(TestCase):
    fixtures = ['survey.json']

    def setUp(self):
        self.c = Client()

    def test_get_survey_first_page(self):
        response = self.c.get('/survey/1')
        num_questions = len(response.context['questions'])
        next_page = response.context['next_page']
        current_page = response.context['current_page']
        survey = response.context['survey']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(current_page, 1)
        self.assertEqual(num_questions, 3)
        self.assertEqual(next_page, 2)
        self.assertEqual(survey.id, 1)

    def test_post_survey_first_page_correct(self):
        data = {
            'question[1]': (1, 2),
            'question[2]': 5,
            'question[3]': (7, 8),
        }
        response = self.c.post('/survey/1', data)
        answers_ids = response.client.session['answers']
        page = response.client.session['survey_page']
        self.assertEqual(response.status_code, 302)
        self.assertEqual(answers_ids, [1, 2, 5, 7, 8])
        self.assertEqual(page, 2)

    def test_post_survey_first_page_missing_answers(self):
        data = {
            'question[1]': (1, 2),
            'question[2]': 5
        }
        response = self.c.post('/survey/1', data)
        answer_ids = response.context['answered']
        next_page = response.context['next_page']
        unanswered_ids = response.context['unanswered']

        self.assertEqual(next_page, 2)
        self.assertEqual(answer_ids, [1, 2, 5])
        self.assertEqual(unanswered_ids, [3])

    def test_get_survey_redirect_back(self):
        response = self.c.get('/survey/1/page/2', follow=True)
        page = response.context['current_page']
        next_page = response.context['next_page']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(page, 1)
        self.assertEqual(next_page, 2)

    def test_post_survey_second_page(self):
        data = {
            'question[4]': 10,
            'question[5]': 12
        }
        session = SessionStore()
        session['survey_page'] = 2
        session['answers'] = [1, 2, 5, 7, 8]
        session.save()
        self.c.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        response = self.c.post('/survey/1/page/2', data, follow=True)
        answers = response.client.session['answers']
        score = response.client.session['score']
        result = response.context['result']

        self.assertTrue('survey_page' not in response.client.session)
        self.assertEqual(answers, [1, 2, 5, 7, 8, 10, 12], 'Invalid answer ids in session.')
        self.assertEqual(score, 8, 'Score not correct.')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(result, Result)


class ResultViewTest(TestCase):
    fixtures = ['survey.json']

    def setUp(self):
        self.c = Client()

    def test_get_closest_alternative(self):
        session = SessionStore()
        session['score'] = 8
        session['answers'] = [1, 2, 5, 7, 8, 10, 12]
        session.save()
        self.c.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        response = self.c.get('/survey/1/closest_path')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('better' in response.context)
        self.assertTrue('worse' in response.context)

    def test_get_closest_alternative_no_score(self):
        # no score on session
        response = self.c.get('/survey/1/closest_path')

        self.assertEqual(response.status_code, 404)
