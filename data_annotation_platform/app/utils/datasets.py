# -*- coding: utf-8 -*-

# Author: G.J.J. van den Burg <gvandenburg@turing.ac.uk>
# License: See LICENSE file
# Copyright: 2020 (c) The Alan Turing Institute

"""
Dataset handling

The dataset model is defined in the adjacent 'dataset_schema.json' file, which 
is a JSONSchema schema definition. It can be easily edited at 
www.jsonschema.net or yapi.demo.qunar.com/editor/

Missing values must be denoted by 'NaN' (this is understood by the JSON 
decoder).

"""

import hashlib
import json
import jsonschema
import logging
import math
import os

from flask import current_app

LOGGER = logging.getLogger(__file__)


def load_schema():
    pth = os.path.abspath(__file__)
    basedir = os.path.dirname(pth)
    schema_file = os.path.join(basedir, "dataset_schema.json")
    if not os.path.exists(schema_file):
        raise FileNotFoundError(schema_file)
    with open(schema_file, "rb") as fp:
        schema = json.load(fp)
    return schema


def validate_dataset(filename):
    if not os.path.exists(filename):
        return "File not found."

    with open(filename, "rb") as fp:
        try:
            data = json.load(fp)
        except json.JSONDecodeError as err:
            return "JSON decoding error: %s" % err.msg

    try:
        schema = load_schema()
    except FileNotFoundError:
        return "Schema file not found."

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as err:
        return "JSONSchema validation error: %s" % err.message

    if len(data["series"]) != data["n_dim"]:
        return "Number of dimensions and number of series don't match"

    if "time" in data.keys():
        if not "format" in data["time"] and "raw" in data["time"]:
            return "'raw' must be accompanied by format"
        if "format" in data["time"] and not "raw" in data["time"]:
            return "Format must be accompanied by 'raw'"
        if "index" in data["time"]:
            if not data["time"]["index"][0] == 0:
                return "Index should start at zero."
            if not len(data["time"]["index"]) == data["n_obs"]:
                return "Number of indices must match number of observations"
        if "raw" in data["time"]:
            if len(data["time"]["raw"]) != data["n_obs"]:
                return "Number of time points doesn't match number of observations"
            if None in data["time"]["raw"]:
                return "Null is not supported in time axis. Use 'NaN' instead."

    has_missing = False
    for var in data["series"]:
        if len(var["raw"]) != data["n_obs"]:
            return "Number of observations doesn't match for %s" % var["label"]
        if None in var["raw"]:
            return "Null is not supported in series. Use 'NaN' instead."
        has_missing = has_missing or any(map(math.isnan, var["raw"]))

    # this doesn't happen in any dataset yet, so let's not implement it until
    # we need it.
    if data["n_dim"] > 1 and has_missing:
        return "Missing values are not yet supported for multidimensional data"

    return None


def get_name_from_dataset(filename):
    with open(filename, "rb") as fid:
        data = json.load(fid)
    return data["name"]


def dataset_is_demo(filename):
    with open(filename, "rb") as fid:
        data = json.load(fid)
    return "demo" in data.keys()


def get_demo_true_cps(name):
    dataset_dir = os.path.join(
        current_app.instance_path, current_app.config["DATASET_DIR"]
    )
    target_filename = os.path.join(dataset_dir, name + ".json")
    if not os.path.exists(target_filename):
        LOGGER.error("Dataset with name '%s' can't be found!" % name)
        return None
    with open(target_filename, "rb") as fid:
        data = json.load(fid)
    if not "demo" in data:
        LOGGER.error("Asked for 'demo' key in non-demo dataset '%s'" % name)
        return None
    if not "true_CPs" in data["demo"]:
        LOGGER.error(
            "Expected field'true_cps' field missing for dataset '%s'" % name
        )
    return data["demo"]["true_CPs"]


def md5sum(filename):
    """ Compute the MD5 hash for a given filename """
    blocksize = 65536
    hasher = hashlib.md5()
    with open(filename, "rb") as fid:
        buf = fid.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = fid.read(blocksize)
    return hasher.hexdigest()


def load_data_for_chart(name, known_md5):
    dataset_dir = os.path.join(
        current_app.instance_path, current_app.config["DATASET_DIR"]
    )
    target_filename = os.path.join(dataset_dir, name + ".json")
    if not os.path.exists(target_filename):
        LOGGER.error("Dataset with name '%s' can't be found!" % name)
        return None
    if not md5sum(target_filename) == known_md5:
        LOGGER.error(
            """
        MD5 checksum failed for dataset with name: %s.
        Found: %s.
        Expected: %s.
        """
            % (name, md5sum(target_filename), known_md5)
        )
        return None
    
    signature_attributes_filename = os.path.join(current_app.instance_path, current_app.config["TEMP_DIR"], "data_timeseries_attributes.json")

    with open(target_filename, "rb") as fid:
        data = json.load(fid)
    
    with open(signature_attributes_filename, "rb") as fid:
        signature_data = json.load(fid)
    
    signature_attributes = signature_data.get(data.get("name"), {})


    chart_data = {
        "name": data["name"] if "name" in data else None,
        "time": data["time"] if "time" in data else None,
        "values": data["series"],
        "characteristics": signature_attributes
    }
    return {"chart_data": chart_data}
