# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.trial.unittest import TestCase
from twisted.python.failure import Failure

import logging
try:
    import syslog as stdsyslog
except ImportError:
    stdsyslog = None
else:
    from twisted.python import syslog



class SyslogObserverTests(TestCase):
    """
    Tests for L{SyslogObserver} which sends Twisted log events to the syslog.
    """
    events = None

    if stdsyslog is None:
        skip = "syslog is not supported on this platform"

    def setUp(self):
        self.patch(syslog.SyslogObserver, 'openlog', self.openlog)
        self.patch(syslog.SyslogObserver, 'syslog', self.syslog)
        self.observer = syslog.SyslogObserver('SyslogObserverTests')


    def openlog(self, prefix, options, facility):
        self.logOpened = (prefix, options, facility)
        self.events = []


    def syslog(self, options, message):
        self.events.append((options, message))


    def test_emitWithoutMessage(self):
        """
        L{SyslogObserver.emit} ignores events with an empty value for the
        C{'message'} key.
        """
        self.observer.emit({'message': (), 'isError': False, 'system': '-'})
        self.assertEqual(self.events, [])


    def test_emitCustomPriority(self):
        """
        L{SyslogObserver.emit} uses the value of the C{'syslogPriority'} as the
        syslog priority, if that key is present in the event dictionary.
        """
        self.observer.emit({
            'message': ('hello, world',), 'isError': False, 'system': '-',
            'syslogPriority': stdsyslog.LOG_DEBUG
        })
        self.assertEqual(
            self.events,
            [(stdsyslog.LOG_DEBUG, '[-] hello, world')]
        )


    def test_emitErrorPriority(self):
        """
        L{SyslogObserver.emit} uses C{LOG_ALERT} if the event represents an
        error.
        """
        self.observer.emit({
            'message': ('hello, world',), 'isError': True, 'system': '-',
            'failure': Failure(Exception("foo")),
        })
        self.assertEqual(
            self.events,
            [(stdsyslog.LOG_ALERT, '[-] hello, world')]
        )


    def test_emitCustomPriorityOverridesError(self):
        """
        L{SyslogObserver.emit} uses the value of the C{'syslogPriority'} key if
        it is specified even if the event dictionary represents an error.
        """
        self.observer.emit({
            'message': ('hello, world',), 'isError': True, 'system': '-',
            'syslogPriority': stdsyslog.LOG_NOTICE,
            'failure': Failure(Exception("bar")),
        })
        self.assertEqual(
            self.events,
            [(stdsyslog.LOG_NOTICE, '[-] hello, world')]
        )


    def test_emitCustomFacility(self):
        """
        L{SyslogObserver.emit} uses the value of the C{'syslogPriority'} as the
        syslog priority, if that key is present in the event dictionary.
        """
        self.observer.emit({
            'message': ('hello, world',), 'isError': False, 'system': '-',
            'syslogFacility': stdsyslog.LOG_CRON,
        })
        self.assertEqual(
            self.events,
            [(stdsyslog.LOG_INFO | stdsyslog.LOG_CRON, '[-] hello, world')]
        )


    def test_emitCustomSystem(self):
        """
        L{SyslogObserver.emit} uses the value of the C{'system'} key to prefix
        the logged message.
        """
        self.observer.emit({
            'message': ('hello, world',), 'isError': False,
            'system': 'nonDefaultSystem',
        })
        self.assertEqual(
            self.events,
            [(stdsyslog.LOG_INFO, "[nonDefaultSystem] hello, world")]
        )


    def test_emitMessage(self):
        """
        L{SyslogObserver.emit} logs the value of the C{'message'} key of the
        event dictionary it is passed to the syslog.
        """
        self.observer.emit({
            'message': ('hello, world',), 'isError': False,
            'system': '-',
        })
        self.assertEqual(
            self.events,
            [(stdsyslog.LOG_INFO, "[-] hello, world")]
        )


    def test_emitMultilineMessage(self):
        """
        Each line of a multiline message is emitted separately to the syslog.
        """
        self.observer.emit({
            'message': ('hello,\nworld',), 'isError': False,
            'system': '-',
        })
        self.assertEqual(
            self.events,
            [
                (stdsyslog.LOG_INFO, '[-] hello,'),
                (stdsyslog.LOG_INFO, '[-] \tworld'),
            ]
        )


    def test_emitStripsTrailingEmptyLines(self):
        """
        Trailing empty lines of a multiline message are omitted from the
        messages sent to the syslog.
        """
        self.observer.emit({
            'message': ('hello,\nworld\n\n',), 'isError': False,
            'system': '-',
        })
        self.assertEqual(
            self.events,
            [
                (stdsyslog.LOG_INFO, '[-] hello,'),
                (stdsyslog.LOG_INFO, '[-] \tworld'),
            ]
        )


    def assertPriorityMapping(self, expected, event):
        """
        Check that when emitted, C{event} is translated into
        C{expected} syslog priority.

        @param expected: a L{syslog} priority
        @type expected: C{int}
        @param event: an event
        @type event: C{dict}

        """
        m = {
            'message': ('hello,\nworld\n\n',),
            'isError': False,
            'system': '-',
        }
        m.update(event)
        self.observer.emit(m)
        self.assertEqual(
            self.events,
            [(expected, '[-] hello,'), (expected, '[-] \tworld')]
        )


    def test_emitLevelMissingLevelUseDefault(self):
        """
        On missing logLevel defaults to stdsyslog.LOG_INFO.
        """
        self.assertPriorityMapping(stdsyslog.LOG_INFO, {})


    def test_emitLevelInvalidLevelUseDefault(self):
        """
        On invalid logLevel defaults to stdsyslog.LOG_INFO.
        """
        self.assertPriorityMapping(stdsyslog.LOG_INFO, {'logLevel': 'INVALID'})


    def test_emitLevelWARN(self):
        """
        Logging levels are nicely mapped to syslog priorities.
        """
        self.assertPriorityMapping(
            stdsyslog.LOG_WARNING, {'logLevel': logging.WARN}
        )


    def test_emitLevelERR(self):
        """
        Logging levels are nicely mapped to syslog priorities.
        """
        self.assertPriorityMapping(
            stdsyslog.LOG_ERR, {'logLevel': logging.ERROR}
        )


    def test_emitLevelDEBUG(self):
        """
        Logging levels are nicely mapped to syslog priorities.
        """
        self.assertPriorityMapping(
            stdsyslog.LOG_DEBUG, {'logLevel': logging.DEBUG}
        )


    def test_emitLevelIsError(self):
        """
        Messages with isError=True are mapped to LOG_ALERT.
        """
        self.assertPriorityMapping(
            stdsyslog.LOG_ALERT, {'isError': True}
        )


    def test_emitLevelOvverrideIsError(self):
        """
        Using logLevel ovverrides isError.
        """
        self.assertPriorityMapping(
            stdsyslog.LOG_INFO, {'isError': True, 'logLevel': logging.INFO}
        )


    def test_emitLevelPriorityOverridesLogLevel(self):
        """
        Using syslogPriority overrides logLevel.
        """
        self.assertPriorityMapping(
            stdsyslog.LOG_ALERT,
            {
                'isError': False,
                'logLevel': logging.INFO,
                'syslogPriority': stdsyslog.LOG_ALERT,
            }
        )


    def test_emitLevelWARNString(self):
        """
        Logging levels are nicely mapped to syslog priorities
        """
        self.assertPriorityMapping(
            stdsyslog.LOG_WARNING, {'logLevel': 'WARN'}
        )


    def test_emitLevelWARNINGString(self):
        """
        Logging levels are nicely mapped to syslog priorities
        """
        self.assertPriorityMapping(
            stdsyslog.LOG_WARNING, {'logLevel': 'WARNING'}
        )


    def test_emitLevelCRITICALString(self):
        """
        Logging levels are nicely mapped to syslog priorities
        """
        self.assertPriorityMapping(
            stdsyslog.LOG_ALERT, {'logLevel': 'CRITICAL'}
        )


    def test_emitLevelFATALString(self):
        """
        Logging levels are nicely mapped to syslog priorities
        """
        self.assertPriorityMapping(
            stdsyslog.LOG_ALERT, {'logLevel': 'FATAL'}
        )