import mmap
import time

import events

import common

shared_memory = mmap.mmap (0, common.SHARED_MEMORY_SIZE, common.SHARED_MEMORY_NAME)
ready_to_consume_event = events.Win32Event (common.READY_TO_CONSUME)
finished_producing_event = events.Win32Event (common.FINISHED_PRODUCING)

while 1:
  ready_to_consume_event.set ()
  finished_producing_event.wait ()
  print shared_memory.readline ()
  time.sleep (2)

