#!/usr/bin/python
"""
Display in a curse windows irq/s rate


Author : Sebastien Wacquiez <sw@enix.org>
"""
import os
import re
import time
import curses
import select
import sys
import errno

DELAY=200
intrfile="/proc/interrupts"


def diffpersecond(newvalues, oldvalues, elapsed):
    assert len(newvalues) == len(oldvalues), "new and old values should be list of the same lenght"
    return map(lambda a: "%s"%int((int(a[0]) - int(a[1]))/elapsed), zip(newvalues, oldvalues))

class IrqStats(object):
    def __init__(self, filename):
        self.filename = filename
        self.stats = {}
        self.last = {}
        self.lastrun = 0
        tmp = file(self.filename).read().split("\n")[0]
        tmp = re.sub(" +", " ", tmp)
        self.cpucount = len(tmp.strip().split())
        self.scroll = 0
        self.hscroll = 0
    
    def gather(self):        
        data = file(self.filename).read()
        tt = time.time()
        data = re.sub(" +", " ", data)
        data = data.strip().split("\n")
        head = data[0].strip()
        cpucount = len(head.split())
        if self.cpucount != cpucount:
            print "Warning : CPU Count have changed"
            self.cpucount = cpucount
        result = {}
        for line in data[1:]:
            line = line.split()
            intr = line[0].strip().strip(":")
            result[intr] = {
                "intr": intr,
                "raw": line[1:cpucount+1],
                "desc" : " ".join(line[cpucount+1:]),
                }
        if self.lastrun:
            elapsed = tt - self.lastrun
            for k, v in self.last.items():
                self.stats[k] = v.copy()
                # Now we iter over the stats counter in both old and new data and compute a int/seconds
                self.stats[k]["rate"] = diffpersecond(result[k]["raw"], v["raw"], elapsed)
        self.lastrun = tt
        self.last = result
    def print_stats(self):
        if not self.stats:
            return
        print "\x1b[2J\x1b[H"
        print "\t", "\t".join([ "CPU%s"%i for i in range(self.cpucount) ])
        for k in sorted(self.stats.keys()):
            v = self.stats[k]
            print "%s\t"%k, "\t".join(v["rate"]), "\t",v["desc"]

    def curses_keypress(self, key):
        if key == curses.KEY_UP:
            self.scroll = max(0, self.scroll - 1)
        elif key == curses.KEY_DOWN:
            self.scroll = max(0, self.scroll + 1)
        elif key == curses.KEY_LEFT:
            self.hscroll = max(0, self.hscroll + 1)
        elif key == curses.KEY_RIGHT:
            self.hscroll = max(0, self.hscroll - 1)
           

    def curses_stats(self, win):
        if not self.stats:
            return
        win.erase()
        height, width = win.getmaxyx()
        start = 0 + self.scroll
        stop = start + height - 1
        hstart = 0 + self.hscroll
        hstop = hstart + width - 2
        win.addstr(0,0, ("     " + "".join([ "% 7s"%("CPU%s"%i) for i in range(self.cpucount) ]))[hstart:hstop], curses.A_REVERSE)
        i = 1
        for k in sorted(self.stats.keys())[start:stop]:
            v = self.stats[k]
            win.addstr(i, 1, ("% 4s"%k +  "".join([ "% 7s"%r for r in v["rate"]]) + "  " + v["desc"])[hstart:hstop])
            i += 1
        win.refresh()


              
def run_irqtop(win):
    irq = IrqStats(intrfile)
    curses.curs_set(0)
    curses.noecho()
    win.keypad(1)
    win.nodelay(1)
    poll = select.poll()
    poll.register(sys.stdin.fileno(), select.POLLIN|select.POLLPRI)
    while True:
        irq.gather()
        try:
            events = poll.poll(DELAY)
        except select.error as e:
            if e.args and e.args[0] == errno.EINTR:
                events = []
            else:
                raise
        for (fd, event) in events:
            if event & (select.POLLERR | select.POLLHUP):
                sys.exit(1)
            if fd == sys.stdin.fileno():
                try:
                    key = win.getch()
                    irq.curses_keypress(key)
                except curses.ERR:
                    pass
        irq.curses_stats(win)

    

curses.wrapper(run_irqtop)
