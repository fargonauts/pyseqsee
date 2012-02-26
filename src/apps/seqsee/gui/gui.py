"""Adapting the generic FARG GUI to Seqsee."""

from farg.ui.gui import gui
from apps.seqsee.gui.central_pane import CentralPane
from apps.seqsee.gui.conversation import Conversation

class SeqseeGUI(gui.GUI):
  def __init__(self, controller, flags, geometry='810x700-0+0'):
    gui.GUI.__init__(self, controller, flags, geometry)

    # TODO(# --- Jan 3, 2012): Not sure if this is the right abstraction. I want to be able
    # to display messages for debugging. I should have a better messaging system built right
    # into the controller.
    controller.mw = self.mw

    self.mw.bind('<KeyPress-q>', lambda e: self.Quit())
    self.mw.bind('<KeyPress-s>', lambda e: self.Steps(1))
    self.mw.bind('<KeyPress-l>', lambda e: self.Steps(10))
    self.mw.bind('<KeyPress-k>', lambda e: self.Steps(100))
    self.mw.bind('<KeyPress-c>', lambda e: self.Start())
    self.mw.bind('<KeyPress-p>', lambda e: self.Pause())

  def PopulateCentralPane(self, args):
    height = args.gui_canvas_height
    width = args.gui_canvas_width
    canvas = CentralPane(self.mw, self.controller, args,
                         height=height, width=width,
                         background='#FEE')
    canvas.grid()
    self.central_pane = canvas
    self.items_to_refresh.append(canvas)
    canvas.ReDraw()

  def PopulateInteractionPane(self, args):
    conversation = Conversation(self.mw, self.controller, height=10)
    conversation.grid()
    self.conversation = conversation
    self.items_to_refresh.append(conversation)
    conversation.ReDraw()
