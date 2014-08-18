# -*- test-case-name: twisted.python.logger.test.test_file -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
#
# Author: Roberto Polli <roberto.polli@babel.it>

"""
File log observer.
"""

from zope.interface import implementer
import syslog as stdsyslog

from ._observer import ILogObserver
from ._format import formatTime
from ._format import timeFormatRFC3339
from ._format import formatEventAsClassicLogText
from ._levels import LogLevel

# These defaults come from the Python syslog docs.
DEFAULT_OPTIONS = 0
DEFAULT_FACILITY = stdsyslog.LOG_USER

# Mappings to Python's syslog module
toSyslogLevelMapping = {
        LogLevel.debug: stdsyslog.LOG_DEBUG,
        LogLevel.info: stdsyslog.LOG_INFO,
        LogLevel.warn: stdsyslog.LOG_WARNING,
        LogLevel.error: stdsyslog.LOG_ERR,
        LogLevel.critical: stdsyslog.LOG_ALERT,
       }
fromSyslogLevelMapping = dict([
    (value, key) for (key, value)
    in toSyslogLevelMapping.items()
])

@implementer(ILogObserver)
class SyslogObserver(object):
    """
    A log observer for logging to syslog.

    See L{twisted.python.log} for context.

    This logObserver will automatically use LOG_ALERT priority for logged
    failures (such as from C{log.err()}), but you can use any priority and
    facility by setting the 'C{syslogPriority}' and 'C{syslogFacility}' keys in
    the event dict.
    """
    openlog = stdsyslog.openlog

    def __init__(self, formatEvent, prefix, options=DEFAULT_OPTIONS,
                 facility=DEFAULT_FACILITY, syslog=stdsyslog.syslog):
        """
        @type prefix: C{str}
        @param prefix: The syslog prefix to use.

        @type options: C{int}
        @param options: A bitvector represented as an integer of the syslog
            options to use.

        @type facility: C{int}
        @param facility: An indication to the syslog daemon of what sort of
            program this is (essentially, an additional arbitrary metadata
            classification for messages sent to syslog by this observer).
            
        @param formatEvent: A callable that formats an event.
        @type formatEvent: L{callable} that takes an C{event} argument and
            returns a formatted event as L{unicode}.

        """
        self.openlog(prefix, options, facility)
        
        if False:
            self._encoding = "utf-8"
        else:
            self._encoding = None

        self.formatEvent = formatEvent
        self.syslog = stdsyslog.syslog

    def __call__(self, event):
        """
        Write event to file.

        @param event: An event.
        @type event: L{dict}
        """
        text = self.formatEvent(event)

        if text is None:
            text = u""

        # Set priority by loglevel and eventually
        #  override it if log_failure or syslogPriority is defined
        try:
            priority = toSyslogLevelMapping[event['log_level']]
        except KeyError:
            priority = stdsyslog.LOG_INFO
            
        if "log_failure" in event:
            text = u"\n".join((text, event["log_failure"].getTraceback()))
            priority = stdsyslog.LOG_ALERT
        elif 'syslogPriority' in event:
            priority = int(event['syslogPriority'])


        if self._encoding is not None:
            text = text.encode(self._encoding)

        if text:
            facility = 0                
            if 'syslogFacility' in event:
                facility = int(event['syslogFacility'])
            # write multi-line text
            lines = text.split('\n')
            while lines[-1:] == ['']:
                lines.pop()
        
            firstLine = True
            for line in lines:
                if firstLine:
                    firstLine = False
                else:
                    # indent further lines
                    line = '\t' + line
       
                self.syslog(priority | facility, text)



def textSyslogObserver(prefix="Twisted", options=DEFAULT_OPTIONS,
                 facility=DEFAULT_FACILITY, timeFormat=timeFormatRFC3339):
    """
    Create a L{SyslogObserver} that emits text to a specified syslog object.

    @type prefix: C{str}
    @param prefix: The syslog prefix to use.

    @type options: C{int}
    @param options: A bitvector represented as an integer of the syslog
        options to use.

    @type facility: C{int}
    @param facility: An indication to the syslog daemon of what sort of
        program this is (essentially, an additional arbitrary metadata
        classification for messages sent to syslog by this observer).

    @param timeFormat: The format to use when adding timestamp prefixes to
        logged events.  If C{None}, or for events with no C{"log_timestamp"}
        key, the default timestamp prefix of C{u"-"} is used.
    @type timeFormat: L{unicode} or C{None}

    @return: A file log observer.
    @rtype: L{SyslogObserver}
    """
    def formatEvent(event):
        return formatEventAsClassicLogText(
            event, formatTime=lambda e: formatTime(e, timeFormat)
        )

    return SyslogObserver(formatEvent, prefix, options=DEFAULT_OPTIONS,
                 facility=DEFAULT_FACILITY)
