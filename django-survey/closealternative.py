"""
The main idea/logic:

The user gets a score when he finishes the survey.
That score corresponds to a Result objects, with a min_score and a max_score.

Steps:
1. Retrieve the Result objects that are right after and right before the current one.
"After" means Result1.max_score >= Result2.min_score,
"Before" means Result0.max_score <= Result1.min_score,
    where Result1 is the obtained result
    and Result2 is the "next result" and Result0 is the previous result

2. Find what it would take to get from the current user answers to the *next* result.
    a. Take each question with its answers and make a loop from 1 to len(num_answers_in_question)
        This loop value will be the weight value.
        The weight is an object that has associated a value, a score, a page number,
        a question id, a list of answers to remove, and a list of answers to add.

        Inside this loop try all combinations of removing and adding answers to the question.

    b. For each page keep a set changes that improve the score the most by doing 1, 2, 3, 4... changes.
        The score improvement when doing 2 changes must be bigger that doing 1 change (on the same page)

    c. Find out the number of points needed to get to the next Result.

    d. Take the weight objects in ascending order by their value and compute all possible combinations
        that will improve the score enough to reach the number of points needed.

    e. Out of all these possible combinations, pick the one that requires the fewest changes to
        the given user answers.

3. Find what it would take to get from the current user answers to the *previous* result.
    Do the same as above (2) but use a variable higher_is_better that reverses some of the comparisons.
"""

import heapq
import logging
from operator import attrgetter
from collections import namedtuple
from itertools import chain
import copy

from survey.models import Question, Answer


logger = logging.getLogger(__name__)

AnsTuple = namedtuple("AnsTuple", ['id', 'score'])
Weight = namedtuple('Weight', ['val', 'rm', 'add', 'q', 'pg', 'score'])


def compute_closest_alternatives(score, next_result, prev_result, answers, other_answers):
    d = DiscoverPath(score=score,
                     next_result=next_result,
                     prev_result=prev_result,
                     answers=answers,
                     other_answers=other_answers)
    alternative = d.compute()
    return _prepare_result_for_display(alternative)


def _extract_worst(n, lst):
    """Returns the n smallest AnsTuples from a list.
    >>> lst = [AnsTuple(1, -10), AnsTuple(2, 0), AnsTuple(3, 10), AnsTuple(4, -1)]
    >>> _extract_worst(3, lst)
    [AnsTuple(id=1, score=-10), AnsTuple(id=4, score=-1), AnsTuple(id=2, score=0)]
    >>> lst = [AnsTuple(1, 10), AnsTuple(2, 1), AnsTuple(3, 10), AnsTuple(4, -1)]
    >>> _extract_worst(0, lst)
    []
    """
    return heapq.nsmallest(n, lst, key=attrgetter('score'))


def _extract_best(n, lst):
    """Returns the n largest AnsTuples from a list.
    >>> lst = [AnsTuple(1, -10), AnsTuple(2, 0), AnsTuple(3, -20), AnsTuple(4, -1)]
    >>> _extract_best(2, lst)
    [AnsTuple(id=2, score=0), AnsTuple(id=4, score=-1)]
    >>> lst = [AnsTuple(1, 10), AnsTuple(2, 1), AnsTuple(3, 15), AnsTuple(4, -1)]
    >>> _extract_best(0, lst)
    []
    """
    return heapq.nlargest(n, lst, key=attrgetter('score'))


