"""
This module provides functions for running verification checks on small
models and to create reports about them.

"""
from __future__ import print_function
from collections import defaultdict
import ConfigParser
import argparse
import csv
import datetime
import json
import logging
import os
import glob
import math
from django.conf import settings
from jinja2 import Environment, PackageLoader
from netCDF4 import Dataset
import numpy as np

import matplotlib
matplotlib.use('Agg')  # needs to be at top of module
import matplotlib.pyplot as plt

from threedi_verification.utils import system

jinja_env = Environment(loader=PackageLoader('threedi_verification',
                                             'templates'))
logger = logging.getLogger(__name__)

OUTDIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                      '..', 'var', 'html'))
ARCHIVEDIR = os.path.join(OUTDIR, 'archive')
TIMESTAMPED_OUTDIR = os.path.join(
    ARCHIVEDIR, datetime.datetime.now().strftime('%Y-%m-%d_%H%M'))
CRASHED = 'Calculation core crashes'
SOME_ERROR = 'Model loading problems'
LOADED = 'Loaded fine'

EPSILON = 0.000001

INVALID_DESIRED_VALUE = 1234567890  # Hardcoded in the template, too.
MODEL_PARAMETERS = (
    ('geometry', 'BathymetryFile'),
    ('grid', 'GridSpace'),
    ('grid', 'kmax'),
    ('grid', 'BathDelta'),
    ('time', 'Dt'),
    ('Ground Water', 'NumLayers'),
    ('numerics', 'Teta'),
    ('numerics', 'Advection'),
)


def unmask(something):
    """Some numbers come out as numpy masked numbers. Fix that.

    Json barfs on it, that's wy."""
    if something is None:
        return None
    try:
        return float(something)
    except:
        return str(something)


class InstructionReport(object):

    def __init__(self):
        self.log = None
        self.id = None
        self.parameter = None
        self.desired = None
        self.margin = None
        self.found = None
        self.equal = None
        self.title = None
        self.invalid_desired_value = None
        self.what = []
        self.instruction_id = None
        self.image_relpath = None

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    def as_dict(self):
        equal = bool(self.equal)
        return dict(
            log=self.log,
            id=self.id,
            parameter=unmask(self.parameter),
            desired=self.desired,
            margin=unmask(self.margin),
            epsilon=unmask(self.epsilon),
            found=unmask(self.found),
            equal=equal,
            title=self.title,
            invalid_desired_value=self.invalid_desired_value,
            shortlog=self.shortlog,
            what=self.what,
            epsilon_found=unmask(self.epsilon_found),
            margin_found=unmask(self.margin_found),
            instruction_id=self.instruction_id,
            image_relpath=self.image_relpath,
        )

    @property
    def shortlog(self):
        if self.log is None:
            return ''
        if len(self.log) < 400:
            return self.log
        return self.log[:200] + ' ... ' + self.log[-200:]

    @property
    def epsilon(self):
        """Return allowed margin (positive)."""
        if self.margin is None:
            return EPSILON
        relative = '%' in self.margin
        margin = self.margin.replace('%', '')
        if self.desired == 'nan':
            return
        try:
            margin = float(margin)
        except ValueError:
            logger.exception("Wrong 'margin' value: %s", margin)
            return EPSILON
        if relative:
            if self.found is None:  # Corner case.
                return 0
            return abs(self.desired) / 100 * margin
        else:
            return abs(margin)

    @property
    def epsilon_found(self):
        if (self.found is None or self.desired is None
                or self.desired == 'nan'):
            return
        return abs(self.found - self.desired)

    @property
    def margin_found(self):
        if not self.epsilon_found:
            return
        if not self.found:  # Division by zero.
            return
        return self.epsilon_found / abs(self.desired) * 100


