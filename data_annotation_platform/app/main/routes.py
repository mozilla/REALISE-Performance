# -*- coding: utf-8 -*-

# Author: G.J.J. van den Burg <gvandenburg@turing.ac.uk>
# License: See LICENSE file
# Copyright: 2020 (c) The Alan Turing Institute

import datetime
import logging

from flask import render_template, flash, url_for, redirect, request
from flask_login import current_user

from app import db
from app.decorators import login_required
from app.main import bp
from app.main.email import send_annotation_backup
from app.models import Annotation, Task, Dataset
from app.utils.datasets import load_data_for_chart
from app.utils.tasks import generate_user_task

logger = logging.getLogger(__name__)

RUBRIC = """
Please mark the point(s) in the time series where an <b>abrupt change</b> in
 the behaviour of the series occurs. The goal is to define segments of the time 
 series that are separated by places where these abrupt changes occur. Recall 
 that it is also possible for there to be <i>no change points</i>.
 Different types of changes (mean, variance, both) can be marked
 by clicking repeatedly on the same datapoint.
<br>
"""

def __get_done_and_todo(user):
    tasks = Task.query.filter_by(annotator_id=user.id).all()
    tasks_done = [t for t in tasks if t.done and not t.dataset.is_demo]
    tasks_todo = [
        t for t in tasks if (not t.done) and (not t.dataset.is_demo)
    ]
    datasets = Dataset.query.filter_by(is_demo=False).all()
    tasks_potential = [d for d in datasets
            if d.id not in [t.dataset_id for t in tasks]]
    left = user.max_tasks - len(tasks_done)
    if len(tasks_potential) > left:
        tasks_potential = tasks_potential[:left]
    return tasks_done, tasks_todo, tasks_potential

@bp.route("/")
@bp.route("/index")
def index():
    if not current_user.is_anonymous and not current_user.is_confirmed:
        return redirect(url_for("auth.not_confirmed"))
    if current_user.is_authenticated:
        tasks_done, tasks_todo, tasks_potential = __get_done_and_todo(current_user)
        return render_template(
            "index.html",
            title="Home",
            tasks_done=tasks_done,
            tasks_todo=tasks_todo,
            tasks_potential=tasks_potential,
        )
    return render_template("index.html", title="Home")


@bp.route("/assign")
@login_required
def assign():
    # Intermediate page that assigns a task to a user if needed and then
    # redirects to /annotate/task.id
    user_tasks = Task.query.filter_by(annotator_id=current_user.id).all()
    user_tasks = [t for t in user_tasks if not t.dataset.is_demo]
    user_tasks = [t for t in user_tasks if not t.done]

    # if the user has, for some reason, a unfinished assigned task, redirect to
    # that. This can happen if the admin has assigned this task.
    if len(user_tasks) > 0:
        task = user_tasks[0]
        return redirect(url_for("main.annotate", task_id=task.id))

    task = generate_user_task(current_user)
    if task is None:
        flash(
            "There are no more datasets to annotate at the moment, thanks for all your help!",
            "info",
        )
        return redirect(url_for("main.index"))
    db.session.add(task)
    db.session.commit()
    return redirect(url_for("main.annotate", task_id=task.id))


@bp.route("/annotate/<int:task_id>", methods=("GET", "POST"))
@login_required
def annotate(task_id):
    if request.method == "POST":
        # record post time
        now = datetime.datetime.utcnow()

        # get the json from the client
        annotation = request.get_json()
        if annotation["identifier"] != task_id:
            flash("Internal error: task id doesn't match.", "error")
            return redirect(url_for(task_id=task_id))

        task = Task.query.filter_by(id=task_id).first()

        # if it is a re-annotation, get back to the home page
        # otherwise proceed with the next time series
        if task.done:
            next = "main.index"
        else:
            next = "main.assign"

        # remove all previous annotations for this task
        for ann in Annotation.query.filter_by(task_id=task_id).all():
            db.session.delete(ann)
        task.done = False
        task.annotated_on = None
        db.session.commit()

        # record the annotation
        if annotation["changepoints"] is None:
            ann = Annotation(cp_index=None, type=None, task_id=task_id)
            db.session.add(ann)
            db.session.commit()
        else:
            for cp in annotation["changepoints"]:
                ann = Annotation(cp_index=cp["x"], type=cp["t"], task_id=task_id)
                db.session.add(ann)
                db.session.commit()

        # mark the task as done
        task.done = True
        task.annotated_on = now
        task.time_spent = annotation["time_spent"]
        task.difficulty = annotation["difficulty"]
        task.problem = annotation["problem"]
        db.session.commit()
        done, _, todo = __get_done_and_todo(current_user)
        flash("Your annotation has been recorded, thank you! Done {}, {} to go!"\
                .format(len(done), len(todo)), "success")

        # send the annotation as email to the admin for backup
        record = {
            "user_id": task.annotator_id,
            "dataset_name": task.dataset.name,
            "dataset_id": task.dataset_id,
            "task_id": task.id,
            "annotations_raw": annotation,
        }
        send_annotation_backup(record)

        return url_for(next)

    task = Task.query.filter_by(id=task_id).first()

    # check if task exists
    if task is None:
        flash("No task with id %r exists." % task_id, "error")
        return redirect(url_for("main.index"))

    # check if task is assigned to this user
    if not task.annotator_id == current_user.id:
        flash(
            "No task with id %r has been assigned to you." % task_id, "error"
        )
        return redirect(url_for("main.index"))

    # check if task is not already done
    '''
    if task.done:
        flash("It's not possible to edit annotations at the moment.")
        return redirect(url_for("main.index"))
    '''

    data = load_data_for_chart(task.dataset.name, task.dataset.md5sum)
    if data is None:
        flash(
            "An internal error occurred loading this dataset, the admin has been notified. Please try again later. We apologise for the inconvenience.",
            "error",
        )
        return redirect(url_for("main.index"))
    title = f"Dataset: {task.dataset.id}"
    is_multi = len(data["chart_data"]["values"]) > 1
    return render_template(
        "annotate/index.html",
        title=title,
        identifier=task.id,
        data=data,
        rubric=RUBRIC,
        is_multi=is_multi,
    )

@bp.route("/view_annotations/<int:task_id>", methods=("GET", "POST"))
@login_required
def view_annotations(task_id):
    task = Task.query.filter_by(id=task_id).first()
    # check if task exists
    if task is None:
        flash("No task with id %r exists." % task_id, "error")
        return redirect(url_for("main.index"))

    dataset = Dataset.query.filter_by(id=task.dataset_id).first()
    data = load_data_for_chart(dataset.name, dataset.md5sum)
    is_multi = len(data["chart_data"]["values"]) > 1
    annotations = Annotation.query.filter_by(task_id=task_id).all()
    data["annotations"] =\
            [dict(user="user-%i" % task.annotator_id, index=a.cp_index)
                for a in annotations]

    return render_template(
        "annotate/view.html",
        title="View Annotations for dataset",
        data=data,
        is_multi=is_multi,
        task_id=task_id,
    )
