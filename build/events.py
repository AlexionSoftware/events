"""Utilities for working with Windows & Python events
Windows has event objects which can be created and fired system-wide. This
 is useful for signalling between processes. Eg each of three cooperating
 processes could create the same event and then use a thread (cf event_handler
 below) which would block on the event to perform some useful action, for
 example a data reload.

Python also has an event construct, based around the threading support
 module. Although it is intra-process only, its basic functionality is
 the same as the Windows events (set, reset, wait).

This module implements a common event interface, and offers a python
 version of it (PythonEvent) and a Windows version (Win32Event) where
 available. The module behaves perfectly well on Linux simply by not
 creating the Win32Event class.

(c) Tim Golden <tim.golden@iname.com> 25th November 2003

25th Nov 2003 0.1  Initial release by Tim Golden
"""

__VERSION__ = "0.1"

import threading
#
# Exceptions specifically for use with event
#  classes
#
class x_event (Exception):
  pass
class x_unimplemented (x_event):
  pass
class x_event_timeout (x_event):
  pass
class x_event_abandoned (x_event):
  pass

class _Event:
  """A lightweight wrapper round Event objects"""

  def __init__ (self, name, initial_state, manual_reset):
    """Create a named event object"""
    raise x_unimplemented

  def set (self):
    """Set (ie fire) the event"""
    raise x_unimplemented

  def reset (self):
    """Reset (ie stop firing) the event"""
    raise x_unimplemented

  def pulse (self):
    """Pulse (ie fire once and stop) the event"""
    raise x_unimplemented

  def is_set (self):
    "Is the event set?"
    raise x_unimplemented

  def wait (self, timeout_secs):
    """Wait for the event to fire, optionally timing out"""
    raise x_unimplemented

_Event.fire = _Event.set
_Event.stop = _Event.reset

class PythonEvent (_Event):
  """A lightweight wrapper round the Python Event objects"""

  def __init__ (self, name, initial_state=0, manual_reset=0):
    """Create a named event object"""
    self.name = name
    self.event = threading.Event ()
    if initial_state:
      self.event.set ()
    else:
      self.event.clear ()

  def set (self):
    """Set (ie fire) the event"""
    self.event.set ()

  def reset (self):
    """Reset (ie stop firing) the event"""
    self.event.clear ()

  def pulse (self):
    """Pulse (ie fire once and stop) the event"""
    self.event.set ()
    self.event.clear ()

  def is_set (self):
    "Is the event set?"
    return self.event.isSet ()

  def wait (self, timeout_secs=None):
    """Wait for the event to fire, optionally timing out"""
    if self.event.wait (timeout_secs) is None:
      raise x_event_timeout

try:
  import win32event
except ImportError:
  win32event = None
else:
  class Win32Event (_Event):
    """Windows events can be named or unnamed and are machine-wide,
     so ideal for IPC, although not inter-machine, so no use for
     distributed IPC. The win32event module in the win32all extensions
     already exposes all the functions you need; this class is a
     lightweight object wrapper round those functions.

    Rather than having to pass an object handle around, separate
     processes can create references to the same event by using the
     same name in each case.
    NB The first process to create the event determines its initial
     state and manual reset. No matter what later invocations specify
     for these values, the first one is what matters.

    Typical usage:

    PROCESS 1                                  | PROCESS 2
                                               |
    import events                              | import events
                                               |
    e1 = events.Win32Event ("ready_for_data")  | ok_to_produce = events.Win32Event ("ready_for_data")
    e2 = events.Win32Event ("data_produced")   | data_produced = events.Win32Event ("data_produced")
                                               |
                                               | while 1:
                                               |   ready.wait ()
    # ... setup code                           |   produce_data ()
                                               |   data_produced.set ()
                                               |
    while 1:                                   |
      e1.set ()                                |
      e2.wait ()                               |
      consume_data ()                          |

    """
    def __init__ (self, name, initial_state=0, manual_reset=0):
      """Create a named event object
      If the name is already in use, a handle the existing event object is reused
      If initial_state is 1, the event is created set
      If manual_reset is 1, whenever the event is set, it will remain until manually reset.
       If you are trying to signal multiple processes with the one event, this flag
       need to be set, otherwise the first process to be signalled will cause the
       flag to be reset. NB The *first* process to create the named event will determine
       the state of this flag, not any subsequent processes.
      """
      self.name = name
      self.event = win32event.CreateEvent (None, manual_reset, initial_state, name)

    def set (self):
      """Set (ie fire) the event"""
      win32event.SetEvent (self.event)

    def reset (self):
      """Reset (ie stop firing) the event"""
      win32event.SetEvent (self.event)

    def pulse (self):
      """Pulse (ie fire once and stop) the event"""
      win32event.PulseEvent (self.event)

    def is_set (self):
      "Is the event set?"
      try:
        self.wait (0)
        return 1
      except x_event_timeout:
        return 0

    def wait (self, timeout_secs=win32event.INFINITE):
      """Wait for the event to fire, optionally timing out"""
      if timeout_secs == win32event.INFINITE:
        result = win32event.WaitForSingleObject (self.event, timeout_secs)
      else:
        result = win32event.WaitForSingleObject (self.event, 1000 * timeout_secs)

      if result == win32event.WAIT_TIMEOUT:
        raise x_event_timeout
      elif result == win32event.WAIT_ABANDONED:
        raise x_event_abandoned

  Event = Win32Event # for the sake of legacy code

  #
  # Below is an event handler class
  #
  STOP_EVENT = Event ("__STOP_EVENT_HANDLER")

  class EventHandler (threading.Thread):
    """Given two events, call a parameterless function when one fires,
     and exit the thread when the other fires"""

    def __init__ (self, action, action_event, stop_event=STOP_EVENT):
      """Create a thread to call a parameterless function whenever the action
       event is fired, finishing when the stop event fires
      """
      threading.Thread.__init__ (self)
      self.stop_event = stop_event
      self.events = {}
      self.events[action_event.event] = action
      self.events[stop_event.event] = self._stop
      self.start ()

    def stop (self):
      """This can be called instead of firing the stop event"""
      self.stop_event.fire ()

    def _stop (self):
      self.finished = 1

    def run (self):
      """Until the stop event is fired, perform the action whenever the action event fires"""
      self.finished = 0
      events = self.events.keys ()

      while not self.finished:
        result = win32event.WaitForMultipleObjects (events, 0, win32event.INFINITE)
        if win32event.WAIT_OBJECT_0 <= result <= win32event.WAIT_OBJECT_0 + len (events) - 1:
          self.events[events[result - win32event.WAIT_OBJECT_0]]()