class MduReport(object):

    def __init__(self, mdu_filepath, test_run_id=None):
        self.log = None
        self.successfully_loaded_log = None
        self.id = mdu_filepath
        self.instruction_reports = defaultdict(InstructionReport)
        self.loadable = True
        self.status = None
        self.index_lines = []
        self.csv_contents = []
        self.model_parameters = []

        # test_run_id is needed to uniquely save the plots
        self.test_run_id = test_run_id

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    def as_dict(self):
        # Basically: what ends up in mdu.html as context.
        result = dict(
            loadable=self.loadable,
            short_title=self.short_title,
            index_lines=self.index_lines,
            log=self.log,
            successfully_loaded_log=None,  # No verbosity at the moment
            log_summary=self.log and self.log_summary or None,
            csv_contents=self.csv_contents,
            model_parameters=self.model_parameters,
            instruction_reports=[],
            )
        for instruction_report in self.instruction_reports.values():
            result['instruction_reports'].append(instruction_report.as_dict())
        return result

    def _propagate_ids(self):
        for instruction_id in self.instruction_reports:
            instruction_report = self.instruction_reports[
                instruction_id]
            instruction_report.id = instruction_id

    @property
    def log_filename(self):
        id = self.id.replace('/', '-')
        return 'mdu_log_%s.html' % id

    def record_instructions(self, instructions, csv_filename):
        """Store a good representation of the csv instructions."""
        contents = json.dumps(instructions, indent=4)
        self.csv_contents.append({'filename': csv_filename,
                                  'contents': contents})

    @property
    def details_filename(self):
        name = '/{}/'.format(settings.TESTCASES_ROOT_NAME)
        id = self.id.split(name)[1]
        id = id.replace('/', '-')
        return 'details_%s.html' % id

    @property
    def log_summary(self):
        last_lines = self.log.split('\n')[-3:]
        return '\n'.join(last_lines)

    @property
    def title(self):
        name = '/{}/'.format(settings.TESTCASES_ROOT_NAME)
        try:
            title = self.id.split(name)[1]
        except Exception as e:
            logger.exception(e)
            title = "FIXTITLEPROPERTY"
        return title

    @property
    def short_title(self):
        parts = self.title.split('/')
        short = parts[-1]
        short = short.rstrip('.mdu')
        short = short.replace('_', ' ')
        return short

    @property
    def instructions(self):
        return sorted(self.instruction_reports.values())

    @property
    def overall_status(self):
        """Return number of instructions; used for table rowspan."""
        correct_results = [instruction for instruction in self.instructions
                           if instruction.equal]
        wrong_results = [instruction for instruction in self.instructions
                         if not instruction.equal]
        # Hardcoded values
        if len(wrong_results) == 0:
            return 'GOOD'
        if len(correct_results) > len(wrong_results):
            return 'PARTIALLY'
        return 'WRONG'


class InpReport(MduReport):
    """A version of the MduReport for the flow lib"""

    def __init__(self, path, *args, **kwargs):
        super(InpReport, self).__init__(path, *args, **kwargs)
        self.input_files = []

    def as_dict(self):
        # Basically: what ends up in mdu.html as context.
        result = dict(
            loadable=self.loadable,
            short_title=self.short_title,
            index_lines=self.index_lines,
            log=self.log,
            successfully_loaded_log=None,  # No verbosity at the moment
            log_summary=self.log and self.log_summary or None,
            csv_contents=self.csv_contents,
            model_parameters=self.model_parameters,
            input_files=self.input_files,
            instruction_reports=[],
            )
        for instruction_report in self.instruction_reports.values():
            result['instruction_reports'].append(instruction_report.as_dict())
        return result

    @property
    def log_filename(self):
        # TODO: overrride?
        id = self.id.replace('/', '-')
        return 'mdu_log_%s.html' % id

    @property
    def details_filename(self):
        name = '/{}/'.format(settings.URBAN_TESTCASES_ROOT_NAME)
        id = self.id.split(name)[1]
        id = id.replace('/', '-')
        return 'details_%s.html' % id

    @property
    def title(self):
        name = '/{}/'.format(settings.URBAN_TESTCASES_ROOT_NAME)
        try:
            title = self.id.split(name)[1]
        except Exception as e:
            logger.exception(e)
            title = "FIXTITLEPROPERTYFORFLOW"
        return title

    @property
    def short_title(self):
        parts = self.title.split('/')
        short = parts[-1]
        short = short.replace('_', ' ')
        return short


