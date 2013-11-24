import logging
from AppKit import NSWorkspace

import _accessibility as acbl


SYSTEMWIDE_ELEMENT = acbl.create_systemwide_ref()


class AccessibleApplication(object):
    """
    Defines an application available to the Accessibility API.
    """
    def __init__(self, element, bundle):
        self._element = element
        self._bundle = bundle
        self._title = None
        self._windows = []

        # Gets the windows
        try:
            num_windows = self._element.count('AXWindows')
            if num_windows != 0:
                for ref in self._element.get('AXWindows'):
                    self._windows.append(AccessibleWindow(ref, self))
        except Exception as e:
            logging.debug('Error while fetching windows for bundle <%s>: %s', bundle, e.args[0])

    @property
    def bundle(self):
        return self._bundle

    @property
    def title(self):
        if self._title is None:  # Cache the title, since it won't change
            try:
                self._title = self._element.get('AXTitle')
            except Exception as e:
                logging.debug('No title found for bundle %s. Exception: %s.', self._bundle, e.args[0])

        return self._title

    @property
    def hidden(self):
        try:
            _hidden = self._element.get('AXHidden')
            return _hidden
        except Exception as e:
            logging.debug('No AXHidden property found for bundle %s. Exception: %s.', self._bundle, e.args[0])
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
        try:
            _pos = self._element.get('AXPosition')
            return _pos
        except Exception as e:
            logging.debug('No AXPosition property found for window in app %s. Exception: %s.', self._parent.title, e.args[0])
            return None

    @position.setter
    def position(self, value):
        self._element.set('AXPosition', value)

    @property
    def size(self):
        try:
            _size = self._element.get('AXSize')
            return _size
        except Exception as e:
            logging.debug('No AXSize property found for window in app %s. Exception: %s.', self._parent.title, e.args[0])
            return None

    @size.setter
    def size(self, value):
        self._element.set('AXSize', value)

    @property
    def frame(self):
        # (left, top, width, height)
        position = self.position
        size = self.size
        if position is None or size is None:
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
        try:
            _min = self._element.get('AXMinimized')
            return _min
        except Exception as e:
            logging.debug('No AXMinimized property found for window in app %s. Exception: %s.', self._parent.title, e.args[0])
            return None


def new_application(pid, bundle):
    """
    Create an AccessibleApplication manually using its PID and bundle
    identifier.
    """
    app = None
    ref = acbl.create_application_ref(pid)
    try:
        role = ref.get('AXRole')
        if role == u'AXApplication':
            app = AccessibleApplication(ref, bundle)
            logging.debug('Bundle <%s> is an accessible application.', bundle)
        else:
            logging.debug('Bundle <%s> is not an accessible application, role is %s.', bundle, role)
    except acbl.APIDisabledError:
        logging.debug('Bundle <%s> is not available to the Accessibility API.', bundle)
    except Exception as e:
        logging.debug('Bundle <%s> role request failed with exception: %s.', bundle, e.args[0])

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
    workspace = NSWorkspace.sharedWorkspace()
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
        try:
            role = ref.get('AXRole')
            if role == u'AXApplication':
                running_apps.append(AccessibleApplication(ref, application.bundleIdentifier()))
                _accessibile.append(application.bundleIdentifier())
            else:
                _unavailable.append(application.bundleIdentifier())
        # Deal with errors
        except acbl.APIDisabledError:
            _unavailable.append(application.bundleIdentifier())
        except ValueError:
            _unavailable.append(application.bundleIdentifier())
        except Exception as e:
            logging.debug('Bundle <%s> role request failed with exception: %s', application.bundleIdentifier(), e.args[0])
            _unavailable.append(application.bundleIdentifier())

    logging.debug('Current accessible application bundles: <%s>.', '>, <'.join(_accessibile))
    logging.debug('Currently ignored bundles: <%s>.', '>, <'.join(_ignored))
    logging.debug('Unavailable bundles: <%s>.', '>, <'.join(_unavailable))
    return running_apps
