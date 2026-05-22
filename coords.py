import msnoise.api as ms

txt_file_path = "../station_info.txt"   #Script saved in same folder as station info

db = ms.connect()

print("Starting coordinate update from text file...")

with open(txt_file_path, "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        try:
            sta_code, lon, lat, alt = line.split(" ")
            ms_sta = ms.get_station(db, 'Y2', sta_code)  #Finds station in db
            
            if ms_sta:
                ms_sta.X = float(lon)
                ms_sta.Y = float(lat)
                ms_sta.altitude = float(alt)*1000
                print(f" updated {sta_code} -> Lon: {lon}, Lat: {lat}, Alt: {alt}")
            else:
                print(f" Station {sta_code} not found in database.")
                
        except ValueError:
            print(f" Error parsing line: '{line}'.")

db.commit()     #Save Changes
db.close()
print("Coordinate update complete!")