class Report(object):

    def __init__(self):
        self.mdu_reports = defaultdict(MduReport)

    def write_template(self, template_name, outfile=None, title=None,
                       context=None):
        if context is None:
            context = {}
        if not os.path.exists(TIMESTAMPED_OUTDIR):
            os.mkdir(TIMESTAMPED_OUTDIR)
        if outfile is None:
            outfile = template_name
        outfile1 = os.path.join(OUTDIR, outfile)
        outfile2 = os.path.join(TIMESTAMPED_OUTDIR, outfile)
        template = jinja_env.get_template(template_name)
        open(outfile1, 'w').write(template.render(view=self,
                                                  title=title,
                                                  context=context))
        static = '../../'
        open(outfile2, 'w').write(template.render(view=self,
                                                  title=title,
                                                  context=context,
                                                  static=static))
        logger.debug("Wrote %s and %s", outfile1, outfile2)

    def _propagate_ids(self):
        for mdu_id in self.mdu_reports:
            mdu_report = self.mdu_reports[mdu_id]
            mdu_report.id = mdu_id
            mdu_report._propagage_ids()

    @property
    def mdus(self):
        return sorted(self.mdu_reports.values())

    @property
    def problem_mdus(self):
        return [mdu for mdu in self.mdus
                if mdu.status in [CRASHED, SOME_ERROR]]

    @property
    def loaded_mdus(self):
        return [mdu for mdu in self.mdus
                if mdu.status not in [CRASHED, SOME_ERROR]]

    @property
    def summary_items(self):
        result = []
        for status in [CRASHED, SOME_ERROR, LOADED]:
            number = len([mdu for mdu in self.mdus if mdu.status == status])
            result.append("%s: %s" % (status, number))
        successful_tests = 0
        failed_tests = 0
        errored_tests = 0
        for mdu in self.mdus:
            for instruction in mdu.instructions:
                if instruction.equal:
                    successful_tests += 1
                elif instruction.log:
                    errored_tests += 1
                else:
                    failed_tests += 1
        result.append("Tests with setup errors: %s" % errored_tests)
        result.append("Failed tests: %s" % failed_tests)
        result.append("Successful tests: %s" % successful_tests)
        return result

    def export_reports(self):
        self._propagate_ids()
        self.write_template('index.html',
                            title='Overview')
        for mdu in self.mdu_reports.values():
            self.write_template('mdu.html',
                                title=mdu.title,
                                outfile=mdu.details_filename,
                                context=mdu)


def _desired_time_index(instruction, instruction_report, dataset):
    """Look up the time (array) index (or indices in case of SUM) in the
       netcdf, based on the time value
    """
    # Time
    desired_time = instruction['time']
    if desired_time == 'SUM':
        logger.debug("We want to sum all time values")
        instruction_report.what.append("sum of all times")
        desired_time_index = slice(None)  # [:]
    else:
        desired_time = float(desired_time)
        logger.debug("Desired time: %s", desired_time)
        # TODO: less brute force, if possible.
        time_values = list(dataset.variables['time'][:])
        try:
            desired_time_index = time_values.index(desired_time)
        except ValueError:
            # Re-try because we often see a time '1800.0' that doesn't match a
            # time '1800.0517' or something like that. Can't hurt to do a bit
            # of rounding.
            desired_rounded_time = round(desired_time)
            rounded_time_values = [round(value) for value in time_values]
            try:
                desired_time_index = rounded_time_values.index(
                    desired_rounded_time)
                logger.warn("Didn't find proper time %s, but after rounding "
                            "we did find %s",
                            desired_time,
                            time_values[desired_time_index])
            except ValueError:
                msg = "Time %s not found in %s" % (desired_time,
                                                   time_values)
                instruction_report.log = msg
                logger.error(msg)
                return
        instruction_report.what.append("time value %s at index %s" % (
            desired_time, desired_time_index))
    return desired_time_index


def _value_lookup(dataset, parameter_name, desired_time_index, location_index,
                  instruction_report):
    values = dataset.variables[parameter_name]
    logger.debug("Shape before looking up times/location: %r", values.shape)
    try:
        logger.debug("Looking up time %r and location %r",
                     desired_time_index, location_index)
        values = values[desired_time_index, location_index]
    except IndexError:
        msg = "Index (%r, %r) not found. Shape of values is %r." % (
            desired_time_index, location_index, values.shape)
        instruction_report.log = msg
        logger.error(msg)
        return
    except MemoryError:
        msg = "Index (%r, %r) not found because of memory error. Shape of values is %r." % (
            desired_time_index, location_index, values.shape)
        instruction_report.log = msg
        logger.exception(msg)
        return

    logger.debug("Shape after looking up times and location: %r", values.shape)
    return values.sum()


