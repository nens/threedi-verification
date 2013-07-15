"""
This module provides functions for running verification checks on small 
models and to create reports about them.

"""
from __future__ import print_function
from collections import defaultdict
import argparse
import csv
import datetime
import json
import logging
import os
import shutil

from netCDF4 import Dataset
import numpy as np
from jinja2 import Environment, PackageLoader

from threedi_verification.utils import system

jinja_env = Environment(loader=PackageLoader('threedi_verification', 'templates'))
logger = logging.getLogger(__name__)

OUTDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                      '..', 'var', 'html'))
TIMESTAMPED_OUTDIR = os.path.join(
    OUTDIR, datetime.datetime.now().strftime('%Y-%m-%d_%H%M'))
CRASHED = 'Calculation core crashes'
SOME_ERROR = 'Model loading problems'
LOADED = 'Loaded fine'

INVALID_DESIRED_VALUE = 1234567890  # Hardcoded in the template, too.


class InstructionReport(object):

    def __init__(self):
        self.log = None
        self.id = None
        self.parameter = None
        self.desired = None
        self.found = None
        self.equal = None
        self.title = None
        self.invalid_desired_value = None
        self.what = []

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    @property
    def shortlog(self):
        if self.log is None:
            return ''
        if len(self.log) < 400:
            return self.log
        return self.log[:200] + ' ... ' + self.log[-200:]


class MduReport(object):

    def __init__(self):
        self.log = None
        self.successfully_loaded_log = None
        self.id = None
        self.instruction_reports = defaultdict(InstructionReport)
        self.loadable = True
        self.status = None
        self.index_lines = []
        self.csv_contents = []

    def __cmp__(self, other):
        return cmp(self.id, other.id)

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
        id = self.id.split('/testbank/')[1]
        id = id.replace('/', '-')
        return 'details_%s.html' % id

    @property
    def log_summary(self):
        last_lines = self.log.split('\n')[-3:]
        return '\n'.join(last_lines)

    @property
    def title(self):
        return self.id.split('/testbank/')[1]

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
    def num_instructions(self):
        """Return number of instructions; used for table rowspan."""
        return len(self.instructions)


class Report(object):

    def __init__(self):
        self.mdu_reports = defaultdict(MduReport)

    def write_template(self, template_name, outfile=None, title=None, 
                       context=None):
        if not os.path.exists(TIMESTAMPED_OUTDIR):
            os.mkdir(TIMESTAMPED_OUTDIR)
        if outfile is None:
            outfile = template_name
        outfile1 = os.path.join(OUTDIR, outfile)
        template = jinja_env.get_template(template_name)
        open(outfile1, 'w').write(template.render(view=self, 
                                                  title=title, 
                                                  context=context))
        outfile2 = os.path.join(TIMESTAMPED_OUTDIR, outfile)
        shutil.copy(outfile1, outfile2)
        logger.debug("Wrote %s and %s", outfile1, outfile2)

    def _propagate_ids(self):
        for mdu_id in self.mdu_reports:
            mdu_report = self.mdu_reports[mdu_id]
            mdu_report.id = mdu_id
            for instruction_id in mdu_report.instruction_reports:
                instruction_report = mdu_report.instruction_reports[
                    instruction_id]
                instruction_report.id = instruction_id

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

                    
report = Report()


def _desired_time_index(instruction, instruction_report, dataset):
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
            msg = "Time %s not found in %s" % (desired_time, 
                                               time_values)
            instruction_report.log = msg
            logger.error(msg)
            return
        instruction_report.what.append("time value %s at index %s" % (
            desired_time, desired_time_index))
    return desired_time_index


def _value_lookup(dataset, parameter_name, desired_time_index, location_index, instruction_report):
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
    if not parameter_name in dataset.variables:
        msg = "Parameter '%s' not found in %s" % (
            parameter_name,
            dataset.variables.keys())
        instruction_report.log = msg
        logger.error(msg)
        return

    # Expected value
    try:
        desired = float(instruction['ref'])
    except ValueError:
        desired = instruction['ref']
        msg = "Invalid non-float value: %r" % desired
        instruction_report.invalid_desired_value = msg
        logger.error(msg)
        desired = INVALID_DESIRED_VALUE
    instruction_report.desired = desired

    # Observation point
    station_name = instruction['obs_name']
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
    desired_time_index = _desired_time_index(instruction, instruction_report, dataset)
    if desired_time_index is None:
        return

    # Value lookup.
    found = _value_lookup(dataset, parameter_name, desired_time_index, location_index, instruction_report)
    if found is None:
        return

    instruction_report.found = found
    instruction_report.equal = (abs(desired - found) < 0.001)
    logger.info("Found value %s for parameter %s; desired=%s", 
                found,
                parameter_name,
                desired)


