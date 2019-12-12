###
# Copyright (c) 2013, Stacey Ell
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###
from time import time
from datetime import timedelta
from functools import partial
from itertools import takewhile
from supybot.commands import (
    additional,
    wrap
)
import supybot.utils as utils
import supybot.schedule as schedule
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Countdown')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

def decowrap(*args, **kwargs):
    def decorator(func):
        return wrap(func, *args, **kwargs)
    return decorator

def fib():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

def modfib():
    fibiter = fib()
    yield next(fibiter)
    next(fibiter)  # skip first `1'
    while True:
        yield next(fibiter)

def countdown_alarm_points(seconds):
    rounder = lambda x: x - (x % 30 if x > 120 else 0)
    alarms = list(map(rounder, takewhile(lambda x: x < seconds, modfib())))
    alarms.append(seconds)
    return alarms

pluralization_table = {
    'week': (_('week'), _('weeks')),
    'day': (_('day'), _('days')),
    'hour': (_('hour'), _('hours')),
    'minute': (_('minute'), _('minutes')),
    'second': (_('second'), _('seconds')),
}

def format_unit(val, unit):
    if unit in pluralization_table:
        idx = 0 if val == 1 else 1
        unit = pluralization_table[unit][idx]
    return '{} {}'.format(val, unit)

def format_timedelta(delta, show_weeks=True, atom_joiner=None):
    if atom_joiner is None:
        atom_joiner = utils.str.commaAndify
    days, seconds = delta.days, delta.seconds
    atoms = []
    if show_weeks and days // 7:
        atoms.append(format_unit(days // 7, 'week'))
        days = days % 7
    if days:
        atoms.append(format_unit(days, 'day'))
    if seconds // 3600:
        atoms.append(format_unit(seconds // 3600, 'hour'))
        seconds = seconds % 3600
    if seconds // 60:
        atoms.append(format_unit(seconds // 60, 'minute'))
        seconds = seconds % 60
    if seconds:
        atoms.append(format_unit(seconds, 'second'))
    if not atoms:
        raise ValueError('Time difference not great enough to be noted.')
    return atom_joiner(atoms)

class Countdown(callbacks.Plugin):
    def __init__(self, irc, *args, **kwargs):
        self.__parent = super(Countdown, self)
        self.__parent.__init__(irc, *args, **kwargs)
        self._resolved = {}

    def _countdown_resp(self, irc, remaining_seconds, end_response):
        if remaining_seconds > 0:
            delta = timedelta(seconds=remaining_seconds)
            irc.reply(format_timedelta(delta), prefixNick=False)
        else:
            irc.reply(end_response, prefixNick=False)

    @decowrap(['positiveInt', additional('text')])
    def countdown(self, irc, msg, args, seconds, final_message=None):
        """<seconds> [final_message]

        Counts down
        """
        if final_message is None:
            final_message = 'GO!'
        now = time()
        callback_part = partial(self._countdown_resp, irc)
        trigger_resolve_at = now + seconds - min(seconds, 3)
        schedule.addEvent(self._populate_resolved, trigger_resolve_at)
        for alarm_point in countdown_alarm_points(seconds):
            schedule.addEvent(
                partial(callback_part, alarm_point, final_message),
                now + seconds - alarm_point)

Class = Countdown

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
