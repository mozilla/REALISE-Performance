# -*- coding: utf-8 -*-

# Author: G.J.J. van den Burg <gvandenburg@turing.ac.uk>
# License: See LICENSE file
# Copyright: 2020 (c) The Alan Turing Institute

import csv
import io
import os
import datetime

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    send_file,
    url_for,
)

from werkzeug.utils import secure_filename

from app import db
from app.admin import bp
from app.decorators import admin_required
from app.admin.forms import (
    AdminManageTaskForm,
    AdminAddDatasetForm,
    AdminManageDatasetsForm,
    AdminManageUsersForm,
    AdminSelectDatasetForm,
)
from app.models import User, Dataset, Task, Annotation
from app.utils.datasets import (
    get_name_from_dataset,
    md5sum,
    dataset_is_demo,
    load_data_for_chart,
)
from sqlalchemy import func


@bp.route("/manage/tasks", methods=("GET", "POST"))
@admin_required
def manage_tasks():
    user_list = [(u.id, u.username) for u in User.query.all()]
    dataset_list = [
        (d.id, d.name) for d in Dataset.query.order_by(Dataset.name).all()
    ]

    form = AdminManageTaskForm()
    form.username.choices = user_list
    form.dataset.choices = dataset_list

    if form.validate_on_submit():
        user = User.query.filter_by(id=form.username.data).first()
        if user is None:
            flash("User does not exist.", "error")
            return redirect(url_for("admin.manage_tasks"))
        dataset = Dataset.query.filter_by(id=form.dataset.data).first()
        if dataset is None:
            flash("Dataset does not exist.", "error")
            return redirect(url_for("admin.manage_tasks"))

        action = None
        if form.assign.data:
            action = "assign"
        elif form.delete.data:
            action = "delete"
        else:
            flash(
                "Internal error: no button is true but form was submitted.",
                "error",
            )
            return redirect(url_for("admin.manage_tasks"))

        task = Task.query.filter_by(
            annotator_id=user.id, dataset_id=dataset.id
        ).first()
        if task is None:
            if action == "delete":
                flash("Can't delete a task that doesn't exist.", "error")
                return redirect(url_for("admin.manage_tasks"))
            else:
                task = Task(annotator_id=user.id, dataset_id=dataset.id)
                task.admin_assigned = True
                db.session.add(task)
                db.session.commit()
                flash("Task registered successfully.", "success")
        else:
            if action == "assign":
                flash("Task assignment already exists.", "error")
                return redirect(url_for("admin.manage_tasks"))
            else:
                # delete annotations too
                for ann in Annotation.query.filter_by(task_id=task.id).all():
                    db.session.delete(ann)
                db.session.delete(task)
                db.session.commit()
                flash("Task deleted successfully.", "success")

    tasks = (
        Task.query.join(User, Task.user)
        .join(Dataset, Task.dataset)
        .order_by(Dataset.name, User.username)
        .all()
    )
    return render_template(
        "admin/manage_tasks.html", title="Assign Task", form=form, tasks=tasks
    )

@bp.route("/manage/tasks/download", methods=("GET",))
@admin_required
def download_tasks_csv():
    tasks = (
        Task.query
        .filter_by(done=1)
        .join(User, Task.user)
        .join(Dataset, Task.dataset)
        .order_by(Dataset.name, User.username)
        .all()
    )

    header = [
        "TaskID",
        "DatasetName",
        "Username",
        "CompletedOn",
        "Difficulty",
        "TimeSpent",
        "Problem",
    ]

    proxy = io.StringIO()
    writer = csv.writer(proxy)
    writer.writerow(header)
    for task in tasks:
        row = [
            task.id,
            task.dataset.name,
            task.user.username,
            task.annotated_on,
            task.difficulty,
            task.time_spent,
            task.problem,
        ]
        writer.writerow(row)

    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode("utf-8"))
    mem.seek(0)
    proxy.close()

    fname = "%i_tasks.csv" % (round(datetime.datetime.now().timestamp()))

    return send_file(
        mem, as_attachment=True, attachment_filename=fname, mimetype="text/csv"
    )


