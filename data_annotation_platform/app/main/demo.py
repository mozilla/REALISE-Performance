# -*- coding: utf-8 -*-

# Author: G.J.J. van den Burg <gvandenburg@turing.ac.uk>
# License: See LICENSE file
# Copyright: 2020 (c) The Alan Turing Institute

import datetime
import logging
import markdown
import textwrap
import itertools

from flask import (
    render_template,
    flash,
    url_for,
    redirect,
    request,
    session,
    abort,
)
from flask_login import current_user

from sqlalchemy import desc

from app import db
from app.decorators import login_required
from app.models import Annotation, Dataset, Task
from app.main import bp
from app.main.forms import NextForm
from app.main.routes import RUBRIC
from app.utils.datasets import load_data_for_chart, get_demo_true_cps
import os

ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "realiselab@gmail.com")

LOGGER = logging.getLogger(__name__)

# textwrap.dedent is used mostly for code formatting.
DEMO_DATA = {
    1: {
        "dataset": {"name": "demo_400"},
        "learn": {
            "text": markdown.markdown(
                textwrap.dedent(
                """
                Welcome to the Mozilla data annotation tool. Thank you for taking the time to provide your input.

                Our goal is to create a dataset of *human-annotated* time series to use in the development and 
                evaluation of change point algorithms which could be used in [Perfherder](https://treeherder.mozilla.org/perfherder/alerts?hideDwnToInv=1&page=1) to provide more accurate alerts, saving investigation time and effort for Mozilla Performance Sheriffs.

                The time series you will see was collected from the Mozilla performance infrastructure. We collected performance measurements from multiple signatures and we aggregate them by revision as we group the measurtements for a specific revision and we average them. 

                Once you annotate a time series, feel free to leave a review on its difficulty of annotation. This will help us to conduct our analysis.

                Each step of the shows a limited part of the functionality of the tool so you can develop a good understanding of it.

                Thanks again for your help!
                """
                )
            )
        },
        "annotate": {
            "text": markdown.markdown(
                textwrap.dedent(
                """
                The following time series is presented through the specs described in the box below.
                
                In order to perperly investigate change points, you could *zoom in* within the graph with your mouse or touchpad for more details on X-axis or Y-axis, you can control the behaviour through the correspondent toggle below the graph.

                - *Zooming with mouse*

                Use the scroller to zoom in and out, you could double click on an area to zoom in it.

                - Zooming and panning with touchpad

                Use a two-finger swipe gesture on your touchpad to zoom in (upward sliding) or zoom out (downward sliding). You can also double-click on the left button of the touchpad to zoom in.

                *Be careful!* the initial zoom after changing the zoom mode might be very large. It is recommended to point the cursor on the data points before zooming in.
                Note that you could pan in the graph! Click and hold the left mouse button (or touchpad), then move your cursor or finger to pan the graph 
                
                Also, you could *choose* to include or remove the lines in the graph for convenience by clicking and unclicking the checkbox below.
                
                Click "Submit" when you have finished marking the change points 
                or *"No change points"* when you believe there are none, *such as the case for this example*.
                """
                )
            )
        },
        "evaluate": {
            "text": markdown.markdown(
                textwrap.dedent(
                """
                The evaluation layout that you see will help you afterwards to evaluate your annotation attempt.
                
                The other time series in this demo contain change points.
                """
                )
            )
        },
    },
    2: {
        "dataset": {"name": "demo_100"},
        "learn": {
            "text": markdown.markdown(
                textwrap.dedent(
                """
                Different types of changes (mean, variance, both) can be marked
                by *clicking repeatedly* on the same datapoint. The color of the
                datapoint will change, and the type of change will be reported
                in the *table* underneath the plot as follows: <span style="color:red">red</span> (mean), <span style="color:orange">orange</span>
                (variance), <span style="color:#CCCC00">yellow</span> (mean_variance) and <span style="color:blue">blue</span> (none). A marked
                point can be unmarked by clicking on it again until it turns blue.              
                """
                )
            )
        },
        "annotate": {
            "text": markdown.markdown(
                textwrap.dedent(
                """
                Please mark the point(s) in the time series where an abrupt change in the behaviour of the series occurs.
                The goal is to define segments of the time series that are separated by places where these abrupt changes occur.
                Note that in general we consider the change point to be the 
                point where the new behaviour *starts*, not the last point of 
                the current behaviour. You can reset the graph with the "Reset" button.
                """
                )
            )
        },
        "evaluate": {
            "text": markdown.markdown(
                textwrap.dedent(
                """
                This time series example contains one change point that represents a *step change* (aka the “mean")
                occurred at a certain point in time. A step change is one of the simplest types of change 
                points that can occur.
                """
                )
            )
        },
    },
    3: {
        "dataset": {"name": "demo_300"},
        "learn": {
            "text": markdown.markdown(
                textwrap.dedent(
                """
                In the previous example we've introduced *step change* or *mean*. It had *one* change point.
                Not all datasets that you'll encounter in this program have exactly one change point.
                Also, *mean* is not the only type of change points that 
                can occur, as we'll see in the next example. 
                """
                )
            )
        },
        "annotate": {
            "text": markdown.markdown(
                textwrap.dedent(
                """
                Please mark the point(s) in the time series where an abrupt change in the behaviour of the series occurs.
                The goal is to define segments of the time series that are separated by places where these abrupt changes occur.
                """
                )
            )
        },
        "evaluate": {
            "text": markdown.markdown(
                textwrap.dedent(
                """
                This time series shows an example where a change occurs in the 
                *variance* of the data. At the change point the variance of 
                the noise changes abruptly from a relatively low noise variance 
                to a high noise variance. This is another type of change point 
                that can occur.
                """
                )
            )
        },
    },
}

