# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
#
# Author: Roberto Polli <roberto.polli@babel.it>

"""
Test cases for L{twisted.python.logger._file}.
"""

from zope.interface.verify import verifyObject, BrokenMethodImplementation

from twisted.trial.unittest import TestCase

from twisted.python.failure import Failure
from twisted.python.compat import unicode
from .._observer import ILogObserver
from .._syslog import SyslogObserver
from .._syslog import textSyslogObserver

def mock_syslog(list_buffer):
    """
        A mock function to collect syslog() invocations into 
         a given list_buffer.
    """
    def tmp(*args, **kwds):
        list_buffer.append((args, kwds))
    return tmp

class SyslogObserverTests(TestCase):
    """
    Tests for L{SyslogObserver}.
    """
    
    def test_interface(self):
        """
        L{SyslogObserver} is an L{ILogObserver}.
        """
        observer = SyslogObserver(lambda e: unicode(e), prefix="test_syslog")
        try:
            verifyObject(ILogObserver, observer)
        except BrokenMethodImplementation as e:
            self.fail(e)



    def test_observeWrites(self):
        """
        L{SyslogObserver} writes to the given file when it observes events.
        """
        result = []
        observer = SyslogObserver(lambda e: unicode(e), prefix="test_syslog")
        observer.syslog = mock_syslog(result)
        event = dict(x=1)
        observer(event)
        #unpack the syslog event
        (syslog_flags, syslog_text), _ = result[0] 
        self.assertEquals(syslog_text, unicode(event))



    def _test_observeWrites(self, what, count):
        """
        Verify that observer performs an expected number of writes when the
        formatter returns a given value.

        @param what: the value for the formatter to return.
        @type what: L{unicode}

        @param count: the expected number of writes.
        @type count: L{int}
        """
        try:
            fileHandle = DummyFile()
            observer = SyslogObserver(lambda e: what, prefix="test_syslog")
            event = dict(x=1)
            observer(event)
            self.assertEquals(fileHandle.writes, count)

        finally:
            fileHandle.close()


    def test_observeWritesNone(self):
        """
        L{SyslogObserver} does not write to the given file when it observes
        events and C{formatEvent} returns C{None}.
        """
        self._test_observeWrites(None, 0)


    def test_observeWritesEmpty(self):
        """
        L{SyslogObserver} does not write to the given file when it observes
        events and C{formatEvent} returns C{u""}.
        """
        self._test_observeWrites(u"", 0)


    def test_observeFailure(self):
        """
        If the C{"log_failure"} key exists in an event, the observer should
        append the failure's traceback to the output.
        """

        result = []
        observer = SyslogObserver(lambda e: unicode(e), prefix="test_syslog")
        observer.syslog = mock_syslog(result)
        try:
            1 / 0
        except ZeroDivisionError:
            failure = Failure()

        event = dict(log_failure=failure)
        observer(event)
        (syslog_flags, output), _ = result[0]
        self.assertTrue(
            output.startswith("{0}\nTraceback ".format(unicode(event))),
            "Incorrect output:\n{0}".format(output)
        )





class TextSyslogObserverTests(TestCase):
    """
    Tests for L{textSyslogObserver}.
    """

    def test_returnsSyslogObserver(self):
        """
        L{textSyslogObserver} returns a L{SyslogObserver}.
        """
        observer = textSyslogObserver(prefix="Twisted")
        self.assertIsInstance(observer, SyslogObserver)



    def test_timeFormat(self):
        """
        Returned L{SyslogObserver} has the correct text message.
        """
        result = []
        observer = textSyslogObserver(prefix="test_syslog", timeFormat=u"%f")
        observer.syslog = mock_syslog(result)
        observer(dict(log_format=u"XYZZY", log_time=1.23456))
        (syslog_flags, syslog_text), _ = result[0]
        self.assertEquals(syslog_text, u"234560 [-#-] XYZZY\n")



class DummyFile(object):
    """
    File that counts writes and flushes.
    """

    def __init__(self):
        self.writes = 0
        self.flushes = 0


    def write(self, data):
        """
        Write data.

        @param data: data
        @type data: L{unicode} or L{bytes}
        """
        self.writes += 1


    def flush(self):
        """
        Flush buffers.
        """
        self.flushes += 1


    def close(self):
        """
        Close.
        """
        pass
