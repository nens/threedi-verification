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

from jinja2 import Environment, PackageLoader
from netCDF4 import Dataset
import numpy as np

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
        if (self.found is None
            or self.desired is None
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

    def __init__(self, mdu_filepath):
        self.log = None
        self.successfully_loaded_log = None
        self.id = mdu_filepath
        self.instruction_reports = defaultdict(InstructionReport)
        self.loadable = True
        self.status = None
        self.index_lines = []
        self.csv_contents = []
        self.model_parameters = []

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


def check_map(instruction, instruction_report, dataset):
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


def check_map_nflow(instruction, instruction_report, dataset):
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
        margin = instruction['margin']
        instruction_report.margin = margin

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
                if ('nFlowLink' in instruction or 'nFlowElem' in instruction):
                    check_map_nflow(instruction, instruction_report, dataset)
                else:
                    check_map(instruction, instruction_report, dataset)


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


def check_mdu_file(mdu_filepath):
    for line in open(mdu_filepath):
        if line.startswith('NTimesteps'):
            if '20160' in line:
                msg = "Wrong default 20160 NTimesteps value in %s:\n%s" % (
                    mdu_filepath, line)
                return msg


def run_simulation(mdu_filepath, mdu_report=None, verbose=False):
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
    buildout_dir = os.path.join(original_dir, '..')
    subgridpy = os.path.join(buildout_dir, 'bin', 'subgridpy')
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
            check_csv(csv_filename, mdu_report=mdu_report)

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
    parser.add_argument('--verbose', default=False, action='store_true')
    args = parser.parse_args()
    report = Report()
    logging.basicConfig(level=logging.DEBUG)
    for mdu_filepath in mdu_filepaths(args.directory):
        run_simulation(mdu_filepath, report=report, verbose=args.verbose)
    report.export_reports()
    create_archive_index()
