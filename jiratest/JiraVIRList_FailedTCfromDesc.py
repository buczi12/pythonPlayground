from jira import JIRA
import msvcrt
from tkinter import filedialog
from tkinter import *
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import Counter

def getPwd():
    passwd = ""
    print("Password: ", end='', flush=True)
    while True:
        x = msvcrt.getwch()
        if x == '\r':
            break
        print('*', end='', flush=True)
        passwd += str(x)

    return passwd

def getTRpath():
    Tk().withdraw()
    #path = filedialog.askopenfilename(title="Select .xml SysTR file")
    pathList = list(filedialog.askopenfilenames(title="Select .xml SysTR file"))

    return pathList

def findFailedTCs(paths):
    fTClist = []

    for tr in paths:
        tree = ET.parse(tr)
        root = tree.getroot()

        for tc in root.iter("testcase"):
            if (tc.find("verdict[@result='fail']")) != None:
                fTClist.append(tc.find("ident").text)

    print("\nFailed TCs list: \n")
    print(*fTClist, sep='\n')
    print("\nNumber of failed TCs: %d \n" % len(fTClist))

    return fTClist

def findFailedTCs__(path):
    tree = ET.parse(path)
    root = tree.getroot()
    fTClist = []

    for tc in root.iter("testcase"):
        if (tc.find("verdict[@result='fail']")) != None:
            fTClist.append(tc.find("ident").text)

    print("\nFailed TCs list: \n")
    print(*fTClist, sep='\n')
    print("\nNumber of failed TCs: %d \n" % len(fTClist))

    return fTClist

def getBugData(failedtclist, jira):

    bugList = []
    bugdata = []
    bugdict = {}



    for tc in failedtclist:

        #str = 'type=Problem and ' + '"Test Procedure ID" ~ ' + tc   #Bug/Problem   /// (~ contains)
        str = 'type=Problem and (' + '"Description" ~ ' + tc + ' or "Test Procedure ID" ~ ' + tc + ')'  # Bug/Problem   /// (~ contains)

        bugs = jira.search_issues(str)

        if bugs == []:
            print("There is no Jira BUG for failed test case: ",tc)

        for bug in bugs:
            if bug not in bugList:
                bugList.append(bug)
                bugdict[bug.key] = [tc]
            else:
                bugdict[bug.key].append(tc)

    #print(bugdict)

    print("\n")

    for bug in bugList:
        #for field_name in bug.raw['fields']:  #print all fields
        #   print("Field:", field_name, "Value:", bug.raw['fields'][field_name])

        if bug.fields.versions:
            version = bug.raw['fields']['versions'][0]['name']
        else:
            version = "None"
            print("Missing parameter in bug - Affected version! Bug:", bug)

        #if bug.fields.customfield_10147:  # severity - customfield_10147, Risk Value - customfield_11018
        #    severity = bug.raw['fields']['customfield_10147']['value']

        if bug.fields.customfield_11018:  # severity - customfield_10147, Risk Value - customfield_11018
            severity = bug.raw['fields']['customfield_11018']['value']
        else:
            severity = "None"
            print("Missing parameter in bug - Severity! Bug:", bug)

        #bugdata.append([bug.key, bug.raw['fields']['status']['name'], version, severity, bug.fields.summary, bug.fields.customfield_10175]) # key / ststus / affected version / severity / summary / Test procedure ID
        bugdata.append([bug.key, bug.raw['fields']['status']['name'], version, severity, bug.fields.summary, bugdict[bug.key]]) # key / ststus / affected version / severity / summary / Test procedure ID


    print(*bugdata, sep='\n')
    return bugdata

def createVIRlist(bugdata):
    root = ET.Element("header_xml")

    for bug in bugdata:
        vir = ET.SubElement(root, "VIR_OPEN")

        for tc in bug[5]:
            ET.SubElement(vir, "TCID", attrib={'id': tc})


        virinfo = ET.SubElement(vir, "VIRInfo", attrib={'nr': bug[0], 'status': bug[1], 'submit_sw_ver': bug[2], 'close_sw_ver': "", 'severity': bug[3], 'closed_by': "", 'close_date': ""})
        virinfo.text = bug[4]

    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml()
    with open("VIR_list.xml", "w") as f:
        f.write(xmlstr)
    
    virlistName = "VIR_list_" + myselfData['emailAddress'][0].upper() + myselfData['emailAddress'].split(".")[1][:2].upper() + ".xml"
    with open("VIR_list.xml", "w") as f:
        f.write(xmlstr)
    with open(virlistName, "w") as f:
        f.write(xmlstr)



if len(sys.argv) > 2:
    netID = str(sys.argv[1])
    passwd = str(sys.argv[2])
else:
    print('\nYou need to pass netID and password to login to JIRA.\n')
    netID = input("NetID: ")
    passwd = getPwd()

sysTRpathList = getTRpath()
failedTClist = findFailedTCs(sysTRpathList)

if failedTClist == []:
    print("No failed TCs\n")
else:
    jira = JIRA(basic_auth=(netID, passwd), options={'server': 'http://jiraprod1.delphiauto.net:8080'})
    myselfData = jira.myself()
    bugData = getBugData(failedTClist, jira)
    createVIRlist(bugData)

input("\nDone! Press enter to finish.")
