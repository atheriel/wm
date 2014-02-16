import objc
import logging
from Quartz import *

import config
import daemon
import elements
import utils


def _accessibility_notifications_callback(notification, element):
    """
    Provides the callback for all watched notifications exposed through the Accessibility API.
    """
    if notification in ['AXWindowMiniaturized', 'AXWindowCreated']:
        WindowManager().reflow()
    logging.debug('Notification <%s> for application <%s>.', notification, element['AXTitle'])


class ObserverHelper(NSObject):
    """
    Watches several notifications important to the WindowManager.
    """
    def init(self):
        self = super(ObserverHelper, self).init()
        if self is not None:

            # Start watching notifications
            nc = NSWorkspace.sharedWorkspace().notificationCenter()
            nc.addObserver_selector_name_object_(self, self.appLaunched_, 'NSWorkspaceDidLaunchApplicationNotification', None)
            nc.addObserver_selector_name_object_(self, self.appTerminated_, 'NSWorkspaceDidTerminateApplicationNotification', None)
            nc.addObserver_selector_name_object_(self, self.appHidden_, 'NSWorkspaceDidHideApplicationNotification', None)
            nc.addObserver_selector_name_object_(self, self.appUnhidden_, 'NSWorkspaceDidUnhideApplicationNotification', None)
            nc.addObserver_selector_name_object_(self, self.spaceChanged_, 'NSWorkspaceActiveSpaceDidChangeNotification', None)

            logging.info('An ObserverHelper is now watching notifications in the workspace.')

        return self

    @objc.typedSelector(b'v@:@')
    def appLaunched_(self, notification):
        logging.info('New app launched.')
        bundle = notification.userInfo()['NSApplicationBundleIdentifier']
        pid = notification.userInfo()['NSApplicationProcessIdentifier']
        WindowManager()._add_app(pid, bundle)

    @objc.typedSelector(b'v@:@')
    def appTerminated_(self, notification):
        name = notification.userInfo()['NSApplicationName']
        WindowManager()._remove_app(name)

    @objc.typedSelector(b'v@:@')
    def appHidden_(self, notification):
        try:
            name = notification.userInfo()['NSWorkspaceApplicationKey'].localizedName()
            logging.debug('Application \'%s\' has been hidden.', name)
            WindowManager().reflow()
        except KeyError:
            logging.debug('The notification did not contain the expected dictionary entry.')

    @objc.typedSelector(b'v@:@')
    def appUnhidden_(self, notification):
        try:
            name = notification.userInfo()['NSWorkspaceApplicationKey'].localizedName()
            logging.debug('Application \'%s\' is no longer hidden.', name)
            WindowManager().reflow()
        except KeyError:
            logging.debug('The notification did not contain the expected dictionary entry.')

    @objc.typedSelector(b'v@:@')
    def spaceChanged_(self, notification):
        logging.debug('User has changed spaces.')


class WindowManager(daemon.Daemon):
    """
    Defines a class that should manage windows on OS X.
    """
    __metaclass__ = utils.SingletonMetaclass

    def __init__(self, pidfile, config_file = None):
        super(WindowManager, self).__init__(pidfile)

        self.update(config_file)

    def run(self):
        # Create notification observer
        observer = ObserverHelper.new()  # noqa
        
        # Allows calling arbitrary methods of WindowManager with hotkeys
        def hotkey_handler(proxy, etype, event, refcon):
            keyEvent = NSEvent.eventWithCGEvent_(event)
            flags = keyEvent.modifierFlags()

            if flags != 0:  # any key event we want deals with mod keys
                code = keyEvent.keyCode()

                # Cycle through registered hotkeys
                for name, value in config.HOTKEYS.items():
                    if (value[0] & flags) and value[1] == code:
                        # call the name of the hotkey as a function
                        getattr(WindowManager(), name)()
                        logging.debug('Called method \'%s\' in response to hotkey.', name)
                        continue

        # Register the callback for keyboard events
        mask = CGEventMaskBit(kCGEventKeyDown)
        tap = CGEventTapCreate(kCGSessionEventTap, kCGHeadInsertEventTap, kCGEventTapOptionListenOnly, mask, hotkey_handler, None)
        tap_source = CFMachPortCreateRunLoopSource(None, tap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), tap_source, kCFRunLoopDefaultMode)

        # Enable the tap
        CGEventTapEnable(tap, True)
        logging.info('Global hotkeys are now being watched.')

        self.reflow()

        # Run app loop
        try:
            CFRunLoopRun()
        except KeyboardInterrupt:
            logging.info('Stopping window manager.')

    def update(self, config_file = None):
        self._apps = dict()
        self._windows = []

        # Load running apps
        config.read_config(config_file)
        apps = elements.get_accessible_applications(config.IGNORED_BUNDLES)
        for app in apps:
            self._apps[app.title] = app
            app._element.set_callback(_accessibility_notifications_callback)
            app._element.watch('AXWindowMiniaturized', 'AXWindowCreated')
            for win in app._windows:
                self._add_window(win)

        logging.info('The window manager is now aware of: %s', ', '.join(self._apps.keys()))

        self._layout = config.LAYOUT

    def get_managed_windows(self, screen = NSScreen.mainScreen(), spaceId = None):
        _windows = []

        # Don't include those from hidden apps
        for win in self._windows:
            if not win._parent.hidden and not win.minimized:
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
            if win._parent.title == name:
                self._windows.remove(win)

        del self._apps[name]
        logging.info('The window manager is no longer aware of %s.', name)

        self.reflow()

    def _add_window(self, window):
        if window.resizable:
            self._windows.append(window)
            logging.debug('Added window for application %s.', window._parent.title)
        else:
            logging.debug('Window for application %s is not resizable. Ignoring it.', window._parent.title)
