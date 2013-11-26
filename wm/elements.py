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
        num_windows = self._element.count('AXWindows')
        if num_windows != 0:
            for ref in self._element['AXWindows']:
                self._windows.append(AccessibleWindow(ref, self))

    @property
    def bundle(self):
        return self._bundle

    @property
    def title(self):
        if self._title is None:  # Cache the title, since it won't change
            if 'AXTitle' in self._element:
                self._title = self._element['AXTitle']
            else:
                logging.debug('No title found for bundle %s.', self._bundle)

        return self._title

    @property
    def hidden(self):
        if 'AXHidden' in self._element:
            return self._element['AXHidden']
        else:
            return None

    @hidden.setter
    def hidden(self, value):
        if 'AXHidden' in self._element and self._element.can_set('AXHidden'):
            self._element['AXHidden'] = value
        else:
            logging.debug('Could not set application with bundle %s as (un)hidden.', self._bundle)


class AccessibleWindow(object):
    """
    Defines a window available to the Accessibility API.
    """
    def __init__(self, element, parent):
        self._element = element
        self._parent = parent

    @property
    def position(self):
        if 'AXPosition' in self._element:
            return self._element.get('AXPosition')
        else:
            logging.debug('No AXPosition property found for window in app %s.', self._parent.title)
            return None

    @position.setter
    def position(self, value):
        if 'AXPosition' in self._element and self._element.can_set('AXPosition'):
            self._element['AXPosition'] = value
        else:
            logging.debug('Could not set AXPosition property found for window in app %s.', self._parent.title)

    @property
    def size(self):
        if 'AXSize' in self._element:
            return self._element['AXSize']
        else:
            logging.debug('No AXSize property found for window in app %s.', self._parent.title)
            return None

    @size.setter
    def size(self, value):
        if 'AXSize' in self._element and self._element.can_set('AXSize'):
            self._element['AXSize'] = value
        else:
            logging.debug('Could not set AXSize property found for window in app %s.', self._parent.title)

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
        if 'AXMinimized' in self._element:
            return self._element['AXMinimized']
        else:
            logging.debug('No AXMinimized property found for window in app %s.', self._parent.title)
            return None


def new_application(pid, bundle):
    """
    Create an AccessibleApplication manually using its PID and bundle
    identifier.
    """
    app = None
    ref = acbl.create_application_ref(pid)
    try:
        if ref['AXRole'] == u'AXApplication':
            app = AccessibleApplication(ref, bundle)
            logging.debug('Bundle <%s> is an accessible application.', bundle)
        else:
            logging.debug('Bundle <%s> is not an accessible application, role is %s.', bundle, ref['AXRole'])
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
            if ref['AXRole'] == u'AXApplication':
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