@bp.route("/manage/users", methods=("GET", "POST"))
@admin_required
def manage_users():
    users = User.query.all()
    tasks = Task.query.filter_by(done=1).all()
    for u in users:
        u.annotated = len([t for t in tasks if t.annotator_id == u.id])
    user_list = [(u.id, u.username) for u in users if not u.is_admin]

    form = AdminManageUsersForm()
    form.user.choices = user_list

    if form.validate_on_submit():
        user = User.query.filter_by(id=form.user.data).first()
        if user is None:
            flash("User doesn't exist.", "error")
            return redirect(url_for("admin.manage_users"))

        username = user.username

        tasks = Task.query.filter_by(annotator_id=user.id).all()
        for task in tasks:
            for ann in Annotation.query.filter_by(task_id=task.id).all():
                db.session.delete(ann)
            db.session.delete(task)
        db.session.delete(user)
        db.session.commit()
        flash("User '%s' deleted successfully." % username, "success")
        return redirect(url_for("admin.manage_users"))
    return render_template(
        "admin/manage_users.html", title="Manage Users", users=users, form=form
    )


@bp.route("/manage/datasets", methods=("GET", "POST"))
@admin_required
def manage_datasets():
    dataset_list = [(d.id, d.name) for d in Dataset.query.all()]
    dataset_list.sort(key=lambda x: x[1])

    form = AdminManageDatasetsForm()
    form.dataset.choices = dataset_list

    if form.validate_on_submit():
        dataset = Dataset.query.filter_by(id=form.dataset.data).first()
        if dataset is None:
            flash("Dataset doesn't exist.", "error")
            return redirect(url_for("admin.manage_datasets"))

        dataset_dir = os.path.join(
            current_app.instance_path, current_app.config["DATASET_DIR"]
        )
        filename = os.path.join(dataset_dir, dataset.name + ".json")
        if not os.path.exists(filename):
            flash("Internal error: dataset file doesn't exist!", "error")

        tasks = Task.query.filter_by(dataset_id=dataset.id).all()
        for task in tasks:
            for ann in Annotation.query.filter_by(task_id=task.id).all():
                db.session.delete(ann)
            db.session.delete(task)
        db.session.delete(dataset)
        db.session.commit()
        if os.path.exists(filename):
            os.unlink(filename)
        flash("Dataset deleted successfully.", "success")
        return redirect(url_for("admin.manage_datasets"))

    overview = []
    for dataset in Dataset.query.all():
        tasks = Task.query.filter_by(dataset_id=dataset.id).all()
        n_complete = len([t for t in tasks if t.done])
        desired = current_app.config["TASKS_NUM_PER_DATASET"]
        if len(tasks) == 0:
            perc = float("nan")
        else:
            perc = n_complete / desired * 100
        entry = {
            "id": dataset.id,
            "name": dataset.name,
            "demo": dataset.is_demo,
            "assigned": len(tasks),
            "completed": n_complete,
            "percentage": perc,
        }
        overview.append(entry)
        overview.sort(key=lambda x: x["name"])
    return render_template(
        "admin/manage_datasets.html",
        title="Manage Datasets",
        overview=overview,
        form=form,
    )


@bp.route("/add", methods=("GET", "POST"))
@admin_required
def add_dataset():
    tmp_dir = os.path.join(
        current_app.instance_path, current_app.config["TEMP_DIR"]
    )
    dataset_dir = os.path.join(
        current_app.instance_path, current_app.config["DATASET_DIR"]
    )
    form = AdminAddDatasetForm()
    if form.validate_on_submit():
        temp_filename = os.path.join(
            tmp_dir, secure_filename(form.file_.data.filename)
        )
        if not os.path.exists(temp_filename):
            flash("Internal error: temporary dataset disappeared.", "error")
            return redirect(url_for("admin.add_dataset"))
        name = get_name_from_dataset(temp_filename)
        target_filename = os.path.join(dataset_dir, name + ".json")
        if os.path.exists(target_filename):
            flash("Internal error: file already exists!", "error")
            return redirect(url_for("admin.add_dataset"))
        os.rename(temp_filename, target_filename)
        if not os.path.exists(target_filename):
            flash("Internal error: file moving failed", "error")
            return redirect(url_for("admin.add_dataset"))
        is_demo = dataset_is_demo(target_filename)
        dataset = Dataset(
            name=name, md5sum=md5sum(target_filename), is_demo=is_demo
        )
        db.session.add(dataset)
        db.session.commit()
        flash("Dataset %r added successfully." % name, "success")
        return redirect(url_for("admin.add_dataset"))
    return render_template("admin/add.html", title="Add Dataset", form=form)


