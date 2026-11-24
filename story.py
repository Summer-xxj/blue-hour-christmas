# xxj-summer-zjl
"""Gesture-driven performance; transitions consume stable, fresh gestures only."""
class Story:
    sequence = ('empty', 'heart', '1', '2', '3', 'core', 'tree')
    expected = ('tree', '1', '2', '3', 'fist', 'tree')

    def __init__(self):
        self.stage = 'empty'
        self.changed_at = 0.
        self.last_gesture = None

    def accept(self, gesture, now):
        if gesture is None:
            self.last_gesture = None
            return False
        if gesture == self.last_gesture:
            return False
        self.last_gesture = gesture
        index = self.sequence.index(self.stage)
        if index == len(self.sequence)-1 or gesture != self.expected[index]:
            return False
        self.stage = self.sequence[index+1]
        self.changed_at = now
        return True

    def reset(self):
        self.__init__()
