# Copyright (C) 2011, 2012  Abhijit Mahabal
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>

"""The Main class is the entry point into an app.
"""
from farg.core.controller import Controller
from farg.core.run_mode import batch, gui, single, sxs
from farg.core.stopping_conditions import StoppingConditions
from farg.core.ui.batch_ui import BatchUI
from farg.core.ui.gui import GUI
from farg.third_party import gflags
import logging
import os.path
import sys

FLAGS = gflags.FLAGS

gflags.DEFINE_enum('run_mode', 'gui',
                   ('gui', 'batch', 'sxs', 'single'),
                   'Mode to run in. GUI creates a tkinter display, whereas batch and sxs '
                   'run the program multiple times non-interactively. Each such run uses '
                   'the "single" run mode.')
gflags.DEFINE_enum('debug', '', ('', 'debug', 'info', 'warn', 'error', 'fatal'),
                   'Show messages from what debug level and above?')
gflags.DEFINE_string('stopping_condition', None,
                     'Stopping condition, if any. Only allowed in non-gui modes. If the '
                     'condition is met, the program returns with a StoppingConditionMet '
                     'exception')

gflags.DEFINE_string('input_spec_file', None,
                     'Path specifying inputs over which to run batch processes.'
                     'This will be read by an instance of input_spec_reader_class.')
gflags.DEFINE_integer('num_iterations', 10,
                      "In batch and SxS mode, number of iterations to run", 1)
gflags.DEFINE_integer('max_steps', 1000,
                      "In batch and SxS mode, number of steps per run", 1)

gflags.DEFINE_string('persistent_directory', '',
                     'Directory in which to hold files that persist between runs, such as'
                     'ltm files or statistics about performance on batch runs. '
                     'If not passed, ~/.pyseqsee/{application_name} is used.')
gflags.DEFINE_string('ltm_directory', '',
                     'Directory to hold LTM files. '
                     'If not passed, FLAGS.persistent_directory/ltm is used')
gflags.DEFINE_string('stats_directory', '',
                     'Directory to hold statistics from prior batch runs. '
                     'If not passed, FLAGS.persistent_directory/stats is used')


