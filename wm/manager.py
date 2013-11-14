import AppKit, objc, logging

import elements, config, layout

class ObserverHelper(AppKit.NSObject):
	"""
	Watches several notifications important to the WindowManager.
	"""
	def init(self):
		self = super(ObserverHelper, self).init()
		if self != None:
			self.window_manager = None

			# Start watching notifications
			nc = AppKit.NSWorkspace.sharedWorkspace().notificationCenter()
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
			bundle = notification.userInfo()['NSApplicationBundleIdentifier']
			pid = notification.userInfo()['NSApplicationProcessIdentifier']
			self.window_manager._add_app(pid, bundle)

	@objc.typedSelector(b'v@:@')
	def appTerminated_(self, notification):
		print notification.userInfo()
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

		self._layout = layout.PanelLayout(border = 40, gutter = 40, ignore_menu = True)

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

	def get_managed_windows(self, screen = AppKit.NSScreen.mainScreen(), spaceId = None):
		_windows = []

		# Don't include those from hidden apps
		for win in self._windows:
			if not win._parent.hidden:
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
				logging.info('The window manager is now aware of %s.', app.title)
	
	def _remove_app(self, name):
		del self._apps[name]
		logging.info('The window manager is no longer aware of %s.', name)

	def _add_window(self, window):
		if window.resizable:
			self._windows.append(window)
