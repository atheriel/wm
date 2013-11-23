import AppKit, objc, logging

import _accessibility as acbl

class AccessibleApplication(object):
	"""
	Defines an application available to the Accessibility API.
	"""
	_systemwide_element = None
	
	def __init__(self, element, bundle):
		self._element = element
		self._bundle = bundle
		self._title = None
		self._windows = []

		if not self._systemwide_element:
			self._systemwide_element = acbl.create_systemwide_ref()

		# Gets the windows
		try:
			num_windows = self._element.count('AXWindows')
			if num_windows != 0:
				windowrefs, error = self._element.get('AXWindows')
				for ref in windowrefs:
					self._windows.append(AccessibleWindow(ref, self))
		except Exception as e:
			logging.debug('Error while fetching windows for bundle <%s>: %s', bundle, e.value)

	@property
	def bundle(self):
		return self._bundle
	
	@property
	def title(self):
		if self._title: # Cache the title, since it won't change
			return self._title
		else:
			title, error = self._element.get('AXTitle')
			if error == None:
				self._title = title
			else:
				logging.debug('No title found for bundle %s. Error %d.', self._bundle, error)
			return self._title

	@property
	def hidden(self):
		_hidden, error = self._element.get('AXHidden')
		if error == None:
			return _hidden
		else:
			logging.debug('No AXHidden property found for bundle %s. Error %d.', self._bundle, error)
			return None

	@hidden.setter
	def hidden(self, value):
		self._element.set('AXHidden', value)
	

class AccessibleWindow(object):
	"""
	Defines a window available to the Accessibility API.
	"""
	def __init__(self, element, parent):
		self._element = element
		self._parent = parent

	@property
	def position(self):
		_pos, error = self._element.get('AXPosition')
		if error == None:
			return _pos
		else:
			logging.debug('No AXPosition property found for window in app %s. Error %d.', self._parent.title, error)
			return None

	@position.setter
	def position(self, value):
		self._element.set('AXPosition', value)

	@property
	def size(self):
		_size, error = self._element.get('AXSize')
		if error == None:
			return _size
		else:
			logging.debug('No AXSize property found for window in app %s. Error %d.', self._parent.title, error)
			return None

	@size.setter
	def size(self, value):
		self._element.set('AXSize', value)

	@property
	def frame(self):
		# (left, top, width, height)
		position = self.position
		size = self.size
		if position == None or size == None:
			return None
		
		return (position[0], position[1], size[0], size[1])
	
	@frame.setter
	def frame(self, value):
		self.position = value[0], value[1]
		self.size = value[2], value[3]

	@property
	def resizable(self):
	    return self._element.can_set('AXSize') and self._element.can_set('AXPosition')

	@property
	def minimized(self):
		_min, error = self._element.get('AXMinimized')
		if error == None:
			return _min
		else:
			logging.debug('No AXMinimized property found for window in app %s. Error %d.', self._parent.title, error)
			return None

def new_application(pid, bundle):
	"""
	Create an AccessibleApplication manually using its PID and bundle
	identifier.
	"""
	app = None
	ref = acbl.create_application_ref(pid)
	role, error = ref.get(AppKit.NSAccessibilityRoleAttribute)
	
	if error == -25211:
		logging.debug('Bundle <%s> is not available to the Accessibility API.', bundle)
	elif error != None:
		logging.debug('Bundle <%s> role request failed with error %d.', bundle, error)
	elif role == u'AXApplication':
		app = AccessibleApplication(ref, bundle)
		logging.debug('Bundle <%s> is an accessible application.', bundle)
	elif debug:
		logging.debug('Bundle <%s> is not an accessible application, role is %s.', bundle, role)

	return app

def get_accessible_applications(ignored_bundles = []):
	"""
	Get a list of all available AccessibleApplications.

	:param [str, ...] ignored_bundles: Bundles that should not be included.
	"""
	running_apps = []
	_ignored = []
	_unavailable = []
	_accessibile = []
		
	# Get all running apps
	logging.debug('Getting running applications from the sharedWorkspace.')
	workspace = AppKit.NSWorkspace.sharedWorkspace()
	for application in workspace.runningApplications():
		
		# Skip weird stuff
		if not application.bundleIdentifier():
			continue
		# Apps we should ignore
		if application.bundleIdentifier() in ignored_bundles:
			_ignored.append(application.bundleIdentifier())
			continue
		
		# Create AXUIElementRef
		ref = acbl.create_application_ref(application.processIdentifier())
		role, error = ref.get(AppKit.NSAccessibilityRoleAttribute)
		
		# Deal with errors/responses
		if error == -25211:
			_unavailable.append(application.bundleIdentifier())
		elif error != None:
			logging.debug('Bundle <%s> role request failed with error %d.', application.bundleIdentifier(), error)
		elif role == u'AXApplication':
			running_apps.append(AccessibleApplication(ref, application.bundleIdentifier()))
			_accessibile.append(application.bundleIdentifier())
		else:
			_unavailable.append(application.bundleIdentifier())
	
	logging.debug('Current accessible application bundles: <%s>.', '>, <'.join(_accessibile))
	logging.debug('Currently ignored bundles: <%s>.', '>, <'.join(_ignored))
	logging.debug('Unavailable bundles: <%s>.', '>, <'.join(_unavailable))
	return running_apps
