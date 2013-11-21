import logging
import objc
from Quartz import *

import elements, config, layout

def _add_hotkey_callback(func):
	mask = CGEventMaskBit(kCGEventKeyDown)
	tap = CGEventTapCreate(kCGSessionEventTap, kCGHeadInsertEventTap, kCGEventTapOptionListenOnly, mask, func, None)
	tap_source = CFMachPortCreateRunLoopSource(None, tap, 0)
	CFRunLoopAddSource(CFRunLoopGetCurrent(), tap_source, kCFRunLoopDefaultMode)

	# Enable the tap
	CGEventTapEnable(tap, True)

class ObserverHelper(NSObject):
	"""
	Watches several notifications important to the WindowManager.
	"""
	def init(self):
		self = super(ObserverHelper, self).init()
		if self != None:
			self.window_manager = None

			# Start watching notifications
			nc = NSWorkspace.sharedWorkspace().notificationCenter()
			nc.addObserver_selector_name_object_(self, self.appLaunched_, 'NSWorkspaceDidLaunchApplicationNotification', None)
			nc.addObserver_selector_name_object_(self, self.appTerminated_, 'NSWorkspaceDidTerminateApplicationNotification', None)
			nc.addObserver_selector_name_object_(self, self.appHidden_, 'NSWorkspaceDidHideApplicationNotification', None)
			nc.addObserver_selector_name_object_(self, self.appUnhidden_, 'NSWorkspaceDidUnhideApplicationNotification', None)
			nc.addObserver_selector_name_object_(self, self.spaceChanged_, 'NSWorkspaceActiveSpaceDidChangeNotification', None)

			logging.info('An ObserverHelper is now watchig notifications in the workspace.')
		
		return self

	@objc.typedSelector(b'v@:@')
	def appLaunched_(self, notification):
		if self.window_manager != None:
			logging.info('New app launched.')
			bundle = notification.userInfo()['NSApplicationBundleIdentifier']
			pid = notification.userInfo()['NSApplicationProcessIdentifier']
			self.window_manager._add_app(pid, bundle)

	@objc.typedSelector(b'v@:@')
	def appTerminated_(self, notification):
		if self.window_manager != None:
			name = notification.userInfo()['NSApplicationName']
			self.window_manager._remove_app(name)

	@objc.typedSelector(b'v@:@')
	def appHidden_(self, notification):
		try:
			name = notification.userInfo()['NSWorkspaceApplicationKey'].localizedName()
			logging.debug('Application \'%s\' has been hidden.', name)
			if self.window_manager != None:
	 			self.window_manager.reflow()
	 	except KeyError:
	 		logging.debug('The notification did not contain the expected dictionary entry.')

	@objc.typedSelector(b'v@:@')
	def appUnhidden_(self, notification):
		try:
			name = notification.userInfo()['NSWorkspaceApplicationKey'].localizedName()
			logging.debug('Application \'%s\' is no longer hidden.', name)
			if self.window_manager != None:
	 			self.window_manager.reflow()
	 	except KeyError:
	 		logging.debug('The notification did not contain the expected dictionary entry.')

	@objc.typedSelector(b'v@:@')
	def spaceChanged_(self, notification):
		logging.debug('User has changed spaces.')

class WindowManager(object):
	"""
	Defines a class that should manage windows on OS X.
	"""
	def __init__(self, config_file = None):
		logging.info('Starting window manager.')
		
		self.update(config_file)

		self._layout = layout.VerticalSplitLayout(border = 40, gutter = 40, ratio = 0.5, ignore_menu = True)

	def update(self, config_file = None):
		self._apps = dict()
		self._windows = []

		# Load running apps
		config.read_config(config_file)
		apps = elements.get_accessible_applications(config.IGNORED_BUNDLES)
		for app in apps:
			self._apps[app.title] = app
			for win in app._windows:
				self._add_window(win)

		logging.info('The window manager is now aware of: %s', ', '.join(self._apps.keys()))

	def get_managed_windows(self, screen = NSScreen.mainScreen(), spaceId = None):
		_windows = []

		# Don't include those from hidden apps
		for win in self._windows:
			if win._parent.hidden:
				logging.debug('Window is currently hidden.')
			elif win.minimized:
				logging.debug('Window is currently minimized.')
			else:
				logging.debug('Minimized: %s.', win.minimized)
				_windows.append(win)

		return _windows

	def reflow(self):
		logging.info('Reflowing...')
		self._layout.reflow(self)

	def app_names(self):
		return self._apps.keys()

	def _add_app(self, pid, bundle):
		if not bundle in config.IGNORED_BUNDLES:
			app = elements.new_application(pid, bundle)
			if app:
				self._apps[app.title] = app
				for win in app._windows:
					self._add_window(win)
				logging.info('The window manager is now aware of %s.', app.title)
				self.reflow()
	
	def _remove_app(self, name):
		for win in self._windows:
			if win._parent.title == name: self._windows.remove(win)
		del self._apps[name]
		logging.info('The window manager is no longer aware of %s.', name)
		self.reflow()

	def _add_window(self, window):
		if window.resizable:
			self._windows.append(window)
