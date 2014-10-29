#!/usr/bin/python

import os
import re
import time

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
      

irq = IrqStats(intrfile)
while True:
    irq.gather()
    irq.print_stats()
    time.sleep(0.2)
    
