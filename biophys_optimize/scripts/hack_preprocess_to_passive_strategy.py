#!/usr/bin/env python

import json
import argparse
import os.path
from pkg_resources import resource_filename
import biophys_optimize.neuron_passive_fit as npf

parser = argparse.ArgumentParser(description='hack in paths that strategy will do - passive')
parser.add_argument('input', type=str)
parser.add_argument('output', type=str)
parser.add_argument('passive_fit_type', type=str)
args = parser.parse_args()

fit1_handles = [
    "passive/fixnseg.hoc",
    "passive/iclamp.ses",
    "passive/params.hoc",
    "passive/mrf.ses",
]

fit2_handles = [
    "passive/fixnseg.hoc",
    "passive/iclamp.ses",
    "passive/params.hoc",
    "passive/mrf2.ses",
]

fit3_handles = [
    "passive/fixnseg.hoc",
    "passive/circuit.ses",
    "passive/params.hoc",
    "passive/mrf3.ses",
]

if args.passive_fit_type == npf.PASSIVE_FIT_1:
    fit_handles = fit1_handles
elif args.passive_fit_type == npf.PASSIVE_FIT_2:
    fit_handles = fit2_handles
elif args.passive_fit_type == npf.PASSIVE_FIT_ELEC:
    fit_handles = fit3_handles

with open(args.input, "r") as f:
    data = json.load(f)

import biophys_optimize
bo_name = biophys_optimize.__name__

new_path_info = {
    "fit": [resource_filename(bo_name, f) for f in fit_handles],
    "passive_fit_results_file": os.path.join(data["paths"]["storage_directory"], "%s_results.json" % args.passive_fit_type)
}

data["paths"].update(new_path_info)
data["passive_fit_type"] = args.passive_fit_type

with open(args.output, "w") as f:
    json.dump(data, f, indent=2)
