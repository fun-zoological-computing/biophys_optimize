#!/usr/bin/env python

from neuron import h
import numpy as np
import argparse
import json
import os.path


def load_morphology(filename):
    swc = h.Import3d_SWC_read()
    swc.input(filename)
    imprt = h.Import3d_GUI(swc, 0)
    h("objref this")
    imprt.instantiate(h.this)


def main(input_file, output_file):
    with open(input_file, "r") as f:
        input = json.load(f)

    swc_path = input["paths"]["swc"].encode('ascii', 'ignore')
    up_data = np.loadtxt(input["paths"]["up"])
    down_data = np.loadtxt(input["paths"]["down"])
    with open(input["paths"]["passive_info"], "r") as f:
        info = json.load(f)

    h.load_file("stdgui.hoc")
    h.load_file("import3d.hoc")
    load_morphology(swc_path)

    for sec in h.allsec():
        if sec.name().startswith("axon"):
            h.delete_section(sec=sec)
    axon = h.Section()
    axon.L = 60
    axon.diam = 1
    axon.connect(h.soma[0], 0.5, 0)

    h.define_shape()

    for sec in h.allsec():
        sec.insert('pas')
        for seg in sec:
            seg.pas.e = 0

    for file_path in input["paths"]["fit2"]:
        h.load_file(file_path.encode("ascii", "ignore"))

    h.v_init = 0
    h.tstop = 100
    h.cvode_active(1)

    fit_start = 4.0025

    v_rec = h.Vector()
    t_rec = h.Vector()
    v_rec.record(h.soma[0](0.5)._ref_v)
    t_rec.record(h._ref_t)

    mrf = h.MulRunFitter[0]
    gen0 = mrf.p.pf.generatorlist.object(0)
    gen0.toggle()
    fit0 = gen0.gen.fitnesslist.object(0)

    up_t = h.Vector(up_data[:, 0])
    up_v = h.Vector(up_data[:, 1])
    fit0.set_data(up_t, up_v)
    fit0.boundary.x[0] = fit_start
    fit0.boundary.x[1] = info["limit"]
    fit0.set_w()

    gen1 = mrf.p.pf.generatorlist.object(1)
    gen1.toggle()
    fit1 = gen1.gen.fitnesslist.object(0)

    down_t = h.Vector(down_data[:, 0])
    down_v = h.Vector(down_data[:, 1])
    fit1.set_data(down_t, down_v)
    fit1.boundary.x[0] = fit_start
    fit1.boundary.x[1] = info["limit"]
    fit1.set_w()

    minerr = 1e12
    for i in range(3):
        # Need to re-initialize the internal MRF variables, not top-level proxies
        # for randomize() to work
        mrf.p.pf.parmlist.object(0).val = 1
        mrf.p.pf.parmlist.object(1).val = 10000
        mrf.randomize()
        mrf.prun()
        if mrf.opt.minerr < minerr:
            fit_Ri = h.Ri
            fit_Cm = h.Cm
            fit_Rm = h.Rm
            minerr = mrf.opt.minerr

    storage_directory = input["paths"]["storage_directory"]
    results = {
        "ra": fit_Ri,
        "cm": fit_Cm,
        "rm": fit_Rm,
        "err": minerr,
        "a1": h.somaaxon_area(),
        "a2": h.alldend_area(),
    }
    results_file = os.path.join(storage_directory, "passive_fit_2_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    with open(output_file, "w") as f:
        json.dump({"paths": {"passive_fit2": results_file}}, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='analyze cap check sweep')
    parser.add_argument('input', type=str)
    parser.add_argument('output', type=str)
    args = parser.parse_args()

    main(args.input, args.output)