def check_his(instruction, instruction_report, dataset):
    """History check.

    History checks work with observation points (which are present in
    the netcdf file). The value we need to grab is an observation
    name, a time and a parameter.

    """
    logger.debug("Checking his")
    # Admin stuff.
    instruction_report.title = instruction['note']

    # Parameter.
    parameter_name = instruction['param']
    instruction_report.parameter = parameter_name
    if parameter_name not in dataset.variables:
        msg = "Parameter '%s' not found in %s" % (
            parameter_name,
            dataset.variables.keys())
        instruction_report.log = msg
        logger.error(msg)
        return

    # Expected value
    try:
        if instruction['ref'] == 'nan':
            desired = 'nan'
        else:
            desired = float(instruction['ref'])
    except ValueError:
        desired = instruction['ref']
        msg = "Invalid non-float value: %r" % desired
        instruction_report.invalid_desired_value = msg
        logger.error(msg)
        desired = INVALID_DESIRED_VALUE
    instruction_report.desired = desired

    # Margin
    if instruction.get('margin'):
        margin = instruction['margin']
        instruction_report.margin = margin

    if 'obs_name' in instruction:
        # Observation point
        station_name = instruction['obs_name']

        # Special case, error that occurs in practice
        if 'station_name' not in dataset.variables:
            msg = ("Variable 'station_name' not found in the netcdf. " +
                   "Wrong kind of _his.csv check")
            instruction_report.log = msg
            logger.error(msg)
            return

        station_names = list(
            [''.join(name.data)
             for name in dataset.variables['station_name'][:]])
        try:
            location_index = station_names.index(station_name)
        except ValueError:
            msg = "Station name %s not found in %r." % (
                station_name, station_names)
            instruction_report.log = msg
            logger.error(msg)
            return

        msg = "Using station name %s at index %s." % (
            station_name, location_index)
        instruction_report.what.append(msg)
        logger.debug(msg)

        # Time
        desired_time_index = _desired_time_index(instruction,
                                                 instruction_report,
                                                 dataset)
        if desired_time_index is None:
            return

        # Value lookup.
        found = _value_lookup(dataset, parameter_name, desired_time_index,
                              location_index, instruction_report)
        if found is None:
            return

        instruction_report.found = found
        if desired == 'nan':
            if type(found) == np.ma.core.MaskedConstant:
                instruction_report.equal = True
            else:
                instruction_report.equal = False
        else:
            instruction_report.equal = (
                abs(desired - found) < instruction_report.epsilon)
        logger.info("Found value %s for parameter %s; desired=%s",
                    found,
                    parameter_name,
                    desired)
    else:
        # cross section
        assert 'cross_section_name' in instruction
        cross_section_name = instruction['cross_section_name']
        cross_section_names = list(
            [''.join(name.data)
             for name in dataset.variables['cross_section_name'][:]])
        try:
            location_index = cross_section_names.index(cross_section_name)
        except ValueError:
            msg = "Cross section name %s not found in %r." % (
                cross_section_name, cross_section_names)
            instruction_report.log = msg
            logger.error(msg)
            return

        msg = "Using cross section name %s at index %s." % (
            cross_section_name, location_index)
        instruction_report.what.append(msg)
        logger.debug(msg)

        # Time
        desired_time_index = _desired_time_index(instruction,
                                                 instruction_report,
                                                 dataset)
        if desired_time_index is None:
            return

        # Value lookup.
        found = _value_lookup(dataset, parameter_name, desired_time_index,
                              location_index, instruction_report)
        if found is None:
            return

        instruction_report.found = found
        if desired == 'nan':
            if type(found) == np.ma.core.MaskedConstant:
                instruction_report.equal = True
            else:
                instruction_report.equal = False
        else:
            instruction_report.equal = (
                abs(desired - found) < instruction_report.epsilon)
        logger.info("Found value %s for parameter %s; desired=%s",
                    found,
                    parameter_name,
                    desired)


def check_map(instruction, instruction_report, dataset, instruction_id=None,
              test_run_id=None):
    logger.debug("Checking regular map")
    # Admin stuff
    instruction_report.title = instruction['note']

    # Parameter
    parameter_name = instruction['param']
    instruction_report.parameter = parameter_name
    if parameter_name not in dataset.variables:
        msg = "Parameter '%s' not found in %s" % (
            parameter_name,
            dataset.variables.keys())
        instruction_report.log = msg
        logger.error(msg)
        return

    # Expected value
    try:
        if instruction['ref'] == 'nan':
            desired = 'nan'
        else:
            desired = float(instruction['ref'])
    except ValueError:
        desired = instruction['ref']
        msg = "Invalid non-float value: %r" % desired
        instruction_report.invalid_desired_value = msg
        logger.error(msg)
        desired = INVALID_DESIRED_VALUE
    instruction_report.desired = desired

    # Margin
    if instruction.get('margin'):
        margin = instruction['margin']
        instruction_report.margin = margin

    # x/y lookup
    if not ('x' in instruction and 'y' in instruction):
        msg = "x and/or y not found in instruction: %r" % (
            instruction.keys())
        instruction_report.log = msg
        logger.error(msg)
        return
    x = float(instruction['x'])
    y = float(instruction['y'])
    # TODO: SUM

    fcx = dataset.variables['FlowElemContour_x']
    fcy = dataset.variables['FlowElemContour_y']
    x1 = fcx[:].min(1)
    x2 = fcx[:].max(1)
    y1 = fcy[:].min(1)
    y2 = fcy[:].max(1)
    # Find the quad ("FlowElem") at point x, y
    quad = np.logical_and(
        np.logical_and(
            x1 <= x,
            x2 >= x,
        ),
        np.logical_and(
            y1 <= y,
            y2 >= y,
        ),
    )
    # quad is a [False, False, True, False] mask.
    try:
        location_index = [index for index, value in enumerate(quad)
                          if value][0]
        # ^^^ TODO: Is this right?
    except IndexError:
        msg = "x=%s, y=%s not found in grid" % (x, y)
        instruction_report.log = msg
        logger.error(msg)
        return
    instruction_report.what.append("quad number %s (x=%s, y=%s)" % (
        location_index, x, y))

    # Time
    desired_time_index = _desired_time_index(instruction,
                                             instruction_report,
                                             dataset)
    if desired_time_index is None:
        return

    # Value lookup.
    found = _value_lookup(dataset, parameter_name, desired_time_index,
                          location_index, instruction_report)
    if found is None:
        return

    instruction_report.found = found
    if desired == 'nan':
        if type(found) == np.ma.core.MaskedConstant:
            instruction_report.equal = True
        else:
            instruction_report.equal = False
    else:
        instruction_report.equal = (
            abs(desired - found) < instruction_report.epsilon)
    logger.info("Found value %s for parameter %s; desired=%s",
                found,
                parameter_name,
                desired)
    plot_it(dataset, parameter_name, desired_time_index, location_index,
            instruction_report, instruction_id=instruction_id,
            test_run_id=test_run_id)


