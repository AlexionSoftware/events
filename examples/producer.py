import mmap

import events

import common

shared_memory = mmap.mmap (0, common.SHARED_MEMORY_SIZE, common.SHARED_MEMORY_NAME)
ready_to_consume_event = events.Win32Event (common.READY_TO_CONSUME)
finished_producing_event = events.Win32Event (common.FINISHED_PRODUCING)

line_number = 0

while 1:
  ready_to_consume_event.wait ()
  shared_memory.write ("This is line %d\n" % line_number)
  line_number += 1
  finished_producing_event.set ()