# Cut the tutorial to the first 5 steps
# DEMO_DATA = dict(itertools.islice(DEMO_DATA.items(), 5))


def demo_performance(user_id):
    score = 0
    for demo_id in DEMO_DATA:
        dataset = Dataset.query.filter_by(
            name=DEMO_DATA[demo_id]["dataset"]["name"]
        ).first()
        tasks = (
            Task.query.filter_by(annotator_id=user_id, dataset_id=dataset.id)
            .order_by(desc(Task.annotated_on))
            .limit(1)
            .all()
        )
        task = tasks[0]
        annotations = (
            Annotation.query.join(Task, Annotation.task)
            .filter_by(id=task.id)
            .all()
        )

        true_cp = get_demo_true_cps(dataset.name)
        user_cp = [a.cp_index for a in annotations if not a.cp_index is None]
        if len(true_cp) == len(user_cp) == 0:
            score += 1
            continue

        n_correct, n_window, n_fp, n_fn = metrics(true_cp, user_cp)
        n_tp = n_correct + n_window
        f1 = (2 * n_tp) / (2 * n_tp + n_fp + n_fn)

        score += f1
    score /= len(DEMO_DATA)
    return score


def redirect_user(demo_id, phase_id):
    last_demo_id = max(DEMO_DATA.keys())
    demo_last_phase_id = 3
    if demo_id == last_demo_id and phase_id == demo_last_phase_id:
        # User is already introduced (happens if they redo the demo)
        if current_user.is_introduced:
            return redirect(url_for("main.index"))

        # check user performance
        if demo_performance(current_user.id) < 0.10:
            flash(
                "Unfortunately your performance on the introduction "
                "datasets was not as high as we would like. Please go "
                "through the introduction one more time to make sure "
                "that you understand and are comfortable with change "
                "point detection."
            )
            return redirect(url_for("main.index"))
        else:
            flash("Thank you for completing the introduction!", "success")

        # mark user as introduced
        current_user.is_introduced = True
        db.session.commit()

        return redirect(url_for("main.index"))
    elif phase_id == demo_last_phase_id:
        demo_id += 1
        phase_id = 1
        return redirect(
            url_for("main.demo", demo_id=demo_id, phase_id=phase_id)
        )
    else:
        phase_id += 1
        return redirect(
            url_for("main.demo", demo_id=demo_id, phase_id=phase_id)
        )


def process_annotations(demo_id):
    annotation = request.get_json()
    if annotation["identifier"] != demo_id:
        LOGGER.error(
            "User %s returned a task id in the demo that wasn't the demo id."
            % current_user.username
        )
        flash(
            "An internal error occurred, the administrator has been notified.",
            "error",
        )
        return redirect(url_for("main.index"))

    retval = []
    if not annotation["changepoints"] is None:
        retval = [int(cp["x"]) for cp in annotation["changepoints"]]

    # If the user is already introduced, we assume that their demo annotations
    # are already in the database, and thus we don't put them back in (because
    # we want the original ones).
    if current_user.is_introduced:
        return retval

    dataset = Dataset.query.filter_by(
        name=DEMO_DATA[demo_id]["dataset"]["name"]
    ).first()

    # Create a new task
    task = Task(annotator_id=current_user.id, dataset_id=dataset.id)
    task.done = False
    task.annotated_on = None
    db.session.add(task)
    db.session.commit()
    if annotation["changepoints"] is None:
        ann = Annotation(cp_index=None, task_id=task.id)
        db.session.add(ann)
        db.session.commit()
    else:
        for cp in annotation["changepoints"]:
            ann = Annotation(cp_index=cp["x"], task_id=task.id)
            db.session.add(ann)
            db.session.commit()

    # mark task as done
    task.done = True
    task.annotated_on = datetime.datetime.utcnow()
    db.session.commit()

    return retval


def metrics(true_cp, user_cp, k=5):
    true_cp = [int(x) for x in true_cp]
    user_cp = [int(x) for x in user_cp]

    correct = []
    window = []
    incorrect = []
    rem_true = list(true_cp)

    for cp in user_cp:
        if cp in rem_true:
            correct.append(cp)
            rem_true.remove(cp)
    user_cp = [x for x in user_cp if not x in correct]

    for cp in user_cp:
        to_delete = []
        for y in rem_true:
            if abs(cp - y) < k:
                window.append(cp)
                to_delete.append(y)
                break
        for y in to_delete:
            rem_true.remove(y)
    user_cp = [x for x in user_cp if not x in window]

    for cp in user_cp:
        incorrect.append(cp)

    n_correct = len(correct)
    n_window = len(window)
    n_fp = len(incorrect)
    n_fn = len(rem_true)
    return n_correct, n_window, n_fp, n_fn


