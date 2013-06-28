"""
This module provides functions for running verification checks on small 
models and to create reports about them.

"""
from __future__ import print_function
from collections import defaultdict
import argparse
import csv
import logging
import os

from netCDF4 import Dataset
import numpy as np
from jinja2 import Environment, PackageLoader

from threedi_verification.utils import system

jinja_env = Environment(loader=PackageLoader('threedi_verification', 'templates'))
logger = logging.getLogger(__name__)

OUTDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                      '..', 'var', 'html'))


class InstructionReport(object):

    def __init__(self):
        self.log = None
        self.id = None
        self.parameter = None
        self.desired = None
        self.found = None
        self.equal = None
        self.title = None

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    @property
    def shortlog(self):
        if len(self.log < 400):
            return self.log
        return self.log[:200] + ' ... ' + self.log[-200:]


class MduReport(object):

    def __init__(self):
        self.log = None
        self.successfully_loaded_log = None
        self.id = None
        self.instruction_reports = defaultdict(InstructionReport)
        self.loadable = True

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    @property
    def log_filename(self):
        id = self.id.replace('/', '-')
        return 'mdu_log_%s.html' % id

    @property
    def log_summary(self):
        last_lines = self.log.split('\n')[-3:]
        return '\n'.join(last_lines)

    @property
    def title(self):
        return self.id.split('/testbank/')[1]

    @property
    def instructions(self):
        return sorted(self.instruction_reports.values())


class Report(object):

    def __init__(self):
        self.mdu_reports = defaultdict(MduReport)

    def write_template(self, template_name, outfile=None, title=None, 
                       context=None):
        if outfile is None:
            outfile = template_name
        outfile = os.path.join(OUTDIR, outfile)
        template = jinja_env.get_template(template_name)
        open(outfile, 'w').write(template.render(view=self, 
                                                 title=title, 
                                                 context=context))
        logger.debug("Wrote %s", outfile)

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

    def export_reports(self):
        self._propagate_ids()
        self.write_template('index.html',
                            title='Overview')
        for mdu in self.mdu_reports.values():
            if mdu.log:
                title = "Log of %s" % mdu.title
                self.write_template('mdu_log.html',
                                    title=mdu.title,
                                    outfile=mdu.log_filename,
                                    context=mdu)

                    
report = Report()


def check_his(csv_filename, mdu_report=None):
    instructions = list(csv.DictReader(open(csv_filename), delimiter=';'))
    netcdf_filename = 'subgrid_his.nc'
    with Dataset(netcdf_filename) as dataset:
        for instruction in instructions:
            instruction_id = csv_filename[:-4] + '-' + instruction['testnr']
            instruction_report = mdu_report.instruction_reports[instruction_id]
            # Brute force for now.
            parameter_name = instruction['param']
            instruction_report.parameter = parameter_name
            instruction_report.title = instruction['note']
            try:
                desired = float(instruction['ref'])
            except ValueError:
                desired = instruction['ref']
                msg = "Invalid non-float value: %s" % desired
                instruction_report.log = msg
                logger.error(msg)
                continue
            instruction_report.desired = desired
            if not parameter_name in dataset.variables:
                msg = "Parameter '%s' not found in %s" % (
                    parameter_name,
                    dataset.variables.keys())
                instruction_report.log = msg
                logger.error(msg)
                continue
            parameter_values = dataset.variables[parameter_name][:]
            desired_time = instruction['time']
            if desired_time == 'SUM':
                logger.debug("Summing all values")
                found = parameter_values.sum()
            else:
                desired_time = float(desired_time)
                logger.debug("Looking up value for time %s", desired_time)
                # TODO: less brute force, if possible.
                time_values = list(dataset.variables['time'][:])
                try:
                    desired_index = time_values.index(desired_time)
                except ValueError:
                    msg = "Time %s not found in %s" % (desired_time, 
                                                       time_values)
                    instruction_report.log = msg
                    logger.error(msg)
                    continue
                found = parameter_values[desired_index][0]

            instruction_report.found = found
            instruction_report.equal = (abs(desired - found) < 0.00001)
            logger.info("Found value %s for parameter %s; desired=%s", 
                        found,
                        parameter_name,
                        desired)


def check_map(csv_filename, mdu_report=None):
    instructions = list(csv.DictReader(open(csv_filename), delimiter=';'))
    netcdf_filename = 'subgrid_map.nc'
    with Dataset(netcdf_filename) as dataset:
        for instruction in instructions:
            instruction_id = csv_filename[:-4] + '-' + instruction['testnr']
            instruction_report = mdu_report.instruction_reports[instruction_id]
            # Brute force for now.
            parameter_name = instruction['param']
            instruction_report.parameter = parameter_name
            instruction_report.title = instruction['note']
            try:
                desired = float(instruction['ref'])
            except ValueError:
                desired = instruction['ref']
                msg = "Invalid non-float value: %s" % desired
                instruction_report.log = msg
                logger.error(msg)
                continue
            instruction_report.desired = desired
            if not parameter_name in dataset.variables:
                msg = "Parameter '%s' not found in %s" % (
                    parameter_name,
                    dataset.variables.keys())
                instruction_report.log = msg
                logger.error(msg)
                continue
            parameter_values = dataset.variables[parameter_name][:]
            desired_time = instruction['time']
            if desired_time == 'SUM':
                logger.debug("Summing all values")
                found = parameter_values.sum()
            else:
                desired_time = float(desired_time)
                logger.debug("Looking up value for time %s", desired_time)
                # TODO: less brute force, if possible.
                time_values = list(dataset.variables['time'][:])
                try:
                    desired_index = time_values.index(desired_time)
                except ValueError:
                    msg = "Time %s not found in %s" % (desired_time, 
                                                       time_values)
                    instruction_report.log = msg
                    logger.error(msg)
                    continue
                found = parameter_values[desired_index][0]

            instruction_report.found = found
            instruction_report.equal = (abs(desired - found) < 0.00001)
            logger.info("Found value %s for parameter %s; desired=%s", 
                        found,
                        parameter_name,
                        desired)
                        

def run_simulation(mdu_filepath):
    mdu_report = report.mdu_reports[mdu_filepath]
    original_dir = os.getcwd()
    os.chdir(os.path.dirname(mdu_filepath))
    logger.debug("Loading %s...", mdu_filepath)
    cmd = '/opt/3di/bin/subgridf90 ' + os.path.basename(mdu_filepath)
    logger.debug("Running %s", cmd)
    # ^^^ TODO: hardcoded.
    exit_code, output = system(cmd)
    last_output = ''.join(output.split('\n')[-2:]).lower()
    if exit_code or ('error' in last_output 
                     and 'quitting' in last_output):
        logger.error("Loading failed: %s", mdu_filepath)
        mdu_report.loadable = False
        mdu_report.log = output
    else:
        logger.info("Successfully loaded: %s", mdu_filepath)
        mdu_report.successfully_loaded_log = output 
        csv_filenames = [f for f in os.listdir('.') if f.endswith('.csv')]
        for csv_filename in csv_filenames:
            logger.info("Reading instructions from %s", csv_filename)
            if 'his' in csv_filename:
                check_his(csv_filename, mdu_report=mdu_report)
            else:
                check_map(csv_filename, mdu_report=mdu_report)
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
    
