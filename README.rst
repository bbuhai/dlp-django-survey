django-survey
=============

A basic django app that can be used to make surveys.


Quick start:

1. Install the app::

    pip install <path_to_django_survey_tar_gz_file>

2. Add `django_survey` in the `INSTALLED_APPS` settings::

    INSTALLED_APPS = (
        ...
        'django_survey',
    )

3. Include the django_survey URLconf in you project urls.py like this::

    url(r'^survey/', include('survey.urls', namespace='survey')),

4. Run::

    python manage.py syncdb
    python manage.py loaddata survey.json

5. Go to */survey/* and complete the first survey.