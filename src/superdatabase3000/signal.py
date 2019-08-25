"""A simple module to handle catching signals"""

import signal


class ExitSignalWatcher():
    """This class allows to store any caught SIGINT/SIGTERM"""

    EXIT = 0

    def __init__(self):
        self.sig_handler = None

    @staticmethod
    def _signal_handler(signal_code, unused_frame):
        """Just store the exit status, for later safe exiting"""
        ExitSignalWatcher.EXIT = 128 + signal_code

    def catch(self):
        """Catch signal INT/TERM, so we won't exit while playing with files"""
        if self.sig_handler is None:
            self.sig_handler = {}
        self.sig_handler.setdefault(
            signal.SIGINT,
            signal.signal(signal.SIGINT, ExitSignalWatcher._signal_handler)
        )
        self.sig_handler.setdefault(
            signal.SIGTERM,
            signal.signal(signal.SIGTERM, ExitSignalWatcher._signal_handler)
        )
        ExitSignalWatcher.EXIT = 0

    def restore(self):
        """Restore the previous signal handler"""
        signal.signal(signal.SIGINT, self.sig_handler[signal.SIGINT])
        signal.signal(signal.SIGTERM, self.sig_handler[signal.SIGTERM])
