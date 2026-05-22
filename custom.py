import os, glob

coords={}
with open("station_info.txt", "r") as f: #Extracts station coordinates from txt files
    for line in f:
        l = line.strip().split()
        if not line or line.startswith("#"):
            continue
        l[1:]=list(map(float,l[1:]))
        l[3]*=1000
        coords[l[0]]=l[1:] #Stores station coordinates in a dictionary

net = 'Y2' #Network

def populate(data_folder): #ms populate runs this function to get the Station Data
    datalist = sorted(glob.glob(os.path.join(data_folder, "*"))) #data structure according to our format of storing data (1 level deeper than the main directory)
    stationdict = {}
    for di in datalist:
        tmp = os.path.split(di)
        if tmp[1] != 'Control': #All folder names are station codes except Control
            sta = tmp[1]
            stationdict[net+"_"+sta]=[net,sta,*coords[sta],'UTM','N/A'] #Adding station details in a dictionary
    return stationdict