class Main:
  #: Class to use for running in GUI mode.
  run_mode_gui_class = gui.RunModeGUI
  #: Class to use for running in Batch mode.
  run_mode_batch_class = batch.RunModeBatch
  #: Class to use for running in SxS mode.
  run_mode_sxs_class = sxs.RunModeSxS
  #: Class to use for running in single mode.
  run_mode_single_run_class = single.RunModeSingle

  #: GUI class to use for the tkinter GUI.
  #: Subclasses of Main can override this, probably with a subclass of its value here.
  gui_class = GUI
  #: Batch UI class to use for running in non-interactive mode. It should be able to handle
  #: any questions that may be generated by its codelets.
  #: Subclasses of Main can override this, probably with a subclass of its value here.
  batch_ui_class = BatchUI

  #: The controller runs the show by scheduling codelets to run.
  #: Subclasses of Main can override this, probably with a subclass of its value here.
  controller_class = Controller

  #: In batch and sxs modes, the inputs over which to run are specified in a file.
  #: These will be converted to flags passed to individual runs. An input reader should
  #: be specified for the file to series of flags conversion.
  #: These will usually be a subclass of ReadInputSpec.
  input_spec_reader_class = None

  #: A mapping between stopping condition names and their implmentation (which is a funtion
  #: that takes a controller and returns a bool).
  stopping_conditions_class = StoppingConditions

  def VerifyPersistentDirectoryPath(self):
    """Verify (or create) the persistent directory."""
    directory = FLAGS.persistent_directory
    if not directory:
      homedir = os.path.expanduser('~')
      if not os.path.exists(homedir):
        print ("Could not locate home directory for storing LTM files."
               "You could explicitly specify an existing directory to use by using"
               "the flag --ltm_directory. Quitting.")
        sys.exit(1)
      pyseqsee_home = os.path.join(homedir, '.pyseqsee')
      if not os.path.exists(pyseqsee_home):
        print('Creating directory for storing pyseqsee files: %s' % pyseqsee_home)
        os.mkdir(pyseqsee_home)
      directory = os.path.join(pyseqsee_home, self.application_name)
    if not os.path.exists(directory):
      print('Creating directory for storing persistent files for the %s app: %s' %
            (self.application_name, directory))
      os.mkdir(directory)
    FLAGS.persistent_directory = directory

  def VerifyLTMPath(self):
    """Create a directory for ltms unless flag provided. If provided, verify it exists."""
    if FLAGS.ltm_directory:
      if not os.path.exists(FLAGS.ltm_directory):
        print ("LTM directory '%s' does not exist." % FLAGS.ltm_directory)
        sys.exit(1)
    else:
      self.VerifyPersistentDirectoryPath()
      FLAGS.ltm_directory = os.path.join(FLAGS.persistent_directory, 'ltm')
      if not os.path.exists(FLAGS.ltm_directory):
        print('Creating directory for storing ltms: %s' % FLAGS.ltm_directory)
        os.mkdir(FLAGS.ltm_directory)

  def VerifyStatsPath(self):
    """Create a directory for batch stats unless flag provided. If provided,
       verify it exists."""
    if FLAGS.stats_directory:
      if not os.path.exists(FLAGS.stats_directory):
        print ("Stats directory '%s' does not exist." % FLAGS.stats_directory)
        sys.exit(1)
    else:
      self.VerifyPersistentDirectoryPath()
      FLAGS.stats_directory = os.path.join(FLAGS.persistent_directory, 'stats')
      if not os.path.exists(FLAGS.stats_directory):
        print('Creating directory for storing stats: %s' % FLAGS.stats_directory)
        os.mkdir(FLAGS.stats_directory)


  def VerifyStoppingConditionSanity(self):
    """
    Make sure that stopping conditions are specified only in modes where they make sense.
    """
    run_mode_name = FLAGS.run_mode
    stopping_condition = FLAGS.stopping_condition
    if run_mode_name == 'gui':
      # There should be no stopping condition.
      if stopping_condition:
        print("Stopping condition does not make sense with GUI.")
        sys.exit(1)
    else:  # Verify that the stopping condition's name is defined.
      if FLAGS.stopping_condition and FLAGS.stopping_condition != "None":
        stopping_conditions_list = self.stopping_conditions_class.StoppingConditionsList()
        if FLAGS.stopping_condition not in stopping_conditions_list:
          print('Unknown stopping condition %s. Use one of %s' %
                (FLAGS.stopping_condition, stopping_conditions_list))
          sys.exit(1)
        else:
          self.stopping_condition_fn = (
               self.stopping_conditions_class.GetStoppingCondition(FLAGS.stopping_condition))
      else:
        self.stopping_condition_fn = ''

  def CreateRunModeInstance(self):
    """
    Create a Runmode instance from the flags.
    """
    run_mode_name = FLAGS.run_mode
    if run_mode_name == 'gui':
      return self.run_mode_gui_class(controller_class=self.controller_class,
                                     ui_class=self.gui_class)
    elif run_mode_name == 'single':
      return self.run_mode_single_run_class(controller_class=self.controller_class,
                                            ui_class=self.batch_ui_class,
                                            stopping_condition_fn=self.stopping_condition_fn)
    else:
      if not FLAGS.input_spec_file:
        print('Runmode --run_mode=%s requires --input_spec_file to be specified' %
              run_mode_name)
        sys.exit(1)
      input_spec = list(self.input_spec_reader_class().ReadFile(FLAGS.input_spec_file))
      print(input_spec)
      if run_mode_name == 'batch':
        return self.run_mode_batch_class(controller_class=self.controller_class,
                                         input_spec=input_spec)
      elif run_mode_name == 'sxs':
        return self.run_mode_sxs_class(controller_class=self.controller_class,
                                       input_spec=input_spec)
      else:
        print("Unrecognized run_mode %s" % run_mode_name)
        sys.exit(1)

  def ProcessFlags(self):
    """Called after flags have been read in."""
    self.ProcessCustomFlags()

    if FLAGS.input_spec_file:
      # Check that this is a file and it exists.
      if not os.path.exists(FLAGS.input_spec_file):
        print ("Input specification file '%s' does not exist. Bailing out." %
               FLAGS.input_spec_file)
        sys.exit(1)
      if not os.path.isfile(FLAGS.input_spec_file):
        print ("Input specification '%s' is not a file. Bailing out." %
               FLAGS.input_spec_file)
        sys.exit(1)

    self.VerifyStoppingConditionSanity()
    self.VerifyPersistentDirectoryPath()
    self.VerifyLTMPath()
    self.VerifyStatsPath()
    self.run_mode = self.CreateRunModeInstance()

    if FLAGS.debug:
      numeric_level = getattr(logging, FLAGS.debug.upper(), None)
      if not isinstance(numeric_level, int):
        print('Invalid log level: %s' % FLAGS.debug)
        sys.exit(1)
      logging.basicConfig(level=numeric_level)

  def ProcessCustomFlags(self):
    """
    Apps can override this to process app-specific flags.
    """
    pass

  def Run(self):
    self.run_mode.Run()

  def main(self, argv):
    try:
      argv = FLAGS(argv)  # parse flags
    except gflags.FlagsError as e:
      print('%s\nUsage: %s ARGS\n%s\n\n%s' % (e, sys.argv[0], FLAGS, e))
      sys.exit(1)

    self.ProcessFlags()
    self.Run()
