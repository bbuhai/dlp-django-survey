from django.conf.urls import patterns, url, include
from django.contrib.auth.views import login

from survey import views

survey_patterns = patterns('',
    url(r'^$', views.SurveyView.as_view(), name='survey'),
    url(r'^/page/(?P<page>\d+)$', views.SurveyView.as_view(), name='survey'),
    url(r'^/result$', views.ResultView.as_view(), name='result'),
    url(r'^/closest_path$', views.ClosestPath.as_view(), name='closest')
)

urlpatterns = patterns('',
    url(r'^$', views.ListView.as_view(), name='list'),
    url(r'^(?P<survey_id>\d+)', include(survey_patterns)),
)