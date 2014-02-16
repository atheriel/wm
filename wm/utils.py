from argparse import HelpFormatter


class SingletonMetaclass(type):
    """
    This class is intended to be used as a metatype for classes that follow the
    singleton pattern. It maintains a single copy of the object.
    """
    def __init__(cls, name, bases, dict):
        super(SingletonMetaclass, cls).__init__(cls, bases, dict)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SingletonMetaclass, cls).__call__(*args, **kwargs)
        return cls._instance


class WellSpacedHelpFormatter(HelpFormatter):
    """
    A slight modification to the default HelpFormatter, which should look like
    the following::

        -s, --long
        -s, --long <arg>
            --long-only <arg>
        -s, --long-one, --long-two <arg>
    """

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar

        else:
            options = ''
            args = ''

            if len(action.option_strings) == 1:
                options = '    %s' % action.option_strings[0]
            elif len(action.option_strings) == 2:
                options = '%s, %s' % (action.option_strings[0], action.option_strings[1])
            else:
                opt_list = []
                for option_string in action.option_strings:
                    opt_list.append('%s' % option_string)
                options = ', '.join(opt_list)

            if action.nargs != 0:
                default = action.dest.upper()
                args = self._format_args(action, default)

            return options + ' ' + args

    def _metavar_formatter(self, action, default_metavar):
        if action.metavar is not None:
            result = action.metavar
        elif action.choices is not None:
            # Modify choices output from {a,b,c} to [a, b, c]
            # choice_strs = [str(choice) for choice in action.choices]
            # result = '[%s]' % ', '.join(choice_strs)
            result = '<arg>'
        else:
            result = default_metavar

        def format(tuple_size):
            if isinstance(result, tuple):
                return result
            else:
                return (result, ) * tuple_size
        return format
