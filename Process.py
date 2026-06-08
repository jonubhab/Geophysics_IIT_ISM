import os
import pickle
import socket
import subprocess
import sys
import threading
import time as T
import urllib.request
from datetime import *

import msnoise.api as ms
import msnoise.msnoise_table_def as config

if len(sys.argv) > 1:
    dir = sys.argv[1]
    if not os.path.isabs(dir):
        dir = os.path.abspath(dir)
    print(f"Root directory: {dir}")
else:
    dir = input("Enter the path of root directory: ").strip()
    if not dir.startswith("/"): dir = "/" + dir

if not os.path.exists(dir):
    raise ValueError(f"Directory does not exist: {dir}")

org=os.getcwd()
ctrl=os.path.join(dir, "Control")
os.makedirs(ctrl, exist_ok=True)
os.chdir(ctrl)

msn="msnoise"

new=not os.path.exists("db.ini")
base=new and os.path.exists("msnoise.sqlite")

if not (new or os.path.exists("msnoise.sqlite")) and pickle.load(open("db.ini", "rb"))[0] == 1:
    os.remove("db.ini")
    new=True



def info(n):
    global net
    try:
        return open("info","r").readlines()[n].split(':')[1].strip()
    except:
        print("info file might have been corrupted.")
        if n==2:
            net=None
            if not any(fol=="NET" for fol in struc.split("/")):
                net=input("Network can't be detected from data structure.\nEnter network name: ")
        with open("info", "w") as f:
            f.write(f"Root Directory : {dir}\n")
            f.write(f"Data Structure : {struc}\n")
            f.write(f"Network : {net if net else 'dynamic'}\n")
            f.write(f"data available : {db.query(config.DataAvailability).count() > 0}\n")
            f.write(f"jobs initialized : {db.query(config.Job).count() > 0}\n")
            if n == 5:
                f.write(f"Last Scan : \n")
                return ""
            else: f.write(f"Last Scan : {info(5)}\n")
        return open("info","r").readlines()[n].split(':')[1].strip()

def update(n,inf):
    with open("info", "w") as f:
        f.write(f"Root Directory : {info(0) if n!=0 else inf}\n")
        f.write(f"Data Structure : {info(1) if n!=1 else inf}\n")
        f.write(f"Network : {info(2) if n!=2 else inf}\n")
        f.write(f"data available : {info(3) if n!=3 else inf}\n")
        f.write(f"jobs initialized : {info(4) if n!=4 else inf}\n")
        f.write(f"Last Scan : {info(5) if n!=5 else inf}\n")


def run(cmd, critical=True):
    result = subprocess.run(cmd)
    if result.returncode != 0:
        if critical:
            print(f"Critical step failed: {' '.join(cmd)}")
            sys.exit(1)
        else:
            print(f"Warning: {' '.join(cmd)} failed, continuing...")

if new:
    run([msn, "db", "init"], critical=True)
    db=ms.connect()

    ms.update_config(db,"data_folder",dir)

    ms.update_filter(db, ref=1, low=0.05, mwcs_low=0.05, high=5.0, mwcs_high=5.0,
                     rms_threshold=0.0, mwcs_wlen=25.0, mwcs_step=5.0, used=True)

    print("Select Data Structure:")
    i = 1
    with open(os.path.join(org,"Structures"), "r") as f:
        for l in f.readlines():
            print(f"[{i}] {l.strip()}")
            i += 1
    print(f"[{i}] Create New Data Structure")
    choice = int(input("Your Choice: "))

    net, cus = None, choice > 4
    if not (0 < choice <= i):
        raise ValueError("Invalid choice")
    elif choice != i:
        tmp=open(os.path.join(org,"Structures"), "r").readlines()[choice - 1].split('\"')
        struc = tmp[1]
        if len(tmp) > 3: net=tmp[3]
    else:
        name = input("Name of Data Structure: ")
        struc = input("Data Structure (Path from root directory): ").strip()
        if not any(fol=="NET" for fol in struc.split("/")):
            net=input("Network can't be detected from data structure.\nEnter network name: ")
            with open(os.path.join(org,"Structures"), "a") as f:
                f.write(f"\n{name} : \"{struc}\"\t[NETWORK: \"{net}\"]\n")
        else:
            with open(os.path.join(org,"Structures"), "a") as f:
                f.write(f"\n{name} : \"{struc}\"\n")

    with open("info","w") as f:
        f.write(f"Root Directory : {dir}\n")
        f.write(f"Data Structure : {struc}\n")
        f.write(f"Network : {net if net else 'dynamic'}\n")
        f.write(f"data available : {info(3) if base else False}\n")
        f.write(f"jobs initialized : {info(4) if base else False}\n")
        f.write(f"Last Scan : {info(5) if base else ''}\n")

    ms.update_config(db, "data_structure", struc)





    db.commit()
