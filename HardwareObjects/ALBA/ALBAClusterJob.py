#
#  Project: MXCuBE
#  https://github.com/mxcube.
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

import os
import time
import logging

import sys

sys.path.append("/beamlines/bl13/controls/devel/pycharm/ALBAClusterClient")
from xaloc import XalocJob

from XSDataMXCuBEv1_3 import XSDataResultMXCuBE

root = os.environ['POST_PROCESSING_SCRIPTS_ROOT']

class ALBAClusterJob(object):

    def __init__(self, *args):
        self.job = None

    def run(self, *args):
        pass

    def wait_done(self, wait=True):

        if not self.job:
            return

        time.sleep(0.5) 

        state = self.job.state

        if not wait:
            return state

        while state in ["RUNNING", "PENDING"]:
            logging.getLogger("HWR").debug("Job / is %s" % state)
            time.sleep(0.5) 
            state = self.job.state

        logging.getLogger("HWR").debug(" job finished with state: \"%s\"" % state) 
        return state

    def get_result(self, state):
        pass

class ALBAAutoProcJob(ALBAClusterJob):
    sls_script = os.path.join(root, 'edna-mx/autoproc/mxcube/edna-mx.autoproc.sl')
   
    def run(self, *args):

        jobname = os.path.basename(os.path.dirname(edna_directory))
        self.job = XalocJob("edna-autoproc", jobname, self.sls_script, input_file, edna_directory, 'SCRATCH')
        self.job.submit()

class ALBAEdnaProcJob(ALBAClusterJob):
    sls_script = os.path.join(root, 'edna-mx/ednaproc/mxcube/edna-mx.ednaproc.sl')
   
    def run(self, *args):
        collect_id, input_file, output_dir = args
        self.job = XalocJob("edna-ednaproc", str(collect_id), self.sls_script, input_file, output_dir, 'SCRATCH')
        self.job.submit()

class ALBAStrategyJob(ALBAClusterJob):

    sls_script = os.path.join(root, 'edna-mx/strategy/mxcube/edna-mx.strategy.sl')

    def run(self, *args):

        logging.getLogger("HWR").debug("Starting StrategyJob - ")

        input_file, results_file, edna_directory = args

        jobname = os.path.basename(os.path.dirname(edna_directory))

        self.job = XalocJob("edna-strategy", jobname, self.sls_script, input_file, edna_directory, 'SCRATCH')
        self.job.submit()

        logging.getLogger("HWR").debug("         StrategyJob - %s" % str(self.job))

        self.edna_directory = os.path.dirname(input_file)
        self.results_file = results_file

        logging.getLogger("HWR").debug("  input file: %s" % input_file)
        logging.getLogger("HWR").debug("  edna directory: %s" % self.edna_directory)

    def get_result(self, state):
        if state == "COMPLETED": 
            outfile = os.path.join( self.edna_directory, "ControlInterfaceToMXCuBEv1_3_dataOutput.xml")

            logging.getLogger("HWR").debug("Job / state is COMPLETED")
            logging.getLogger("HWR").debug("  looking for file: %s" % outfile)
            if os.path.exists(outfile):
                job_output = open(outfile).read()
                open(self.results_file, "w").write(job_output)
                result = XSDataResultMXCuBE.parseFile(self.results_file)
            else:
                logging.getLogger("HWR").debug("EDNA Job finished without success / cannot find output file ") 
                result = ""
        else:
            logging.getLogger("HWR").debug("EDNA Job finished without success / state was %s" % (job.state))
            result = ""
        
        return result
