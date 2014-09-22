from django.contrib import admin
from survey.models import (Survey, Question, Answer, Result, Page)
from django.db import models
from django.forms import Textarea, TextInput


class ResultInLine(admin.TabularInline):
    model = Result
    extra = 2
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 70})}
    }


class PageInline(admin.TabularInline):
    model = Page
    extra = 2


class SurveyAdmin(admin.ModelAdmin):
    inlines = [PageInline, ResultInLine]
    fieldsets = [
        ('Survey details', {'fields': ['name', 'description']})
    ]
    list_display = ('name', 'created_at')
    search_fields = ['name']

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': 80})},
        models.TextField: {'widget': Textarea(attrs={'rows': 8, 'cols': 100})}
    }


class AnswerInline(admin.TabularInline):
    readonly_fields = ['id']
    model = Answer
    extra = 2

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': 100})}
    }


class QuestionAdmin(admin.ModelAdmin):
    readonly_fields = ['id']
    fields = ['page', 'question_text', 'position', 'type', 'id']
    inlines = [AnswerInline]
    list_display = ('id', 'question_text', 'page', 'position')
    search_fields = ['question_text']

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': 150})}
    }


admin.site.register(Survey, SurveyAdmin)
admin.site.register(Question, QuestionAdmin)