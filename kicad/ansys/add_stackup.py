# orginal this comes from https://gitlab.com/kicad/code/kicad/-/issues/16665

import xmltodict
import time

def append_id(filename):
    return "{0}_{2}.{1}".format(*filename.rsplit('.', 1) + ["_Stackup"])

######################## USER INPUT ############################

# dimension in mm

thick_silkscreen = 0.0152
thick_paste = 0.0001
thick_mask = 0.0152

# 4 layers
thick_copper = [0.035, 0.035]
thick_cores = [1.51]

input_file = 'TDR1.xml'

################################################################

overall_thickness = 2 * thick_mask + 2 * thick_silkscreen + 2 * thick_paste

for i in thick_copper:
    overall_thickness += i

for i in thick_cores:
    overall_thickness += i


print("Overall thickness : "+str(overall_thickness) + " mm")



data = ''
with open(input_file, 'r') as file:
    data = file.read()




xmldata = xmltodict.parse(data)

layers = []



cadheader = xmldata["IPC-2581"]["Ecad"]["CadHeader"]
cadheader["Spec"] = []

caddata = xmldata["IPC-2581"]["Ecad"]["CadData"]
step = caddata["Step"]
del caddata["Step"]
caddata["Stackup"] = {"@name": "PRIMARY", "@overallThickness": str(overall_thickness), "@tolPlus": "0.0", "@tolMinus": "0.0", "@whereMeasured":"MASK", "StackupGroup": {"@name":"GROUP_PRIMARY","@thickness":str(overall_thickness), "@tolPlus": "0.0", "@tolMinus": "0.0", "StackupLayer":[]}}
caddata["Step"] = step
cuit = 0
coit = 0

lcount = 1

for l in xmldata["IPC-2581"]["Content"]["LayerRef"]:
    name = l["@name"]

    material = "COPPER"
    layer_type = "CONDUCTOR"
    dielec = "3.6100"
    losstang = "0.0200"
    conductivity = "0"
    thickness = 0


    if ".Silkscreen" in name:
        material = "SILKSCREEN"
        layer_type = "SILKSCREEN"
        dielec = "3.3000"
        losstang = "0.0220"
        thickness = thick_silkscreen

    elif ".Paste" in name:
        material = "SOLDERPASTE"
        layer_type = "PASTEMASK"
        dielec = "3.3000"
        losstang = "0.0220"
        thickness = thick_paste

    elif ".Mask" in name:
        material = "SOLDERMASK"
        layer_type = "MASK"
        dielec = "3.3000"
        losstang = "0.0220"
        thickness = thick_mask

    elif "DIELECTRIC" in name:
        material = "FR4"
        layer_type = "DIELECTRIC"
        dielec = "4.5"
        losstang = "0.02"
        thickness = thick_cores[coit]
#         coit += 1

    elif ".Cu" in name:
        conductivity="595900.0000"
        thickness = thick_copper[cuit]
        cuit += 1


    entry = {"@name" : "SPEC_LAYER_" + name, "General":[], "Conductor":{}, "Dielectric":[]}
    entry["General"].append({"@type":"MATERIAL", "Property": {"@text": material}})
    entry["General"].append({"@type":"OTHER", "@comment":"LAYER_TYPE", "Property": {"@text": layer_type}})
    entry["Conductor"].update({"@type":"CONDUCTIVITY", "Property": {"@unit": "MHO/CM", "@value": conductivity}})
    entry["Dielectric"].append({"@type":"DIELECTRIC_CONSTANT", "Property": {"@value": dielec}})
    entry["Dielectric"].append({"@type":"LOSS_TANGENT", "Property": {"@value": losstang}})
    
    if ".Cu" in name:
        entry["General"].append({"@type":"OTHER", "@comment":"LAYER_EMBEDDED_STATUS", "Property": {"@text": "NOT_EMBEDDED"}})
    cadheader["Spec"].append(entry)

    stack = {"@layerOrGroupRef":name, "@thickness": str(thickness), "@tolPlus": "0.0", "@tolMinus": "0.0", "@sequence":str(lcount), "SpecRef":{"@id":"SPEC_LAYER_"+name}}
    caddata["Stackup"]["StackupGroup"]["StackupLayer"].append(stack)
    lcount += 1
    
def finde_alle_schlüssel(d, name):
    schlüssel = []
    for k, v in d.items():
        if k == name:
            schlüssel.append(d)
        if isinstance(v, dict):
            schlüssel.extend(finde_alle_schlüssel(v, name))
        elif isinstance(v, list):
            for i in v:
                if isinstance(i, dict):
                    schlüssel.extend(finde_alle_schlüssel(i, name))
    return schlüssel

#print(caddata["Step"].keys())

pads = finde_alle_schlüssel(caddata["Step"], "PinRef")

for i in pads:
    foundXform = False
    for j in i:
        if j == "Xform":
            foundXform = True
    if not foundXform:
        keylist = []
        for k,v in i.items():
            keylist.append([k,v])
        for k in keylist:
            i.pop(k[0])
        xform = {"@rotation":"0.0"}
        i.update({"Xform":xform})
        for k in keylist:
            i.update({k[0]:k[1]})


#finde_subdicts(caddata["Step"], "Pad")


with open(append_id(input_file),'w') as f:
    f.write(xmltodict.unparse(xmldata,pretty=True))
    f.close()

filedata = ""
filedata2 = []

# remove not recognized component name "CMP_R24" to R24
with open(append_id(input_file), 'r') as file:
    filedata = file.readlines()
    for i in filedata:
        filedata2.append(i.replace("VIA", "PLATED").replace("CMP_",""))
print(filedata)


with open(append_id(input_file), 'w') as file:
  for i in filedata2:
    file.write(i)