@bp.route("/annotations", methods=("GET", "POST"))
@admin_required
def view_annotations():
    dataset_list = [(d.id, d.name) for d in Dataset.query.all()]
    form = AdminSelectDatasetForm()
    form.dataset.choices = dataset_list

    if form.validate_on_submit():
        dataset = Dataset.query.filter_by(id=form.dataset.data).first()
        if dataset is None:
            flash("Dataset does not exist.", "error")
            return redirect(url_for("admin.view_annotations"))
        return redirect(
            url_for("admin.view_annotations_by_dataset", dset_id=dataset.id)
        )

    annotations = (
        Annotation.query.join(Task, Annotation.task)
        .join(User, Task.user)
        .join(Dataset, Task.dataset)
        .order_by(Dataset.name, User.username, Annotation.cp_index)
        .all()
    )
    return render_template(
        "admin/annotations.html",
        title="View Annotations",
        annotations=annotations,
        form=form,
    )


@bp.route("/annotations/download", methods=("GET",))
@admin_required
def download_annotations_csv():
    annotations = (
        Annotation.query.join(Task, Annotation.task)
        .join(User, Task.user)
        .join(Dataset, Task.dataset)
        .order_by(Dataset.id, User.username, Annotation.cp_index)
        .all()
    )

    # based on: https://stackoverflow.com/a/45111660/1154005
    header = [
        "DatasetID",
        "DatasetName",
        "UserID",
        "AnnotatedOn",
        "AnnotationIndex",
        "AnnotationType",
    ]

    proxy = io.StringIO()
    writer = csv.writer(proxy)
    writer.writerow(header)
    for ann in annotations:
        row = [
            ann.task.dataset.id,
            ann.task.dataset.name,
            ann.task.user.id,
            ann.task.annotated_on,
        ]
        if ann.cp_index is None:
            row.append("no_cp")
        else:
            row.append(ann.cp_index)
            row.append(ann.type)
        writer.writerow(row)

    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode("utf-8"))
    mem.seek(0)
    proxy.close()

    fname = "%i_annotations.csv" % (round(datetime.datetime.now().timestamp()))

    return send_file(
        mem, as_attachment=True, attachment_filename=fname, mimetype="text/csv"
    )


@bp.route("/annotations_by_dataset/<int:dset_id>", methods=("GET",))
@admin_required
def view_annotations_by_dataset(dset_id):
    dataset = Dataset.query.filter_by(id=dset_id).first()
    annotations = (
        Annotation.query.join(Task, Annotation.task)
        .join(User, Task.user)
        .join(Dataset, Task.dataset)
        .order_by(Dataset.name, User.username, Annotation.cp_index)
        .all()
    )

    annotations = [a for a in annotations if a.task.dataset.id == dset_id]

    anno_clean = []
    user_counter = {}
    counter = 1
    for ann in annotations:
        if ann.task.user.id in user_counter:
            uid = user_counter[ann.task.user.id]
        else:
            uid = user_counter.setdefault(
                ann.task.user.id, "user-%i" % counter
            )
            counter += 1
        anno_clean.append(dict(user=uid, index=ann.cp_index))

    data = load_data_for_chart(dataset.name, dataset.md5sum)
    is_multi = len(data["chart_data"]["values"]) > 1
    data["annotations"] = anno_clean
    return render_template(
        "admin/annotations_by_dataset.html",
        title="View Annotations for dataset",
        data=data,
        is_multi=is_multi,
    )


@bp.route("/", methods=("GET",))
@admin_required
def index():
    return render_template("admin/index.html", title="Admin Home")