def check_map_nflow(instruction, instruction_report, dataset,
                    instruction_id=None, test_run_id=None):
    """
    Check an instruction where the node is already given (nFlowElem, nFlowLink)

    Params:
        instruction: a single csv instruction (type: dict)
        instruction_report: one line of the report (generated from instruction)
        dataset: the netcdf dataset
        instruction_id: generated string of the instruction
        test_run_id: is just being passed on for the plot generation
    """
    logger.debug("Checking nflow")
    # Admin stuff.
    instruction_report.title = instruction['note']

    # Parameter.
    parameter_name = instruction['param']
    instruction_report.parameter = parameter_name
    if parameter_name not in dataset.variables:
        msg = "Parameter '%s' not found in %s" % (
            parameter_name,
            dataset.variables.keys())
        instruction_report.log = msg
        logger.error(msg)
        return

    # Expected value
    try:
        if instruction['ref'] == 'nan':
            desired = 'nan'
        else:
            desired = float(instruction['ref'])
    except ValueError:
        desired = instruction['ref']
        msg = "Invalid non-float value: %r" % desired
        instruction_report.invalid_desired_value = msg
        logger.error(msg)
        desired = INVALID_DESIRED_VALUE
    instruction_report.desired = desired

    # Margin
    if instruction.get('margin'):
        instruction_report.margin = instruction['margin']

    # nflow (get node number(s))
    if 'nFlowElem' in instruction:
        location_index = instruction['nFlowElem']
        logger.debug("Using nFlowElem %s", location_index)
    else:
        location_index = instruction['nFlowLink']
        logger.debug("Using nFlowLink %s", location_index)

    if location_index == 'SUM':
        location_index = slice(None)  # [:]
        instruction_report.what.append("sum of all flow items")
    else:
        location_index = int(location_index)
        instruction_report.what.append(
            "nFlowLink at index %s" % location_index)

    # Time
    desired_time_index = _desired_time_index(instruction,
                                             instruction_report,
                                             dataset)
    if desired_time_index is None:
        return

    # Value lookup.
    found = _value_lookup(dataset, parameter_name, desired_time_index,
                          location_index, instruction_report)
    if found is None:
        return

    instruction_report.found = found
    if desired == 'nan':
        if type(found) == np.ma.core.MaskedConstant:
            instruction_report.equal = True
        else:
            instruction_report.equal = False
    else:
        instruction_report.equal = (
            abs(desired - found) < instruction_report.epsilon)
    logger.info("Found value %s for parameter %s; desired=%s",
                found,
                parameter_name,
                desired)
    plot_it(dataset, parameter_name, desired_time_index, location_index,
            instruction_report, instruction_id=instruction_id,
            test_run_id=test_run_id)


