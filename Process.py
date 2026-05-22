import os, subprocess,threading,socket,sys,time
import msnoise.api as ms
import urllib.request

if len(sys.argv) > 1:
    dir = sys.argv[1]
    if not os.path.isabs(dir):
        dir = os.path.abspath(dir)
    print(f"Root directory: {dir}")
else:
    dir = input("Enter the path of root directory: ").strip()
    if not dir.startswith("/"): dir = "/" + dir
    if not os.path.isabs(dir):
        raise ValueError(f"Please enter an absolute path (starting with /). Got: {dir}")
    if not os.path.exists(dir):
        raise ValueError(f"Directory does not exist: {dir}")


print("Select Data Structure:")
i=1
with open("Structures","r") as f:
    for l in f.readlines():
        print(f"[{i}] {l.strip()}")
        i+=1
print(f"[{i}] Create New Data Structure")
struc=int(input("Your Choice: "))

wt,cus=False,struc>4
if not(0<struc<=i):
    raise ValueError("Invalid choice")
elif struc!=i:
    if struc==5: wt=True
    struc=open("Structures","r").readlines()[struc-1].split('\"')[1]
else:
    name=input("Name of Data Structure: ")
    struc=input("Data Structure (Path from root directory): ").strip()
    with open("Structures","a") as f:
        f.write(f"\n{name} : \"{struc}\"")


ctrl=os.path.join(dir, "Control")

os.makedirs(ctrl, exist_ok=True)
os.chdir(ctrl)

msn="msnoise"

subprocess.run([msn, "db", "init", "--tech", "1"], check=True)
db=ms.connect()         #$ ms db init

ms.update_config(db,"data_folder",dir)
ms.update_config(db,"data_structure",struc)
ms.update_filter(db, ref=1, low=0.05, mwcs_low=0.05, high=5.0, mwcs_high=5.0,
                 rms_threshold=0.0, mwcs_wlen=25.0, mwcs_step=5.0, used=True)
db.commit()
db.close()


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

if i_net==0: net = {f"{q}Y2{q}" if wt else f"input({q}Network can't be detected from data structure.{n}Enter network name: {q})"}
if i_sta==0: raise ValueError("Stations cannot be detected from Data Structure.")

seek=lambda x,n:reduce(lambda di, _: os.path.split(di)[0], range(n), x)
st=lambda x: os.path.split(seek(x,i_sta-1))[1]
nt=lambda x: os.path.split(seek(x,i_net-1))[1]

def populate(data_folder):  
    global net
    datalist = sorted(glob.glob(os.path.join(data_folder, {f"{q}*{q},"*struc.count('/')}))) 
    stationdict = {{}}
    
    for di in datalist:
        if os.path.commonpath([di, "{ctrl}"]) != "{ctrl}" and not any(ext in di for ext in [".txt",".py",".ini",".sqlite",".pyc"]):                 
            sta = st(di)
            if i_net!=0: net = nt(di)
            stationdict[net+"_"+sta]=[net,sta,*coords[net+"_"+sta],'UTM','N/A'] #Adding station details in a dictionary
    return stationdict
"""

if cus:
    with open(os.path.join(ctrl,"custom.py"),"w") as cus: cus.write(custom)


subprocess.run([msn, "populate"], check=True)
subprocess.run([msn, "scan_archive", "--path", dir, "--init", "--recursively"], check=True)
subprocess.run([msn, "new_jobs", "--init"], check=True)


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
    subprocess.run([msn,"admin"],check=True)

def wait_for_server(port, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"http://localhost:{port}")
            return True
        except:
            time.sleep(0.5)
    return False


try:
    t = threading.Thread(target=run_admin, daemon=True)
    t.start()
    if wait_for_server(port,5):
        subprocess.Popen(["firefox", f"http://localhost:{port}"])
    subprocess.Popen(["gnome-terminal", "--working-directory", ctrl, "--", "bash", "-c",
                      "source ~/anaconda3/etc/profile.d/conda.sh && conda activate msnoise_new; exec bash"])
    t.join()
except KeyboardInterrupt:
    print("\nWeb Admin engine stopped.")


