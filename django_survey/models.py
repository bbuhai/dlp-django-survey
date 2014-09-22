import datetime

from django.db import models

from survey import managers


class Survey(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(db_index=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = datetime.datetime.now()
        super(Survey, self).save(*args, **kwargs)

    def shorten_description(self, length=160):
        max_length = length - 3
        if len(self.description) > length:  # 3 for the ellipses
            return self.description[:max_length] + '...'
        return self.description

    class Meta:
        ordering = ['-created_at']


class Page(models.Model):
    page_num = models.PositiveIntegerField()
    survey = models.ForeignKey(Survey)

    objects = managers.DefaultPageManager()

    def __unicode__(self):
        return "Pg {} from {}".format(self.page_num, self.survey)

    def __str__(self):
        return self.__unicode__()

    class Meta:
        unique_together = ('page_num', 'survey')


class Question(models.Model):
    SINGLE = 'radio'
    MULTIPLE = 'checkbox'
    TYPE_IN_CHOICES = (
        (SINGLE, 'Single answer'),
        (MULTIPLE, 'Multiple answers')
    )

    page = models.ForeignKey(Page)
    question_text = models.CharField(max_length=300)
    position = models.IntegerField(help_text="Question order")
    type = models.CharField(max_length=20, choices=TYPE_IN_CHOICES, default=MULTIPLE)

    def __unicode__(self):
        return self.question_text[:10]

    def __str__(self):
        return self.__unicode__()

    class Meta:
        ordering = ['position']


class Answer(models.Model):
    question = models.ForeignKey(Question)
    answer_text = models.CharField(max_length=200)
    score = models.IntegerField()

    objects = managers.DefaultAnswerManager()

    def __unicode__(self):
        return self.answer_text[:10]

    def __str__(self):
        return self.__unicode__()


class Result(models.Model):
    survey = models.ForeignKey(Survey)
    summary = models.CharField(max_length=300)
    description = models.TextField(null=True, blank=True)
    min_score = models.IntegerField()
    max_score = models.IntegerField()

    objects = managers.DefaultResultManager()

    def __unicode__(self):
        return self.summary[:10]

    def __str__(self):
        return self.__unicode__()