def plot_it(dataset, parameter_name, desired_time_index, location_index,
            instruction_report, instruction_id=None, test_run_id=None):
    """Helper function for calling the actual plotting function"""
    if not np.isscalar(location_index):  # type(location_index) == slice
        # TODO: implement if location index is a range of values
        logger.debug("Can't plot because of 'SUM' of location_index")
        logger.debug("location_index: %s", location_index)
        return
    if not np.isscalar(desired_time_index):
        # TODO: implement plotting when using a range of time values
        logger.debug("Can't plot because of 'SUM' of desired_time_index")
        logger.debug("desired_time_index: %s", desired_time_index)
        return

    if instruction_id:
        # construct MEDIA_ROOT path for saving images while preserving model
        # dir structure
        cwd = os.getcwd()
        model_relpath = os.path.relpath(cwd, settings.BUILDOUT_DIR)

        # NOTE: test_run_id is to identify the plots per test run
        img_path = os.path.join(
            settings.MEDIA_ROOT, model_relpath, str(test_run_id),
            instruction_id + '.png')
        instruction_report.image_relpath = os.path.relpath(img_path,
                                                           settings.MEDIA_ROOT)
        make_time_plot(dataset, parameter_name, desired_time_index,
                       location_index, imgname=img_path)


def make_time_plot(dataset, parameter, time_idx, location_idx,
                   imgname=None):
    """
    Make a nice plot of the parameter w.r.t. time

    Params:
        dataset: netcdf dataset
        parameter: the quantity
        time_idx: index of the time value or a list of indices if 'SUM' is
                  used!
        location_idx: the node index; this can be a range of indices if 'SUM'
                      option is chosen!
        imgname: full path to img file
    """
    # TODO: check if 'SUM' is used; if so, time_idx is not an integer but a
    # list of ints!

    if not imgname:
        raise Exception("No image name given")
    values = dataset.variables[parameter]  # -> values[time_idx, location_idx]
    logger.debug("Shape before plotting: %r", values.shape)

    # determine x, y axis limits (pretty ad hoc)
    n_time_indices = values.shape[0]
    t_domain_size = n_time_indices/10.   # the fraction is arbitrary
    _t_lower = time_idx - t_domain_size if time_idx - t_domain_size >= 0 else \
        time_idx - t_domain_size * 0.2
    _t_upper = time_idx + t_domain_size + 1 if \
        time_idx + t_domain_size + 1 <= n_time_indices else \
        time_idx + t_domain_size * 0.2
    t_lower = math.floor(_t_lower)
    t_upper = math.ceil(_t_upper)
    ymax = values[:, location_idx].max()
    ymin = values[:, location_idx].min()
    yrange = abs(ymax - ymin) if ymax - ymin > 0 else max(abs(ymax), abs(ymin))
    y_lower = ymin - abs(0.25*yrange)
    y_upper = ymax + abs(0.25*yrange)

    # plot values + found value
    plt.plot(values[:, location_idx])
    plt.plot(time_idx, values[time_idx, location_idx], 'ro')

    # plot a vertical dashed line
    plt.axvline(x=time_idx, color='red', linestyle='--')

    # adjust axes
    plt.xlim(t_lower, t_upper)
    plt.ylim(y_lower, y_upper)
    plt.ticklabel_format(useOffset=False)

    # ticks
    plt.locator_params(axis='x', nbins=4, tight=False)  # reduce ticks
    plt.locator_params(axis='y', nbins=5, tight=False)  # reduce ticks

    # make dir if it doesn't exist
    dir_path = os.path.dirname(imgname)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # save it
    F = plt.gcf()
    DefaultSize = F.get_size_inches()
    F.set_size_inches((DefaultSize[0]*0.2, DefaultSize[1]*0.2))
    F.savefig(imgname, dpi=50, bbox_inches='tight')
    plt.close("all")


def make_spatial_plot():
    pass
    # xcc = dataset.variables['FlowElem_xcc']
    # ycc = dataset.variables['FlowElem_ycc']
    # v = values[:,-1]
    # N = matplotlib.colors.Normalize(9.5-(1e-6), 9.5 + (1e-6))
    # plt.scatter(xcc, ycc, c=matplotlib.cm.hsv(N(v)), s=10, edgecolor='none')


def check_csv(csv_filename, netcdf_path=None, mdu_report=None, is_his=False):
    """Parse the csvs as "instructions" and run the instructions on the netcdf
       Params:
            csv_filename: name of csv file (we are in the model folder)]
            netcdf_path: path to netcdf file
            mdu_report: MduReport or InpReport (thing shown in testrun view)
            is_his: boolean checking if the netcdf is called 'subgrid_his.nc'
    """
    with open(csv_filename) as csvfile:
        instructions = list(csv.DictReader(csvfile, delimiter=';'))
    mdu_report.record_instructions(instructions, csv_filename)

    with Dataset(netcdf_path) as dataset:
        for test_number, instruction in enumerate(instructions):
            instruction_id = "{} - {}".format(
                os.path.splitext(csv_filename)[0], str(test_number))
            instruction_report = mdu_report.instruction_reports[instruction_id]
            instruction_report.instruction_id = instruction_id

            # The checks are built around some ad hoc patterns:
            if is_his:
                check_his(instruction, instruction_report, dataset)
            else:
                if ('nFlowLink' in instruction or 'nFlowElem' in instruction):
                    check_map_nflow(instruction, instruction_report, dataset,
                                    instruction_id=instruction_id,
                                    test_run_id=mdu_report.test_run_id)
                else:
                    check_map(instruction, instruction_report, dataset,
                              instruction_id=instruction_id,
                              test_run_id=mdu_report.test_run_id)