else:
    db = ms.connect()
    struc=ms.get_config(db, "data_structure")
    cus= not (any(struc==pre for pre in ["SDS","BUD","IDDS","PDF"]))
    net=info(2)
    if net == 'dynamic': net = None



q,n='"',"\n"
custom=f"""
import os, glob
from functools import reduce

coords={{}}
with open(os.path.join({q+dir+q},"gmap-stations.txt"), "r") as f:        
    for line in f:
        l = line.strip().split('|')
        if not line or line.startswith("#") or len(line.strip())==0:
            continue
        l[2:5]=list(map(float,l[2:5]))
        coords[l[0]+"_"+l[1]]=[l[3],l[2],l[4]]
        
struc={f"{q}{struc}{q}"} 
struc=struc.split('/')
i_sta,i_net=0,0
for i in range(1,len(struc)):
    if struc[-i-1]=="STA": i_sta=i
    if struc[-i-1]=="NET": i_net=i

if i_net==0: net = "{net}"
if i_sta==0: raise ValueError("Stations cannot be detected from Data Structure.")

seek=lambda x,n:reduce(lambda di, _: os.path.split(di)[0], range(n), x)
st=lambda x: os.path.split(seek(x,i_sta-1))[1]
nt=lambda x: os.path.split(seek(x,i_net-1))[1]

def has_mseed(directory):
    for root, dirs, files in os.walk(directory):
        if any(f.endswith('.MSEED') or f.endswith('.mseed') for f in files):
            return True
    return False

def populate(data_folder):  
    global net
    datalist = sorted(glob.glob(os.path.join(data_folder, {f"{q}*{q},"*struc.count('/')}))) 
    stationdict = {{}}
    
    for di in datalist:
        if os.path.commonpath([di, "{ctrl}"]) != "{ctrl}" and os.path.isdir(di) and has_mseed(di) and  "All" not in di:                 
            sta = st(di)
            if i_net!=0: net = nt(di)
            stationdict[net+"_"+sta]=[net,sta,*coords[net+"_"+sta],'DEG','N/A'] #Adding station details in a dictionary
    return stationdict
"""

if cus:
    with open(os.path.join(ctrl,"custom.py"),"w") as cus: cus.write(custom)

run([msn, "populate"])

if db.query(config.Station).count() == 0:
    raise RuntimeError("Critical: populate failed - no stations added.")

def mseed(dir):
    if not os.path.isdir(dir): return any(dir.endswith(ext) for ext in [".MSEED",".mseed"])
    for root, dirs, files in os.walk(dir):
        if any(f.endswith('.MSEED') or f.endswith('.mseed') for f in files):
            return True
    return False


lastscan=datetime.strptime(info(5), '%Y-%m-%d %H:%M:%S') if len(info(5))>0 else None
if lastscan: ms.update_config(db, "crondays", str(max(1, (datetime.now() - lastscan).days)))

exclude = {'All', 'Control'}
dirs = [d for d in os.listdir(dir) if mseed(os.path.join(dir, d)) and d not in exclude]
if new or info(3) == 'False':
    cmd = [msn, "scan_archive","--init","--recursively", "--path",dir]
    update(3, "True")
else: cmd = [msn, "scan_archive","--recursively", "--path",dir]
for d in dirs:
    cmd[-1]=os.path.join(dir,d)
    run(cmd)

update(5,datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

if new or info(4):
    run([msn, "new_jobs", "--init"], critical=False)
    update(4,"True")
else: run([msn, "new_jobs"], critical=False)

if new:
    run([msn, "config", "set", "plugins=msnoise_tomo"])
    run([msn, "p", "tomo", "install"])



last = db.query(config.DataAvailability).order_by(config.DataAvailability.endtime.desc()).first()
if last:
    end = (last.endtime + timedelta(days=1)).strftime("%Y-%m-%d")
    ms.update_config(db, "enddate", end)
    db.commit()

db.close()


port=5000
def run_admin():
    global port
    def is_port_free(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0
    while not is_port_free(port):
        port += 1
    print(f"Web Admin hosted on http://localhost:{port}")
    '''
    from msnoise.msnoise_admin import app
    app.run(host="localhost", port=port)
    '''
    run([msn,"admin","-p",str(port)])

def wait_for_server(port, timeout=30):
    start = T.time()
    while T.time() - start < timeout:
        try:
            urllib.request.urlopen(f"http://localhost:{port}")
            return True
        except:
            T.sleep(0.5)
    return False


try:
    t = threading.Thread(target=run_admin, daemon=True)
    t.start()
    if wait_for_server(port,5):
        subprocess.Popen(["firefox", f"http://localhost:{port}"])
    subprocess.Popen(
        ["gnome-terminal", "--working-directory", ctrl, "--", "bash", "-i", "-c", "conda activate msnoise; exec bash"])
    t.join()
except KeyboardInterrupt:
    print("\nWeb Admin engine stopped.")