def check_map(instruction, instruction_report, dataset):
    logger.debug("Checking regular map")
    # Admin stuff
    instruction_report.title = instruction['note']

    # Parameter
    parameter_name = instruction['param']
    instruction_report.parameter = parameter_name
    if not parameter_name in dataset.variables:
        msg = "Parameter '%s' not found in %s" % (
            parameter_name,
            dataset.variables.keys())
        instruction_report.log = msg
        logger.error(msg)
        return

    # Expected value
    try:
        desired = float(instruction['ref'])
    except ValueError:
        desired = instruction['ref']
        msg = "Invalid non-float value: %r" % desired
        instruction_report.invalid_desired_value = msg
        logger.error(msg)
        desired = INVALID_DESIRED_VALUE
    instruction_report.desired = desired

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
        location_index = [index for index, value in enumerate(quad) if value][0]
        # ^^^ TODO: Is this right?
    except IndexError:
        msg = "x=%s, y=%s not found in grid" % (x, y)
        instruction_report.log = msg
        logger.error(msg)
        return
    instruction_report.what.append("quad number %s (x=%s, y=%s)" % (
        location_index, x, y))

    # Time
    desired_time_index = _desired_time_index(instruction, instruction_report, dataset)
    if desired_time_index is None:
        return

    # Value lookup.
    found = _value_lookup(dataset, parameter_name, desired_time_index, location_index, instruction_report)
    if found is None:
        return

    instruction_report.found = found
    instruction_report.equal = (abs(desired - found) < 0.00001)
    logger.info("Found value %s for parameter %s; desired=%s", 
                found,
                parameter_name,
                desired)


def check_map_nflow(instruction, instruction_report, dataset):
    logger.debug("Checking nflow")
    # Admin stuff.
    instruction_report.title = instruction['note']

    # Parameter.
    parameter_name = instruction['param']
    instruction_report.parameter = parameter_name
    if not parameter_name in dataset.variables:
        msg = "Parameter '%s' not found in %s" % (
            parameter_name,
            dataset.variables.keys())
        instruction_report.log = msg
        logger.error(msg)
        return

    # Expected value
    try:
        desired = float(instruction['ref'])
    except ValueError:
        desired = instruction['ref']
        msg = "Invalid non-float value: %r" % desired
        instruction_report.invalid_desired_value = msg
        logger.error(msg)
        desired = INVALID_DESIRED_VALUE
    instruction_report.desired = desired

    # nflow
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
        instruction_report.what.append("nFlowLink at index %s" % location_index)

    # Time
    desired_time_index = _desired_time_index(instruction, instruction_report, dataset)
    if desired_time_index is None:
        return
    
    # Value lookup.
    found = _value_lookup(dataset, parameter_name, desired_time_index, location_index, instruction_report)
    if found is None:
        return

    instruction_report.found = found
    instruction_report.equal = (abs(desired - found) < 0.00001)
    logger.info("Found value %s for parameter %s; desired=%s", 
                found,
                parameter_name,
                desired)
                        

def check_csv(csv_filename, mdu_report=None):
    instructions = list(csv.DictReader(open(csv_filename), delimiter=';'))
    mdu_report.record_instructions(instructions, csv_filename)
    if 'his' in csv_filename:
        netcdf_filename = 'subgrid_his.nc'
    else:
        netcdf_filename = 'subgrid_map.nc'
    with Dataset(netcdf_filename) as dataset:
        for test_number, instruction in enumerate(instructions):
            instruction_id = csv_filename[:-4] + '-' + str(test_number)
            instruction_report = mdu_report.instruction_reports[instruction_id]
            if 'his' in csv_filename:
                check_his(instruction, instruction_report, dataset)
            else:
                if ('nFlowLink' in instruction or
                    'nFlowElem' in instruction):
                    check_map_nflow(instruction, instruction_report, dataset)
                else:
                    check_map(instruction, instruction_report, dataset)



def run_simulation(mdu_filepath):
    mdu_report = report.mdu_reports[mdu_filepath]
    original_dir = os.getcwd()
    os.chdir(os.path.dirname(mdu_filepath))
    if 'index.txt' in os.listdir('.'):
        mdu_report.index_lines = open('index.txt').readlines()
    logger.debug("Loading %s...", mdu_filepath)
    cmd = '/opt/3di/bin/subgridf90 %s --autostartstop' % os.path.basename(
        mdu_filepath)
    # ^^^ TODO: hardcoded.
    logger.debug("Running %s", cmd)
    exit_code, output = system(cmd)
    last_output = ''.join(output.split('\n')[-2:]).lower()
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
        csv_filenames = [f for f in os.listdir('.') if f.endswith('.csv')]
        for csv_filename in csv_filenames:
            logger.info("Reading instructions from %s", csv_filename)
            check_csv(csv_filename, mdu_report=mdu_report)
    os.chdir(original_dir)


def mdu_filepaths(basedir):
    """Iterator that yields full paths to .mdu files."""
    basedir = os.path.abspath(basedir)
    for dirpath, dirnames, filenames in os.walk(basedir):
        mdu_filenames = [f for f in filenames if f.endswith('.mdu')]
        for mdu_filename in mdu_filenames:
            yield os.path.join(dirpath, mdu_filename)


def main():
    parser = argparse.ArgumentParser(
        description='Run verification tests on the "unit test" models.')
    parser.add_argument('directory',
                        nargs='?',
                        default='.',
                        help='directory with the tests')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    for mdu_filepath in mdu_filepaths(args.directory):
        run_simulation(mdu_filepath)
    report.export_reports()
    
