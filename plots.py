from msnoise.api import *
import subprocess
import shutil
import os

def run(cmd, critical=True):
    result = subprocess.run(cmd.split())
    if result.returncode != 0:
        return False
    return True

_original_get_station_pairs=get_station_pairs

def patched_get_station_pairs(*args, **kwargs):
    station_pairs = _original_get_station_pairs(*args, **kwargs)
    for sta1, sta2 in station_pairs:
        # Check both directions (A, B) and (B, A) just in case
        if sta1 != sta2:
            yield sta1, sta2

get_station_pairs = patched_get_station_pairs

db=connect()
filters = get_filters(db)
params = get_params(db)
comps = params.components_to_compute
mov=list(map(int,params.mov_stack.split(',')))
_, _, datelist = build_movstack_datelist(db)
datelist=list(map(lambda d:d.isoformat(),datelist))
failed,funcfail=[],[]


#distance
print("\ndistance")
for filter in filters:
    for comp in comps:
        save = os.path.join("MSnoise_plots", "distance", "%02i" % filter.ref, comp+ ".png")
        if not os.path.exists(save):
            os.makedirs(os.path.dirname(save), exist_ok=True)
            print(save)
            if run(f"msnoise plot distance -f {filter.ref} -c {comp} -o ? -s FALSE"):
                try:
                    shutil.move('distance %s-f%i.png' % (comp, filter.ref), save)
                    continue
                except FileNotFoundError:
                    pass
            print("failed ",save)
            failed.append(save)
            funcfail.append(save)
print("Plots Failed: ",len(funcfail))
for fail in funcfail:print(fail)
funcfail=[]


#dvv
print("\ndvv")
for filter in filters:
    for comp in comps:
        save = os.path.join("MSnoise_plots", "dvv", "%02i" % filter.ref, comp + ".png")
        if not os.path.exists(save):
            os.makedirs(os.path.dirname(save), exist_ok=True)
            print(save)
            if run(f"msnoise plot dvv -f {filter.ref} -c {comp} -o ? -s FALSE"):
                try:
                    shutil.move('dvv [\'%s\']-f%i-MM.png' % (comp, filter.ref), save)
                    continue
                except FileNotFoundError:
                    pass
            print("failed ", save)
            failed.append(save)
            funcfail.append(save)
print("Plots Failed: ",len(funcfail))
for fail in funcfail:print(fail)
funcfail=[]



#timing
print("\ntiming")
for filter in filters:
    for comp in comps:
        save = os.path.join("MSnoise_plots", "timing", "%02i" % filter.ref, comp + ".png")
        if not os.path.exists(save):
            os.makedirs(os.path.dirname(save), exist_ok=True)
            print(save)
            if run(f"msnoise plot timing -f {filter.ref} -c {comp} -o ? -s FALSE"):
                try:
                    shutil.move('timing %s-f%i-MA.png' % (comp, filter.ref), save)
                    continue
                except FileNotFoundError:
                    pass
            print("failed ", save)
            failed.append(save)
            funcfail.append(save)
print("Plots Failed: ",len(funcfail))
for fail in funcfail:print(fail)
funcfail=[]




#ccftime
print("\nccftime")
for filter in filters:
    for m in mov:
        for comp in comps:
            station_pairs = get_station_pairs(db)
            for sta1,sta2 in station_pairs:
                pair="%s_%s-%s_%s"%(sta1.net,sta1.sta,sta2.net,sta2.sta)
                save=os.path.join("MSnoise_plots","ccftime","%02i"%filter.ref,"%03i_DAYS"%m,comp,pair+".png")
                if not os.path.exists(save):
                    os.makedirs(os.path.dirname(save),exist_ok=True)
                    print(save)
                    if run(f"msnoise plot ccftime {sta1.net}.{sta1.sta} {sta2.net}.{sta2.sta} -f {filter.ref} -c {comp} -m {m} -o ? -s FALSE"):
                        try:
                            shutil.move('ccftime %s-%s-f%i-m%i.png' % (pair, comp, filter.ref, m), save)
                            continue
                        except FileNotFoundError:
                            pass
                    print("failed ",save)
                    failed.append(save)
                    funcfail.append(save)
