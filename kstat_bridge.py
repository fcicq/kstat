# kstat_bridge v0.1, by fcicq, under MIT License
# use with https://github.com/pyhedgehog/kstat

import kstat
import time
import os
import re

KSTAT = kstat.Kstat()
HZ = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
PAGESIZE = KSTAT['unix', 0,'seg_cache']['slab_size']

def solaris_mem(): # for zone, see memory_cap::: (rss, physcap, swap, swapcap)
  pages = KSTAT['unix',0, 'system_pages']
  arc = KSTAT['zfs', 0, 'arcstats']['size']
  return pages['pagestotal'] * PAGESIZE, pages['pageslocked'] * PAGESIZE, pages['pagesfree'] * PAGESIZE, arc

def solaris_cpucores():
  return KSTAT['unix',0,'system_misc']['ncpus']

def solaris_cpuinfo():
  cores = solaris_cpucores()
  res = []
  for i in xrange(cores): # Note: should check state in ['on-line', 'no-intr']
    c = KSTAT['cpu_info', i, 'cpu_info%d' % i]
    res.append(c)
  return res

def getcpunr(): # psrinfo -p
  chip = []
  for i in solaris_cpuinfo():
    if i['state'] in ['on-line', 'no-intr']:
      chip.append(i['chip_id'])
  return len(set(chip))

def solaris_cpu1():
  cores = solaris_cpucores()
  ret = []
  for i in xrange(cores):
    c = KSTAT['cpu_stat', i, 'cpu_stat%d' % i]
    t = c['idle'] + c['iowait'] + c['kernel'] + c['user']
    ret.append((c['idle'], c['iowait'], c['kernel'], c['user'], t, c['pgpgin'] * PAGESIZE, c['pgpgout'] * PAGESIZE, c['intr'], c['pswitch']))
  return ret

def rowsum(d):
  return tuple(map(sum, zip(*d)))

# how many online cpus? * HZ
def solaris_cpu():
  return rowsum(solaris_cpu1())

def solaris_vm_snapshot():
  return KSTAT['unix', 0, 'vminfo']

# Note: delta(swap_X) / delta(updates)
def solaris_vm(new, old):
  #unix:0:vminfo:swap_alloc 71486708419765
  #unix:0:vminfo:swap_avail 464964778301432
  #unix:0:vminfo:swap_free 466211614038050
  #unix:0:vminfo:swap_resv 72733544156383
  #unix:0:vminfo:updates 11978989
  raise NotImplemented

# only support sd? hopefully it works
def solaris_disk(disk):
  a = re.match('sd(\d+)$', disk) 
  try:
    diskid = int(a.groups()[0])
  except (IndexError, ValueError):
    return None
  try:
    k = KSTAT['sd', diskid, disk]
  except KeyError:
    return None
  return k['nread'], k['nwritten']

def solaris_net(interface):
  try:
    k = KSTAT['link', 0, interface]
  except KeyError:
    return None
  return k['ipackets64'], k['opackets64'], k['rbytes64'], k['obytes64']

def solaris_loadavg():
  k = KSTAT['unix', 0, 'system_misc']
  return '%.2f' % (k['avenrun_1min'] / 256.0), \
         '%.2f' % (k['avenrun_5min'] / 256.0), \
         '%.2f' % (k['avenrun_15min'] / 256.0)

def solaris_uptime(): # the commented code does not work as expected
  return 0 # time.time() - KSTAT['unix', 0, 'system_misc']['boot_time']

if __name__ == '__main__':
  print solaris_mem()
  print getcpunr()
  print solaris_cpu()
  print solaris_net('net0')
  print solaris_loadavg()
