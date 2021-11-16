# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

class UnsupportedCFAError(ValueError):
    '''Unsupported Color Filter Array type'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s


class BiasError(ValueError):
    '''Value differs much from power of two'''
    def __init__(self, bias, levels, *args):
        self.bias = bias
        self.levels = levels

    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1} '.format(s, self.args[0], self.levels)
        s = '{0}.'.format(s)
        return s


class NotPowerOfTwoErrorBiasError(BiasError):
    '''Value differs much from a power of two'''
    pass
 

class TooDifferentValuesBiasError(BiasError):
    '''Differences in counts between channels exceed threshold'''
    pass
 

class IncorrectTimestampError(ValueError):
    '''Could not parse such timestamp'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s