class DiscoverPath(object):
    def __init__(self, score, next_result, prev_result, answers, other_answers):
        """Initializes the object.

        self.routes
            is used to know which path to explore (1 for better, -1 for worse)
        self.higher_is_better
            True when computing possible changes for a better result
            False when computing possible changes for a worse result

        :param score: int
            current user score
        :param next_result: survey.models.Result
        :param prev_result: survey.models.Result
        :param answers: dict
        :param other_answers: dict
        :return:
        """
        self.score = score
        self.next = next_result
        self.prev = prev_result
        self.answers = answers
        self.other_answers = other_answers
        self.routes = []
        self.higher_is_better = True
        if next_result:
            self.routes.append(1)
        if prev_result:
            self.routes.append(-1)
        if not self.routes:
            raise ValueError('No possible path. Next and previous possible results are missing.')

    def compute(self):
        """Searches for better or worse survey results, starting from the current user answers.

        Only one question per page can be changed, and the number of answers changed should be minimal.

        :return: dict {'better': dict, 'worse': dict}
        """
        results = {}
        for route in self.routes:
            if route == 1:
                self.higher_is_better = True
                points_needed = self.next.min_score - self.score
                results['better'] = self._get_changes(points_needed)

            else:
                self.higher_is_better = False
                # + 1 because the interval is [min_score, max_score)
                points_needed = self.score - self.prev.max_score + 1
                results['worse'] = self._get_changes(points_needed)

        return results

    def _get_changes(self, points_needed):
        all_possible_changes = []
        w_q = self._weight_all()
        sorted_weights = {}
        for w, details in w_q.iteritems():
            sorted_weights[w] = sorted(details.itervalues(), key=attrgetter('score'), reverse=self.higher_is_better)

        for w, details in sorted_weights.iteritems():
            i = 0
            length = len(details)
            points_needed_cpy = points_needed
            changes = {}
            while points_needed_cpy > 0 and i < length:
                page = details[i].pg
                if self.higher_is_better:
                    points_needed_cpy -= details[i].score
                else:
                    # details[i].score should be < 0
                    points_needed_cpy += details[i].score

                changes[page] = details[i]
                i += 1
                if points_needed_cpy <= 0:
                    continue
                # here it's necessary to check the previous weights
                # without this, some combinations will be missed
                self._search_lower_weight_values(
                    sorted_weights=sorted_weights,
                    w=w,
                    points_needed=points_needed_cpy,
                    changes=changes,
                    all_changes=all_possible_changes
                )

            if points_needed_cpy <= 0:
                all_possible_changes.append(changes)
        best = self._choose_best(all_possible_changes)
        return best

    def _search_lower_weight_values(self, sorted_weights, w, points_needed, changes, all_changes):
        for prev_weight in range(1, w):
            if prev_weight not in sorted_weights:
                continue
            prev_details = sorted_weights[prev_weight]
            prev_length = len(prev_details)
            points = points_needed
            j = 0
            inner_changes = {}
            while points > 0 and j < prev_length:
                obj = prev_details[j]
                j += 1
                if obj.pg in changes:
                    # already used a question from this page
                    continue
                inner_changes[obj.pg] = obj
                if self.higher_is_better:
                    points -= obj.score
                else:
                    points += obj.score

            if points <= 0:
                changes_copy = copy.copy(changes)
                changes_copy.update(inner_changes)
                all_changes.append(changes_copy)

    @staticmethod
    def _choose_best(all_changes):
        """Out of all possible changes, pick the one with the smallest sum for the weights.

        :param all_changes: list
        :return: dict
        """
        best = None
        fewest_changes = None
        for changes in all_changes:
            s = sum(w.val for w in changes.itervalues())
            if best is None or s < best:
                best = s
                fewest_changes = changes
        return fewest_changes

    def _weight_all(self):
        """Loop though all the pages and questions
        in order to compute weights and changes that improve the score.

        :return:
        """
        w = {}

        for page_id, questions in self.answers.iteritems():
            for q_id, ans in questions.iteritems():
                num_ans = len(ans) + len(self.other_answers[page_id][q_id])
                self._weight_question(num_ans, page_id=page_id, q_id=q_id, all_weights=w)

        return w

    def _weight_question(self, max_weight, page_id, q_id, all_weights):
        for weight in range(1, max_weight + 1):
            best_weight = self._get_best_on_page_for_weight(
                weight=weight,
                page_id=page_id,
                q_id=q_id,
                all_weights=all_weights
            )

            if best_weight:
                all_weights[weight] = all_weights.get(weight, {})
                if not page_id in all_weights[weight]:
                    all_weights[weight][page_id] = best_weight
                    continue
                prev_weight = all_weights[weight][page_id]
                if prev_weight.score < best_weight.score and self.higher_is_better\
                        or prev_weight.score > best_weight.score and not self.higher_is_better:
                    all_weights[weight][page_id] = best_weight

    def _get_best_on_page_for_weight(self, weight, page_id, q_id, all_weights):
        best_weight = None
        for j in range(0, weight+1):
            if self.higher_is_better:
                smallest = _extract_worst(j, self.answers[page_id][q_id])
                largest = _extract_best(abs(weight-j), self.other_answers[page_id][q_id])
            else:
                smallest = _extract_best(j, self.answers[page_id][q_id])
                largest = _extract_worst(abs(weight-j), self.other_answers[page_id][q_id])
            if not smallest and not largest:
                # no changes
                continue
            if len(smallest) + len(largest) != weight:
                continue
            new_set = self._combine_answers(self.answers[page_id][q_id], smallest, largest)

            if not new_set:
                # the question should have an answer
                continue
            score_improvement = sum(a.score for a in new_set) - \
                                sum(a.score for a in self.answers[page_id][q_id])

            if not self._is_improvement_bigger(
                    score_improvement, weight, page_id, all_weights
            ) or score_improvement == 0:
                continue
            # if improvement less equal that other weights less that this one => skip
            if best_weight is None or score_improvement > best_weight.score and self.higher_is_better\
                    or score_improvement < best_weight.score and not self.higher_is_better:
                best_weight = Weight(
                    val=weight,
                    score=score_improvement,
                    rm=smallest,
                    add=largest,
                    q=q_id,
                    pg=page_id)
        return best_weight

    def _is_improvement_bigger(self, score_improvement, weight_val, page_id, all_weights):
        """
        Check if a score_improvement value is *better* than the one before, with fewer changes.

        :param score_improvement:
        :param weight_val:
        :param page_id:
        :param all_weights:
        :return:
        """
        if self.higher_is_better and score_improvement < 0:
            return False
        if not self.higher_is_better and score_improvement > 0:
            return False
        try:
            prev_weight_improvement = all_weights[weight_val-1][page_id]
        except KeyError:
            return True
        if prev_weight_improvement.score >= score_improvement and self.higher_is_better\
                or prev_weight_improvement.score <= score_improvement and not self.higher_is_better:
            return False
        return True

    @staticmethod
    def _combine_answers(initial, to_remove, to_add):
        answers = [a for a in initial if a not in to_remove]
        return answers + to_add


