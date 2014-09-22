from itertools import count

import factory

from survey.models import Survey, Page

_survey_id = iter(count(start=1))


def _gen_survey(text):
    return text.format(next(_survey_id))


class SurveyFactory(factory.DjangoModelFactory):
    class Meta:
        model = Survey
    name = 'Survey #x'
    description = 'Generated survey #x'


class PageFactory(factory.DjangoModelFactory):
    class Meta:
        model = Page

