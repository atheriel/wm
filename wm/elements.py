import AppKit
import objc

import wm._accessibility as acbl

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
		num_windows, error = self._element.count('AXWindows')
		if error == None:
			if num_windows != 0:
				windowrefs, error = self._element.get('AXWindows')
				for ref in windowrefs:
					self._windows.append(AccessibleWindow(ref, self))
		else: print error

	@property
	def bundle(self):
		return self._bundle
	
	@property
	def title(self):
		if self._title: # Cache the title, since it won't change
			return self._title
		else:
			title, error = self._element.get(AppKit.NSAccessibilityTitleAttribute)
			if error == None:
				self._title = title
			else:
				print 'No title found. Error', error
			return self._title

	@property
	def hidden(self):
		_hidden, error = self._element.get('AXHidden')
		if error == None:
			return _hidden
		else:
			print 'Error: %d' % error
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
			print 'Error: %d' % error
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
			print 'Error: %d' % error
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

def new_application(pid, bundle, debug = False):
	app = None
	ref = acbl.create_application_ref(pid)
	role, error = ref.get(AppKit.NSAccessibilityRoleAttribute)
	
	if error == -25211 and debug:
		print '>   Bundle <%s> is not available to the Accessibility API.' % bundle
	elif error != None and debug:
		print '>   Bundle <%s> role request failed with error %d.' % (bundle, error)
	elif role == u'AXApplication':
		app = AccessibleApplication(ref, bundle)
		if debug: print '>   Bundle <%s> is an accessible application.' % bundle
	elif debug:
		print '>   Bundle <%s> is not an accessible application, role is %s.' % (bundle, role)

	return app

def get_accessible_applications(ignored_bundles = [], debug = False):
	"""
	Get a list of all available AccessibleApplications.

	:param [str,] ignored_bundles: Bundles that should not be included.
	:param bool debug: Whether to print debugging information.
	"""
	running_apps = []
		
	# Get all running apps
	if debug: print 'Getting running applications from the sharedWorkspace...'
	workspace = AppKit.NSWorkspace.sharedWorkspace()
	for application in workspace.runningApplications():
		
		# Skip weird stuff
		if not application.bundleIdentifier():
			continue
		# Apps we should ignore
		if application.bundleIdentifier() in ignored_bundles:
			if debug: print '>   Bundle <%s> will be ignored.' % application.bundleIdentifier()
			continue
		
		# Create AXUIElementRef
		ref = acbl.create_application_ref(application.processIdentifier())
		role, error = ref.get(AppKit.NSAccessibilityRoleAttribute)
		
		# Deal with errors/responses
		if error == -25211 and debug:
			print '>   Bundle <%s> is not available to the Accessibility API.' % application.bundleIdentifier()
		elif error != None and debug:
			print '>   Bundle <%s> role request failed with error %d.' % (application.bundleIdentifier(), error)
		elif role == u'AXApplication':
			running_apps.append(AccessibleApplication(ref, application.bundleIdentifier()))
			if debug: print '>   Bundle <%s> is an accessible application.' % application.bundleIdentifier()
		elif debug:
			print '>   Bundle <%s> is not an accessible application, role is %s.' % (application.bundleIdentifier(), role)
	
	return running_apps