import logging

from AppKit import NSScreen

class Layout(object):

	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)

	def prepare(self, window_manager):
		pass

	def prev_window(self, window, window_manager):
		return None

	def next_window(self, window, window_manager):
		return None

	def focus_on(self, window):
		pass

	def reflow(self, window_manager, screen, space_id):
		pass

class CenterStageLayout(Layout):
	"""
	An extremely simple layout that centers all windows on the screen, allowing
	for a uniform border space around them.

	:param int border: The border width, in pixels.
	:param bool ignore_menu: Whether to ignore the space taken up by the menu.

	For example::

		layout = CenterStageLayout(border = 40, ignore_menu = False)

	"""

	def reflow(self, window_manager = None, screen = NSScreen.mainScreen(), space_id = None):
		menubar_offset = 0 if self.ignore_menu else 22
		
		windows = window_manager.get_managed_windows(screen, space_id)
		screen_frame = screen.frame()

		for window in windows:
			left = screen_frame[0][0] + self.border
			top = screen_frame[0][1] + self.border + menubar_offset
			right = screen_frame[1][0] - self.border
			bottom = screen_frame[1][1] - self.border - menubar_offset
			window.frame = (left, top, right - left, bottom - top)

class PanelLayout(Layout):
	"""
	A simple layout that positions windows in two equally-sized columns on the
	screen. The 'master' window is on the left.

	:param int border: The border width, in pixels.
	:param int gutter: The space between panels, in pixels.
	:param bool ignore_menu: Whether to ignore the space taken up by the menu.

	For example::

		layout = PanelLayout(border = 40, gutter = 40, ignore_menu = False)

	"""

	def reflow(self, window_manager = None, screen = NSScreen.mainScreen(), space_id = None):
		menubar_offset = 0 if self.ignore_menu else 22
		
		windows = window_manager.get_managed_windows(screen, space_id)
		screen_frame = screen.frame()

		left = screen_frame[0][0] + self.border
		top = screen_frame[0][1] + self.border + menubar_offset
		right = screen_frame[1][0] - self.border
		bottom = screen_frame[1][1] - self.border - menubar_offset

		gutter_left = (screen_frame[1][0] - self.gutter) / 2
		gutter_right = gutter_left + self.gutter

		count = 0
		for window in windows:
			if count % 2 == 0:
				window.frame = (left, top, gutter_left - left, bottom - top)
			else:
				window.frame = (gutter_right, top, right - gutter_right, bottom - top)
			count += 1

class VerticalSplitLayout(Layout):
	"""
	A simple layout that positions windows in two equally-sized columns on the
	screen. The 'master' window is on the left.

	:param int border: The border width, in pixels.
	:param int gutter: The space between panels, in pixels.
	:param float ratio: The ratio between master/nonmaster windows.
	:param bool ignore_menu: Whether to ignore the space taken up by the menu.

	For example::

		layout = VerticalSplitLayout(border = 40, gutter = 40, ratio = 0.5, ignore_menu = False)

	"""

	def reflow(self, window_manager = None, screen = NSScreen.mainScreen(), space_id = None):
		menubar_offset = 0 if self.ignore_menu else 22
		
		windows = window_manager.get_managed_windows(screen, space_id)
		screen_frame = screen.frame()

		left = screen_frame[0][0] + self.border
		top = screen_frame[0][1] + self.border + menubar_offset
		right = screen_frame[1][0] - self.border
		bottom = screen_frame[1][1] - self.border - menubar_offset

		gutter_left = screen_frame[1][0] * self.ratio - self.gutter / 2
		gutter_right = gutter_left + self.gutter

		slave_count = len(windows) - 1
		logging.debug('Number of slave windows: %d.', slave_count)
		slave_height = ((bottom - top) - self.gutter * (slave_count - 1)) / slave_count
		logging.debug('Slave window height is %f.', slave_height)
		count = 0
		offset = 0
		for window in windows:
			if count == 0:
				window.frame = (left, top, gutter_left - left, bottom - top)
			else:
				window.position = (gutter_right, top + offset)
				window.size = (right - gutter_right, slave_height)
				offset += slave_height + self.gutter
				logging.debug('New window frame: %f, %f, %f, %f', window.position[0], window.position[1], window.size[0], window.size[1])
			count += 1
