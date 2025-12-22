class EventSource:

    def __init__(self):
        self.callbacks = []

    def subscribe(self, callback):
        self.callbacks.append(callback)

    def trigger(self, *args):
        for callback in self.callbacks:
            callback(*args)
