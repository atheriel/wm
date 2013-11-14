import AppKit, objc

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
		
		return self

	@objc.typedSelector(b'v@:@')
	def appLaunched_(self, notification):
		# print 'A new application has launched.'
		if self.window_manager != None:
			bundle = notification.userInfo()['NSApplicationBundleIdentifier']
			pid = notification.userInfo()['NSApplicationProcessIdentifier']
			self.window_manager._add_app(pid, bundle)

	@objc.typedSelector(b'v@:@')
	def appTerminated_(self, notification):
		# print 'An application has terminated.'
		print notification.userInfo()
		if self.window_manager != None:
			name = notification.userInfo()['NSApplicationName']
			self.window_manager._remove_app(name)

	@objc.typedSelector(b'v@:@')
	def appHidden_(self, notification):
		# print 'App has been hidden.'
		if self.window_manager != None:
 			self.window_manager.reflow()

	@objc.typedSelector(b'v@:@')
	def appUnhidden_(self, notification):
		# print 'App has been unhidden.'
		if self.window_manager != None:
 			self.window_manager.reflow()

	@objc.typedSelector(b'v@:@')
	def spaceChanged_(self, notification):
		print 'User has changed spaces.'

class WindowManager(object):
	"""
	Defines a class that should manage windows on OS X.
	"""
	def __init__(self, config_file = 'wm.rc', debug = False):
		self.update(config_file, debug)

		self._layout = layout.PanelLayout(border = 40, gutter = 40, ignore_menu = True)

		if debug: print 'Window Manager has finished started up.'

	def update(self, config_file = 'wm.rc', debug = False):
		self._debug = debug
		self._apps = dict()
		self._windows = []

		# Load running apps
		config.read_config(config_file)
		apps = elements.get_accessible_applications(config.IGNORED_BUNDLES, self._debug)
		for app in apps:
			self._apps[app.title] = app
			for win in app._windows:
				self._add_window(win)

	def get_managed_windows(self, screen = AppKit.NSScreen.mainScreen(), spaceId = None):
		_windows = []

		# Don't include those from hidden apps
		for win in self._windows:
			if not win._parent.hidden:
				_windows.append(win)

		return _windows

	def reflow(self):
		self._layout.reflow(self)

	def app_names(self):
		return self._apps.keys()

	def _add_app(self, pid, bundle):
		if not bundle in config.IGNORED_BUNDLES:
			app = elements.new_application(pid, bundle, self._debug)
			if app:
				self._apps[app.title] = app
	
	def _remove_app(self, name):
		del self._apps[name]
		if self._debug: print 'Application %s has been removed from the window manager.' % name

	def _add_window(self, window):
		if window.resizable:
			self._windows.append(window)
