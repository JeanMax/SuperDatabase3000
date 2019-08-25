import superdatabase3000.signal as sig


def test_signal():
    esw = sig.ExitSignalWatcher()
    esw.catch()
    esw.restore()