print("Plots Failed: ",len(funcfail))
for fail in funcfail:print(fail)
funcfail=[]
'''

'''
#interferogram
print("\ninterferogram")
for filter in filters:
    for m in mov:
        for comp in comps:
            station_pairs = get_station_pairs(db)
            for sta1,sta2 in station_pairs:
                pair="%s_%s-%s_%s"%(sta1.net,sta1.sta,sta2.net,sta2.sta)
                save=os.path.join("MSnoise_plots","interferogram","%02i"%filter.ref,"%03i_DAYS"%m,comp,pair+".png")
                if not os.path.exists(save):
                    os.makedirs(os.path.dirname(save),exist_ok=True)
                    print(save)
                    if run(f"msnoise plot interferogram {sta1.net}.{sta1.sta} {sta2.net}.{sta2.sta} -f {filter.ref} -c {comp} -m {m} -o ? -s FALSE"):
                        try:
                            shutil.move('interferogram %s-%s-f%i-m%i.png' % (pair, comp, filter.ref, m), save)
                            continue
                        except FileNotFoundError:
                            pass
                    print("failed ", save)
                    failed.append(save)
                    funcfail.append(save)
print("Plots Failed: ",len(funcfail))
for fail in funcfail:print(fail)
funcfail=[]


#mwcs
print("\nmwcs")
for filter in filters:
    for m in mov:
        for comp in comps:
            station_pairs = get_station_pairs(db)
            for sta1,sta2 in station_pairs:
                pair="%s_%s-%s_%s"%(sta1.net,sta1.sta,sta2.net,sta2.sta)
                save=os.path.join("MSnoise_plots","mwcs","%02i"%filter.ref,"%03i_DAYS"%m,comp,pair+".png")
                if not os.path.exists(save):
                    os.makedirs(os.path.dirname(save),exist_ok=True)
                    print(save)
                    if run(f"msnoise plot mwcs {sta1.net}.{sta1.sta} {sta2.net}.{sta2.sta} -f {filter.ref} -c {comp} -m {m} -o ? -s FALSE"):
                        try:
                            shutil.move('mwcs %s-%s-f%i-m%i.png' % (pair.replace('-','_'), comp, filter.ref, m), save)
                            continue
                        except FileNotFoundError:
                            pass
                    print("failed ", save)
                    failed.append(save)
                    funcfail.append(save)
print("Plots Failed: ",len(funcfail))
for fail in funcfail:print(fail)
funcfail=[]


#spectime
print("\nspectime")
for filter in filters:
    for m in mov:
        for comp in comps:
            station_pairs = get_station_pairs(db)
            for sta1,sta2 in station_pairs:
                pair="%s_%s-%s_%s"%(sta1.net,sta1.sta,sta2.net,sta2.sta)
                save=os.path.join("MSnoise_plots","spectime","%02i"%filter.ref,"%03i_DAYS"%m,comp,pair+".png")
                if not os.path.exists(save):
                    os.makedirs(os.path.dirname(save),exist_ok=True)
                    print(save)
                    if run(f"msnoise plot spectime {sta1.net}.{sta1.sta} {sta2.net}.{sta2.sta} -f {filter.ref} -c {comp} -m {m} -o ? -s FALSE"):
                        try:
                            shutil.move('spectime%s-%s-f%i-m%i.png' % (pair, comp, filter.ref, m), save)
                            continue
                        except FileNotFoundError:
                            pass
                    print("failed ", save)
                    failed.append(save)
                    funcfail.append(save)
print("Plots Failed: ",len(funcfail))
for fail in funcfail:print(fail)
funcfail=[]





#dtt
print("\ndtt")
for filter in filters:
    for m in mov:
        for comp in comps:
            station_pairs = get_station_pairs(db)
            for sta1,sta2 in station_pairs:
                pair = "%s_%s-%s_%s" % (sta1.net, sta1.sta, sta2.net, sta2.sta)
                for date in datelist:
                    if os.path.isfile(os.path.join("MWCS","%02i"%filter.ref,"%03i_DAYS"%m,comp,pair.replace('-','_'),date+".txt")):
                        save=os.path.join("MSnoise_plots","dtt","%02i"%filter.ref,"%03i_DAYS"%m,comp,pair,date+".png")
                        if not os.path.isfile(save):
                            os.makedirs(os.path.dirname(save),exist_ok=True)
                            print(save)
                            if run(f"msnoise plot dtt {sta1.net}.{sta1.sta} {sta2.net}.{sta2.sta} {date} -f {filter.ref} -c {comp} -m {m} -o ? -s FALSE"):
                                try:
                                    shutil.move('dtt_%s-f%i-m%i-%s.png' % (pair,filter.ref,m,date),save)
                                    continue
                                except FileNotFoundError:
                                    pass
                            print("failed ",save)
                            failed.append(save)
                            funcfail.append(save)
print("Plots Failed: ",len(funcfail))
for fail in funcfail:print(fail)
funcfail=[]



print("\nTotal Failure: ",len(failed))
for fail in failed: print(fail)