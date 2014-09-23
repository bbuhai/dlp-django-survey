from math import ceil
import logging

from django.shortcuts import (render, HttpResponseRedirect,
                              Http404, get_object_or_404)
from django.core.urlresolvers import reverse
from django.views.generic.base import View
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator

from survey.models import Survey, Question, Answer, Page, Result
from closealternative import compute_closest_alternatives, AnsTuple


logger = logging.getLogger(__name__)


class ListView(View):
    template_name = 'survey/list.html'

    def get(self, request):
        """Display a list with all the surveys available.

        The results are paged.

        :param request:
        :return:
        """
        page = request.GET.get('page', 1)
        limit = 3

        all_surveys = Survey.objects.all()
        paginator = Paginator(all_surveys, limit)

        try:
            surveys = paginator.page(page)
        except PageNotAnInteger:
            surveys = paginator.page(1)
        except EmptyPage:
            surveys = paginator.page(paginator.num_pages)

        start_at = (surveys.number - 1) * limit + 1

        context = {
            'surveys': surveys,
            'start_at': start_at
        }

        return render(request, self.template_name, context)


def test_me(user):
    return True


class SurveyView(View):
    template_name = 'survey/survey.html'
    SURVEY_PAGE = 'survey_page'

    @method_decorator(user_passes_test(test_func=test_me))
    def dispatch(self, request, *args, **kwargs):
        return super(SurveyView, self).dispatch(request, *args, **kwargs)

    def get(self, request, survey_id, page=1):
        """Renders a specific survey page.

        Store in session the survey_page (current page) and the ids of the answers.
        The survey_page is used to restrict the user (skip ahead in the survey).
        The answer ids is used later to compute a close result alternative.

        :param request:
        :param survey_id: numeric
        :param page: numeric
        :return:
        """
        survey = get_object_or_404(Survey, pk=survey_id)
        page = int(page)
        session_page = request.session.get(self.SURVEY_PAGE, 1)

        if page != session_page:
            return HttpResponseRedirect(reverse('survey:survey', args=(survey_id, session_page)))

        if page == 1:
            request.session['answers'] = []

        questions = Question.objects.filter(page__page_num=page, page__survey=survey_id)
        next_page = Page.objects.get_next_page(survey_id, page)

        context = {
            'survey': survey,
            'questions': questions,
            'next_page': next_page,
            'current_page': page
        }
        return render(request, self.template_name, context)

    def post(self, request, survey_id, page=1):
        """ Handle user survey answers.

        Make sure that all questions were answered.
        If all are answered then proceed to the next page or to the results page.
        If not, redisplay the page, with the questions marked.

        :param request:
        :param survey_id: numeric
        :param page: numeric
        :return:
        """
        questions_on_page = Question.objects.filter(page__page_num=page, page__survey=survey_id)
        survey = get_object_or_404(Survey, pk=survey_id)
        unanswered_q = []
        answered_ids = []
        answers_so_far = request.session.get('answers', [])
        for q in questions_on_page:
            answer_ids_str = request.POST.getlist('question[{}]'.format(q.id))
            try:
                answer_ids = map(int, answer_ids_str)
            except ValueError as e:
                answer_ids = []
                unanswered_q.append(q.id)
                logger.info(e)

            if answer_ids:
                answers_so_far += answer_ids
                answered_ids += answer_ids
            else:
                unanswered_q.append(q.id)
        next_page = Page.objects.get_next_page(survey_id, page)

        if len(unanswered_q) == 0:
            request.session['answers'] = answers_so_far
            if next_page:
                # there is another page
                request.session[SurveyView.SURVEY_PAGE] = next_page
                return HttpResponseRedirect(reverse('survey:survey', args=(survey_id, next_page)))

            else:
                # finished the survey
                del request.session[SurveyView.SURVEY_PAGE]
                return HttpResponseRedirect(reverse('survey:result', args=(survey_id,)))
        # some questions were not answered
        # so we're going to redisplay the same page
        context = {
            'unanswered': unanswered_q,
            'answered': answered_ids,
            'survey': survey,
            'next_page': next_page,
            'questions': questions_on_page,
            'current_page': page
        }
        return render(request, self.template_name, context)


class ResultView(View):
    template_name = 'survey/result.html'

    def get(self, request, survey_id):
        answer_ids = request.session.get('answers', [])
        score = Answer.objects.get_score_sum(answer_ids)
        request.session['score'] = score

        result = Result.objects.get_result(survey_id, score)
        context = {
            'result': result,
            'score': score,
            'survey_id': survey_id
        }
        logging.debug('score: {}'.format(score))
        return render(request, self.template_name, context)


class ClosestPath(View):
    template_name = 'survey/closest_path.html'

    def get(self, request, survey_id):
        try:
            score = int(request.session.get('score', None))
        except TypeError:
            raise Http404()
        next_result = Result.objects.get_result_above(survey_id, score)
        prev_result = Result.objects.get_result_below(survey_id, score)
        given_ans_ids = request.session.get('answers')

        pages = Page.objects.filter(survey=survey_id)
        other_ans = {}
        given_ans = {}
        # organize the answers by page and question
        # and keep them split into answers the user has submitted
        # and into answers the user has not submitted for that particular page and question
        # this is useful when computing score improvements
        for page in pages:
            answers = Answer.objects.filter(question__page=page)
            given_ans[page.id] = {}
            other_ans[page.id] = {}
            for ans in answers:
                a = AnsTuple(id=ans.id, score=ans.score)
                other_ans[page.id][ans.question_id] = other_ans[page.id].get(ans.question_id, [])
                given_ans[page.id][ans.question_id] = given_ans[page.id].get(ans.question_id, [])

                if ans.id in given_ans_ids:
                    given_ans[page.id][ans.question_id].append(a)
                else:
                    other_ans[page.id][ans.question_id].append(a)

        better, worse = compute_closest_alternatives(score=score,
                                                     next_result=next_result,
                                                     prev_result=prev_result,
                                                     answers=given_ans,
                                                     other_answers=other_ans)
        context = {
            'better': better,
            'worse': worse
        }
        return render(request, self.template_name, context)
