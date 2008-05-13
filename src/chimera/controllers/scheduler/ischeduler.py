
class IScheduler (object):

    def reschedule (self, machine):
        """
        Re-schedule using current database state. This will setup a
        timer to wakeup the Machine to process the next runnable task.

        Reschedule runs only phase-one scheduling,
        date/observability. So, may not be possible to process the new
        scheduled items because of realtime constraints.
        """

    def next (self, now, sensors):
        """
        Called to get next runnable task after run phase-two
        scheduling on the current runqueue. It may use 'now'
        information to see if we are laggy according to our last
        reschedule and cut non-runnable items or reschedule again.
        """

    def done (self, task):
        """
        Called to change runnable state of 'task'. When called, will
        remove 'task' from the runqueue (task can be either completed
        or just ignored with some error)
        """