def _prepare_result_for_display(alternatives):
    """Given two alternatives (better and/or worse) create a structure easy to use in the template.

    The structure is like this:
    {
        <Question obj>: {
            'add': [<Answer obj>, <Answer obj>],
            'rm: [<Answer obj>]
        }
        ...
    }

    :param alternatives:
    :return: dict, dict
    """
    better = alternatives.get('better', {})
    better_prepared = {}
    worse = alternatives.get('worse', {})
    worse_prepared = {}

    question_ids = []
    answer_ids = []
    for w in chain(better.itervalues(), worse.itervalues()):
        question_ids.append(w.q)
        answer_ids += [a.id for a in w.add]
        answer_ids += [a.id for a in w.rm]

    questions = Question.objects.in_bulk(question_ids)
    answers = Answer.objects.in_bulk(answer_ids)

    for w in better.itervalues():
        better_prepared[questions[w.q]] = {'add': [], 'rm': []}
        better_prepared[questions[w.q]]['add'] = [answers[a.id] for a in w.add]
        better_prepared[questions[w.q]]['rm'] = [answers[a.id] for a in w.rm]

    for w in worse.itervalues():
        worse_prepared[questions[w.q]] = {'add': [], 'rm': []}
        worse_prepared[questions[w.q]]['add'] = [answers[a.id] for a in w.add]
        worse_prepared[questions[w.q]]['rm'] = [answers[a.id] for a in w.rm]
    return better_prepared, worse_prepared


def _main():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _main()