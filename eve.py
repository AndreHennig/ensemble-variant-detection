#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import glob
import logging
import argparse
import datetime
import platform
from eve import detectors,mappers

class EVE(object):
    """Ensemble Variant Detection"""
    def __init__(self, argv):
        # parse arguments
        self.args = self.parse_args(argv)

        # create working directories
        self.create_working_directories()

        # initialize logger
        self.initialize_logger()
        self.log_system_info()

        # load mapper
        if 'bam' in self.args:
            self.mapper = mappers.BWAMapper()

        # load detectors
        self.detectors = []

        for detector in self.args.variant_detectors.split(','):
            # config filepath (txt/yaml)
            # @TODO : normalize handling of config files (just use txt)
            conf = os.path.join('config', 'detectors', '%s.yaml' % detector)
            if not os.path.exists(conf):
                conf = os.path.join('config', 'detectors', '%s.txt' % detector)

            # @TODO: dynamically load classes
            if detector == 'mpileup':
                self.detectors.append(detectors.MpileupDetector(
                    self.args.bam, self.args.fasta, conf, self.working_dir
                ))

    def run(self):
        """Main application process"""
        # map reads
        if 'bam' in self.args:
            logging.info("Mapping reads")
            self.bam = self.mapper.run(self.args.input_reads)

        # run variant detectors
        # TESTING


        # normalize output from variant detectors and read in as either a NumPy
        # matrix or pandas DataFrame

        # run classifier
        # (http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)

        # output final VCF



    def create_working_directories(self):
        """Creates directories to output intermediate files into"""
        now = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')

        self.working_dir = os.path.join(self.args.working_directory, now)

        for subdir in ['mapped', 'vcf']:
            path = os.path.join(self.working_dir, subdir)
            if not os.path.isdir(path):
                os.makedirs(path)

    def initialize_logger(self):
        """Initializes a logger instance"""
        logging.basicConfig(level=logging.DEBUG,
                format='(%(asctime)s)[%(levelname)s] %(message)s',
                filename=os.path.join(self.working_dir, 'eve.log'))

        # log to console as well
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)

        # set a format which is simpler for console use
        formatter = logging.Formatter('[%(levelname)s] %(message)s')

        # tell the handler to use this format
        console.setFormatter(formatter)

        # add the handler to the root logger
        logging.getLogger('').addHandler(console)

    def log_system_info(self):
        """Prints system information to the log.
           Code adapted from the SunPy project."""
        # EVE version
        from eve import __version__ as eve_version
        logging.info("Starting EVE %s" % eve_version)

        # Time
        now = datetime.datetime.utcnow().strftime("%A, %d. %B %Y %I:%M%p UT")
        logging.info("Time: %s" % now)

        # Platform
        system = platform.system()
        processor = platform.processor()

        if system == "Linux":
            distro = " ".join(platform.linux_distribution())
            logging.debug("OS: %s (Linux %s %s)" %  (
                distro, platform.release(), processor))
        elif system == "Darwin":
            logging.debug("OS: Mac OS X %s (%s)" % (
                platform.mac_ver()[0], processor)
            )
        elif system == "Windows":
            logging.debug("OS: Windows %s %s (%s)" %  (
                platform.release(), platform.version(), processor))
        else:
            logging.debug ("Unknown OS (%s)" % processor)

        # Architecture
        logging.debug('Architecture: %s' % platform.architecture()[0])

        # Python version
        logging.debug("Python %s" % platform.python_version())

        # Check python dependencies
        try:
            from numpy import __version__ as numpy_version
        except ImportError:
            numpy_version = "NOT INSTALLED"

        try:
            from scipy import __version__ as scipy_version
        except ImportError:
            scipy_version = "NOT INSTALLED"

        try:
            from sklearn import __version__ as sklearn_version
        except ImportError:
            sklearn_version = "NOT INSTALLED"

        try:
            from yaml import __version__ as yaml_version
        except ImportError:
            yaml_version = "NOT INSTALLED"

        logging.debug("NumPy: %s" % numpy_version)
        logging.debug("SciPy: %s" % scipy_version)
        logging.debug("Scikit-Learn: %s" % sklearn_version)
        logging.debug("PyYAML: %s" % yaml_version)

        # @TODO: command-line tool versions (SAMtools, etc)

    def parse_args(self, argv):
        """Parses input arguments"""
        parser = argparse.ArgumentParser(
                description='Ensemble Variant Detection')
        parser.add_argument('input_reads', nargs='+',
                            help=('Input paired-end Illumina reads or '
                                  'alignment. Supported file formats include '
                                  '.fastq, .fastq.gz, and .bam'))
        parser.add_argument('-o', '--output',
                            help='Location to save final VCF output to.')
        parser.add_argument('-f', '--fasta', required=True,
                            help='Location of genome sequence file to use.')
        parser.add_argument('-g', '--gff', required=True,
                            help='Location of GFF annotation file to use.')
        parser.add_argument('-m', '--mapper', default='bwa',
                            help='Mapper to use for read alignment')
        parser.add_argument('-d', '--variant-detectors',
                            default='gatk,mpileup,varscan',
                            help=('Comma-separated list of the variant '
                                  'detectors to be used.'))
        parser.add_argument('-w', '--working-directory',
                            default='output/',
                            help='Location to store intermediate files')
        args = parser.parse_args()

        # validate input arguments
        if len(args.input_reads) > 2:
            raise IOError("Too many input arguments specified")
        if not os.path.isfile(args.gff):
            raise IOError("Invalid GFF filepath specified")

        # determine input type (FASTQ or BAM)
        if len(args.input_reads) == 1 and args.input_reads[0].endswith('.bam'):
            args.bam == args.input_reads[0]

        return args

if __name__ == '__main__':
    app = EVE(sys.argv)
    sys.exit(app.run())