def model_parameters(mdu_filepath):
    """Return parameter/value pairs from the mdu."""
    config = ConfigParser.ConfigParser()
    config.readfp(open(mdu_filepath))
    for section, parameter in MODEL_PARAMETERS:
        try:
            value = config.get(section, parameter)
        except ConfigParser.NoSectionError:
            value = "(Section %s not found)" % section
        except ConfigParser.NoOptionError:
            value = "(parameter not found)"
        value = value.split('#')[0]
        yield parameter, value


def input_files(model_dir):
    """Just return the contents of the input files"""
    ini_files = glob.glob(os.path.join(os.path.abspath(model_dir), '*.ini'))
    if len(ini_files) != 1:
        logger.error("No or more than one ini file found. ini_files: %s",
                     ini_files)
        return
    ini_file = ini_files[0]
    variant_path = os.path.join(model_dir, os.path.splitext(ini_file)[0])
    input_generated_dir = os.path.join(variant_path, 'input_generated')

    # will capture 'input.  1' and 'input_grid_gen.  1'
    pattern = os.path.join(input_generated_dir, 'input*')
    inp_file_names = glob.glob(pattern)
    logger.debug("Found the following input files: %s", inp_file_names)
    txts = []
    for fn in inp_file_names:
        with open(fn, 'r') as f:
            filename = fn.split('/')[-1]
            txts.append((filename, f.read()))
    return txts


def check_mdu_file(mdu_filepath):
    for line in open(mdu_filepath):
        if line.startswith('NTimesteps'):
            if '20160' in line:
                msg = "Wrong default 20160 NTimesteps value in %s:\n%s" % (
                    mdu_filepath, line)
                return msg


def run_flow_simulation(model_dir, inp_report=None, verbose=False):
    """
    Run simulation using python-flow

    Params:
        model_dir: path to the model dir
        inp_report: formerly mdu_report
    """
    original_dir = os.getcwd()
    os.chdir(model_dir)
    # os.chdir("..")
    if 'index.txt' in os.listdir('.'):
        inp_report.index_lines = open('index.txt').readlines()
    logger.debug("Loading %s...", model_dir)
    buildout_dir = original_dir

    pyflow = os.path.join(buildout_dir, 'bin', 'pyflow')
    ini_files = glob.glob(os.path.join(os.path.abspath(model_dir), '*.ini'))
    if len(ini_files) != 1:
        logger.error("No or more than one ini file found. ini_files: %s",
                     ini_files)
        return
    ini_file = ini_files[0]
    ini_name = os.path.splitext(ini_file)[0]
    variant_dir = os.path.join(model_dir, ini_name)
    cmd = '%s %s -m -o debug' % (pyflow, ini_file)
    logger.debug("Running %s", cmd)
    exit_code, output = system(cmd)
    last_output = ''.join(output.split('\n')[-2:]).lower()

    if verbose:
        logger.info(output)
    if exit_code or ('error' in last_output
                     and 'quitting' in last_output):
        logger.error("Loading failed: %s", model_dir)
        inp_report.loadable = False
        inp_report.log = output
        if 'Segmentation fault' in output:
            inp_report.status = CRASHED
        else:
            inp_report.status = SOME_ERROR
    else:
        inp_report.status = LOADED
        logger.info("Successfully loaded: %s", model_dir)
        inp_report.successfully_loaded_log = output
        inp_report.input_files = input_files(model_dir)
        csv_filenames = [f for f in os.listdir('.') if f.endswith('.csv')]
        for csv_filename in csv_filenames:
            logger.info("Reading instructions from %s", csv_filename)
            netcdf_path = os.path.join(ini_name, 'results/subgrid_map.nc')
            check_csv(csv_filename, netcdf_path, mdu_report=inp_report)

    # Cleanup results
    for f in os.listdir(os.path.join(variant_dir,'results')):
        item = os.path.join(os.path.join(variant_dir,'results'), f)
        if os.path.isfile(item):
            os.remove(item)
    # Also delete makegrid files because of interference with 'hg update'
    for f in os.listdir(os.path.join(variant_dir, 'preprocessed')):
        item = os.path.join(os.path.join(variant_dir, 'preprocessed'), f)
        if os.path.isfile(item):
            os.remove(item)

    os.chdir(original_dir)


