from objc import Category
from AppKit import NSScreen
from Foundation import NSRect


def _frame_from_dict(values):
    frame = NSRect()
    frame[0][0] = values['x']
    frame[0][1] = values['y']
    frame[1][0] = values['width']
    frame[1][1] = values['height']
    return frame


def _dict_from_frame(frame):
    values = {'x': frame[0][0], 'y': frame[0][1], 'width': frame[1][0], 'height': frame[1][1]}
    print values
    return values


class NSScreen(Category(NSScreen)):
    """
    A simple category on NSScreen to provide a useful method.
    """
    def get_flipped_frame(self, relative_to = NSScreen.mainScreen()):
        frame = _dict_from_frame(self.frame)
        main_frame = _dict_from_frame(relative_to)

        frame['y'] = - frame['y'] + main_frame['height'] - frame['height']

        return _frame_from_dict(frame)