def get_user_feedback(true_cp, user_cp):
    """Generate HTML to show as feedback to the user"""
    n_correct, n_window, n_fp, n_fn = metrics(true_cp, user_cp)

    text = "\n\n*Feedback:*\n\n"
    if len(true_cp) == len(user_cp) == 0:
        text += " - *Correctly identified that there are no change points.*\n"
    if len(true_cp) > 0:
        text += f"- *Number of changepoints exactly correct: {n_correct}.*\n"
    if n_window:
        text += f"- *Number of points correct within a 5-step window: {n_window}.*\n"
    if n_fp:
        text += f"- *Number of incorrectly identified points: {n_fp}.*\n"
    if n_fn:
        text += f"- *Number of missed change points: {n_fn}.*"
    text.rstrip()

    text = markdown.markdown(text)
    return text


def demo_learn(demo_id, form):
    demo_data = DEMO_DATA[demo_id]["learn"]
    return render_template(
        "demo/learn.html",
        title="Demo example – " + str(demo_id) + " out of " + str(len(DEMO_DATA)),
        text=demo_data["text"],
        form=form,
        admin_emails=ADMIN_EMAILS
    )


def demo_annotate(demo_id):
    demo_data = DEMO_DATA[demo_id]["annotate"]
    dataset = Dataset.query.filter_by(
        name=DEMO_DATA[demo_id]["dataset"]["name"]
    ).first()
    if dataset is None:
        LOGGER.error(
            "Demo requested unavailable dataset: %s"
            % DEMO_DATA[demo_id]["dataset"]["name"]
        )
        flash(
            "An internal error occured. The administrator has been notified. We apologise for the inconvenience, please try again later.",
            "error",
        )
        return redirect(url_for("main.index"))

    chart_data = load_data_for_chart(dataset.name, dataset.md5sum)
    is_multi = len(chart_data["chart_data"]["values"]) > 1
    return render_template(
        "annotate/index.html",
        title="Demo example – " + str(demo_id) + " out of " + str(len(DEMO_DATA)),
        data=chart_data,
        rubric=demo_data["text"],
        identifier=demo_id,
        is_multi=is_multi,
        admin_emails=ADMIN_EMAILS
    )


def demo_evaluate(demo_id, phase_id, form):
    demo_data = DEMO_DATA[demo_id]["evaluate"]
    user_changepoints = session.get("user_changepoints", "__UNK__")
    if user_changepoints == "__UNK__":
        flash(
            "The previous step of the demo was not completed successfully. Please try again.",
            "error",
        )
        return redirect(
            url_for("main.demo", demo_id=demo_id, phase_id=phase_id - 1)
        )
    dataset = Dataset.query.filter_by(
        name=DEMO_DATA[demo_id]["dataset"]["name"]
    ).first()
    chart_data = load_data_for_chart(dataset.name, dataset.md5sum)
    is_multi = len(chart_data["chart_data"]["values"]) > 1
    true_changepoints = get_demo_true_cps(dataset.name)
    if true_changepoints is None:
        flash(
            "An internal error occurred, the administrator has been notified. We apologise for the inconvenience, please try again later.",
            "error",
        )
        return redirect(url_for("main.index"))

    feedback = get_user_feedback(true_changepoints, user_changepoints)

    annotations_true = [dict(index=x) for x in true_changepoints]
    annotations_user = [dict(index=x) for x in user_changepoints]
    return render_template(
        "demo/evaluate.html",
        title="Demo example – " + str(demo_id) + " out of " + str(len(DEMO_DATA)),
        data=chart_data,
        annotations_user=annotations_user,
        annotations_true=annotations_true,
        text=demo_data["text"],
        feedback=feedback,
        form=form,
        is_multi=is_multi,
        admin_emails=ADMIN_EMAILS
    )


@bp.route(
    "/introduction/",
    defaults={"demo_id": 1, "phase_id": 1},
    methods=("GET", "POST"),
)
@bp.route(
    "/introduction/<int:demo_id>/",
    defaults={"phase_id": 1},
    methods=("GET", "POST"),
)
@bp.route(
    "/introduction/<int:demo_id>/<int:phase_id>", methods=("GET", "POST")
)
@login_required
def demo(demo_id, phase_id):
    form = NextForm()

    if request.method == "POST":
        if form.validate_on_submit():
            return redirect_user(demo_id, phase_id)
        else:
            user_changepoints = process_annotations(demo_id)
            session["user_changepoints"] = user_changepoints
            return url_for("main.demo", demo_id=demo_id, phase_id=phase_id + 1)

    if phase_id == 1:
        return demo_learn(demo_id, form)
    elif phase_id == 2:
        return demo_annotate(demo_id)
    elif phase_id == 3:
        return demo_evaluate(demo_id, phase_id, form)
    else:
        abort(404)