def run_subgrid_simulation(mdu_filepath, mdu_report=None, verbose=False):
    original_dir = os.getcwd()
    os.chdir(os.path.dirname(mdu_filepath))
    if 'index.txt' in os.listdir('.'):
        mdu_report.index_lines = open('index.txt').readlines()
    logger.debug("Loading %s...", mdu_filepath)

    mdu_error = check_mdu_file(mdu_filepath)
    if mdu_error:
        # Temp check for faulty default NTimesteps value
        logger.error(mdu_error)
        mdu_report.loadable = False
        mdu_report.log = mdu_error
        mdu_report.status = SOME_ERROR
        os.chdir(original_dir)
        return

    # cmd = '/opt/3di/bin/subgridf90 %s --autostartstop --nodisplay' % os.path.basename(
    #     mdu_filepath)
    # ^^^ Direct subgrid executable call
    # Below: new via-the-library call
    buildout_dir = original_dir
    # kill_after_timeout_command = "timeout 5m"
    #subgridpy = os.path.join(buildout_dir, 'bin', 'subgridpy')
    subgridpy = os.path.join(buildout_dir, 'bin', 'simplesubgrid')
    cmd = '%s %s' % (subgridpy, os.path.basename(mdu_filepath))
    logger.debug("Running %s", cmd)
    exit_code, output = system(cmd)
    last_output = ''.join(output.split('\n')[-2:]).lower()
    if verbose:
        logger.info(output)
    if exit_code or ('error' in last_output
                     and 'quitting' in last_output):
        logger.error("Loading failed: %s", mdu_filepath)
        mdu_report.loadable = False
        mdu_report.log = output
        if 'Segmentation fault' in output:
            mdu_report.status = CRASHED
        else:
            mdu_report.status = SOME_ERROR
    else:
        mdu_report.status = LOADED
        logger.info("Successfully loaded: %s", mdu_filepath)
        mdu_report.successfully_loaded_log = output
        mdu_report.model_parameters = list(model_parameters(mdu_filepath))
        csv_filenames = [f for f in os.listdir('.') if f.endswith('.csv')]
        for csv_filename in csv_filenames:
            logger.info("Reading instructions from %s", csv_filename)
            is_his = False
            if 'his' in csv_filename:
                netcdf_path = 'subgrid_his.nc'
                is_his = True
            else:
                netcdf_path = 'subgrid_map.nc'
            check_csv(csv_filename, netcdf_path, mdu_report=mdu_report,
                      is_his=is_his)

    # Cleanup: zap *.nc files.
    for nc in [f for f in os.listdir('.') if f.endswith('.nc')]:
        os.remove(nc)

    os.chdir(original_dir)


def mdu_filepaths(basedir):
    """Iterator that yields full paths to .mdu files."""
    basedir = os.path.abspath(basedir)
    for dirpath, dirnames, filenames in os.walk(basedir):
        mdu_filenames = [f for f in filenames if f.endswith('.mdu')]
        for mdu_filename in mdu_filenames:
            yield os.path.join(dirpath, mdu_filename)


def create_archive_index():
    """Write an index.html file for the archive/* directories."""
    archive_dirs = [filename for filename in os.listdir(ARCHIVEDIR)
                    if os.path.isdir(os.path.join(ARCHIVEDIR, filename))]
    archive_dirs.sort()
    archive_dirs.reverse()
    template = jinja_env.get_template('archive.html')
    outfile = os.path.join(ARCHIVEDIR, 'index.html')
    view = {'archive_dirs': archive_dirs}
    static = '../'
    open(outfile, 'w').write(template.render(
        view=view,
        title='Archive of previous tests',
        static=static))


def main():
    parser = argparse.ArgumentParser(
        description='Run verification tests on the "unit test" models.')
    parser.add_argument('directory',
                        nargs='?',
                        default='.',
                        help='directory with the tests')
    parser.add_argument('testcase',
                        default=None,
                        help="testcase to run (like 4_09_07)")
    parser.add_argument('--verbose', default=False, action='store_true')
    args = parser.parse_args()
    report = Report()
    logging.basicConfig(level=logging.DEBUG)
    for mdu_filepath in mdu_filepaths(args.directory):
        if args.testcase and (args.testcase not in mdu_filepath):
            continue
        run_subgrid_simulation(mdu_filepath, mdu_report=report,
                               verbose=args.verbose)
    report.export_reports()
    create_archive_index()
