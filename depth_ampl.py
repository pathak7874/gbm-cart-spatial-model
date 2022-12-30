"""
    APC using Tau Lidar camera
    Date: 22-06-21
    Author: GADC

"""
"""
    Design and Development Notes:
    8.3.2 Planning - see Project Proposal
    8.3.3 Inputs
        Standards none apply
        Codes of Practise - none apply
        Opportunity - to replace the VT based APc unit with a more accurate version
        Risks - no major risk if design fails
    8.3.4 Outputs
        New design for APC units
        Test plan
            Validate counting in a similar environment to a bus
            Check correct mqtt messages are received
            Check can connect with PC running setup software
                Check video transmission is acceptable
    8.3.5 Changes - follow Biodata versioning number system
"""

"""
Project Proposal + Functional Spec
A Tau Lidar camera will connect via usb to a RPi
The Rpi will run a python program to analyse the depth image and
identify passengers passing under the camera. Counts will be forwarded via
MQTT to a broker for saving data

Final application will written in python
"""
"""
ERRORS:
serial error codes:
    8001    Timeout connecting to camera
    8002    No ethernet (or wifi) connection for mqtt

gps error codes:
    5101    No response from GPS chip
    5102    No satellite fix

digital input output codes:
    520x    Failed to read door status

"""
"""
INSTALL - for python3:
Need to use 3.7 or later
then
python -m pip install TauLidarCommon
also
python3.8 -m pip install paho-mqtt
"""

import numpy as np
import cv2
import math
import time
import sys
import os
import gc

from TauLidarCommon.frame import FrameType
from TauLidarCamera.camera import Camera
import TauCameraSetup

blob_id = 0
# image from camera is 160 x 60 pixels
upperZoneLine = 55
lowerZoneLine = 5

# define range of desired color in HSV
lower_blue = np.array([105,50,50])
upper_blue = np.array([180,255,255])	# was 150, 255,255
# size of blob to be allowed - area in pixels
minBlobSize = 200
# minimum overlap for a blob to be rediscovered after it has been lost - as a percentage
minLostOverlap = 25
# Number of frames used to get a background
backgroundFrames = 10

lostSet = []

"""
setup for file based data
"""
def frsetup():
    Camera.setRange(0, 2000)

    print("\nPress Esc key over GUI or Ctrl-c in terminal to shutdown ...")

    cv2.namedWindow('Depth Map')
    cv2.namedWindow('Amplitude')

    cv2.moveWindow('Depth Map', 20, 20)
    cv2.moveWindow('Amplitude', 20, 360)

def matchBlobs(r1,r2, bPrint):
    # rectangle defined as (x, y, w, h) values
    # r1 and r2 are the two bounding boxes of the blobs to match  
    # return is (dist, overlap)
    # where dist is the distance between the centres
    # and overlap is the percentage overlap between the rectangles
    dist = 0.0
    overlap = 0.0
    
    rOv = [max(r1[0], r2[0]),\
           max(r1[1], r2[1]),\
           min(r1[0]+r1[2], r2[0] + r2[2]) - max(r1[0], r2[0]),\
           min(r1[1]+r1[3], r2[1] + r2[3]) - max(r1[1], r2[1])]
    if (bPrint): print(r1, r2, rOv)
    if ((rOv[2] < 0) or (rOv[3] < 0)):
        overlap = 0.
    else:
        overlap = 100.0*(rOv[2]*rOv[3])/\
                   ((r1[2]*r1[3])+(r2[2]*r2[3])-(rOv[2]*rOv[3]))
    
    centre1 = [r1[0]+int(r1[2]/2.0), r1[1]+int(r1[3]/2.0)]
    centre2 = [r2[0]+int(r2[2]/2.0), r2[1]+int(r2[3]/2.0)]
    dist = math.sqrt((centre1[0]-centre2[0])*\
                     (centre1[0]-centre2[0]) + \
                     (centre1[1]-centre2[1])*\
                     (centre1[1]-centre2[1]))
    
    return [int(dist), int(overlap)]

"""
Tries to match each blob in this frame, with blobs
from the previous frame
Deals with blobs that cannot be matched
for each blob in this frame
    look for the nearest blob in the previous frame (from the prevSet list)
    (nearest is based on highest overlapping percentage)
    (alternative would be distance between centres)
    If we find a matching blob, update the blob details with the new position
        of this blob, and keep track of the maximum area.

"""
def blobMatching(thisSet, prevSet):
    global blob_id, upperZoneLine, lowerZoneLine, lostSet
    # compare this set of blobs with
    # the set from the previous frame
    # and try to match the closest
    newSet = thisSet
    lastSet = prevSet
    iFound = -1
    last_removed = None
    for i in range(len(newSet)):
        c = newSet[i]
        # find the closest in the lastSet to this one's centre
        position = c[0]
        centre = c[2]
        iFound = -1
        last_dist = 1000     # start with a false maximum and look for the minimum
        last_ovr = 0	# similar for overlap but look for minimum
        last_id = 100
        if (len(lastSet) == 0):
            # no previous blobs
            last_id = 101
        for i2 in range(len(lastSet)):
            c2 = lastSet[i2]
            # find the nearest centre of the last set of blobs
            # to this centre
            # if a blob has disappeared, where was it last seen
            # and can we determine whether it has crossed from one line to the other
            r1 = c[0]
            r2 = c2[0]
            #print(r1,r2)
            newmatch = matchBlobs(r1, r2, False)
            #if (len(newSet) > 1):
            #    print("i2: "+str(i2), "last_ovr: "+str(newmatch[1])) 
            #print("i2 distance: "+str(newmatch[0]))
            """
            if (newmatch[0] < last_dist):
		# this is a closer blob - but is another blob closer to this one (c2)
                bOK = True
                for i3 in range(len(newSet)):
                    #print("i3: "+str(i3))
                    if not(i3 == i):
                        c3 = newSet[i3]
                        r3 = c3[0]
                        testmatch = matchBlobs(r3, r2, False)
                        #print("\ti3 distances", str(testmatch[0]), str(newmatch[0]))
                        if (testmatch[0] < newmatch[0]):
                            bOK = False
                #print(bOK)
                if bOK:
                    last_dist = newmatch[0]
                    last_id = c2[1]
                    iFound = i2
                    #print("iFound: "+str(iFound)) 
                pass
            """
            if (newmatch[1] > last_ovr):
		# this is a closer blob - but does another blob have more overlap than this one (c2)
                bOK = True
                for i3 in range(len(newSet)):
                    #print("i3: "+str(i3))
                    if not(i3 == i):
                        c3 = newSet[i3]
                        r3 = c3[0]
                        testmatch = matchBlobs(r3, r2, False)
                        #print("\ti3 distances", str(testmatch[0]), str(newmatch[0]))
                        if (testmatch[1] > newmatch[1]):
                            bOK = False
                # Are the two blobs with max overlap more than a specified distance apart
                """
                if (newmatch[0] > 10):
                    bOK = False
                """
                #print(bOK)
                if bOK:
                    last_ovr = newmatch[1]
                    last_id = c2[1]
                    iFound = i2
                    #if (len(newSet) > 1):
                    #    print("iFound: "+str(iFound), "last_ovr: "+str(last_ovr)) 

        #print("last_id: "+ str(last_id))
        if ((last_id == 100) or (last_id == 101)):
            """
                we did not find a match - so check whether this is a blob
                that has been lost for a few frames
            """
            bWasLost = False    # flag for blob has previously been seen before 
            i3 = 0
            while (i3 < len(lostSet)):
                testmatch = matchBlobs(c[4], lostSet[i3][4], False)
                #if ((testmatch[1] > 10) and (testmatch[1] < 70)):
                #print("testmatch1: ", testmatch)
                if (testmatch[1] > minLostOverlap):
                    #print("refound as: ", lostSet[i3][1])
                    bWasLost = True
                    c = lostSet[i3]
                    temp = lostSet.pop(i3)
                else:
                    i3 = i3 + 1
            if not(bWasLost):
                # we could not match this blob to a previous frame
                # annotate the new blob
                area = position[2]*position[3]
                #print("New blob at: "+str(position)+"   area: "+str(area))
                if centre[1] < lowerZoneLine:
                    print("line: 0", newSet)
                if  centre[1] > upperZoneLine:
                    print("line: 1", newSet)
                # !!! sort out start and newcnts indexing              
                c[1] = blob_id
                #print("New blob id: "+str(blob_id))
                lostSet = []	# remove all previously lost
                
                blob_id = blob_id + 1
                if (blob_id > 99):
                    blob_id = 0
        else:
            # update the id with the matching blob
            c[1] = last_id
            c[4] = lastSet[iFound][4]	# keep the entry point
            c[5] = lastSet[iFound][5]	# keep the entry time
            if (lastSet[iFound][3] > c[3]):
                c[3] = lastSet[iFound][3]	# keep the maximum area of this blob as it passes through
            # now we have identified the pair of blobs - remove the blob
            # from the lastSet
            #if (len(newSet) > 1):
            #    print("Removing index: "+str(iFound))
            if (iFound > -1):
                last_removed = lastSet.pop(iFound)
                #print(lastSet)
    if (len(lastSet) > 0):
        # deal with blobs that may have left the scene
        # Did it start and end on opposite zone lines, and how long was it in the zone
        for i2 in range(len(lastSet)):
            start = lastSet[i2][4]
            position = lastSet[i2][0]
            timeDiff = time.time() - lastSet[i2][5]
            area = lastSet[i2][3]
            bIsCount = False
            if (((start[1] + start[3]) > upperZoneLine) and ((position[1]) < lowerZoneLine)):
                print("Count UP   blob: "+str(lastSet[i2])+"    transit time: "+str((int(timeDiff*10))/10)+ "    at: "+str(time.time()))
                bIsCount = True
            if (((start[1]) < lowerZoneLine) and ((position[1]+position[3]) > upperZoneLine)):
                print("Count DOWN   blob: "+str(lastSet[i2])+"    transit time: "+str((int(timeDiff*10))/10)+ "    at: "+str(time.time()))
                bIsCount = True
            if not(bIsCount):
                #print("Blob not found:")
                #print("\t", start, position, lostSet, timeDiff)
                bWasLost = False
                i3 = 0
                while (i3 <len(lostSet)):
                    testmatch = matchBlobs(start, lostSet[i3][4], False)
                    #print("testmatch2: ", testmatch)
                    if (testmatch[1] > minLostOverlap):
                        #print("refound as: ", lostSet[i3])
                        newSet.append(lostSet.pop(i3))
                        #print("lostSet2: ", lostSet)
                        bWasLost = True
                    else:
                        i3 = i3 + 1
                if not(bWasLost):
                    if not(lastSet[i2][1] == 100):
                        # otherwise it has not been allocated
                        lostSet.append(lastSet[i2])
                        #print("Declaring: ", lastSet[i2], "  as lost")
            """
            if (len(newSet) > 1):
                print(newSet)
            """
    return newSet

"""
Take the set of blobs from this frame
and see whether there are any overlapping blobs that
may be merged
threshold is a percentage overlap
"""
"""
def mergeBlobs(newset, threshold):
    mergedset = []
    overlapList = []	# build a list of overlapping pairs of blobs
    for i in range(len(newset)-1):
        r1 = newset[i][0]
        j = i+1
        while (j < len(newset)):
            r2 = newset[j][0]
            newmatch = matchBlobs(r1, r2, True)
            if (newmatch[1] > threshold):
                overlapList.append([i,j])
                print(i,j, newmatch)
            j = j + 1
    for i in range(len(newset)):
        for j in range(len(overlapList)):
            if not(i == overlapList[j][1]):
                if (i == overlapList[j][0]):
                    c1 = newset[i]
                    c2 = newset[j]
                    # deal with the merging of bob i and blob j
                    # ...
                    r1 = c1[0]
                    r2 = c2[0]
                    print(r1,r2)
                    if (r2[0]+r2[2] > r1[0]+r1[2]):
                        r1[2] = r2[0]+r2[2] - r1[0]   # which extends furthest right
                    if (r2[1]+r2[3] > r1[1]+r1[3]):
                        r1[3] = r2[1]+r2[3] - r1[1]   # which extends furthest down
                    if (r2[0] < r1[0]):
                        r1[0] = r2[0]          # blob c2 starts further to the left than c1
                    if (r2[1] < r1[1]):
                        r1[1] = r2[1]          # which starts highest
                    c1[0] = r1
                    mergedset.append(c1)
                    
                else:
                    # no merging here
                    mergedset.append(newset[i])
    return mergedset
"""

def updateBackground(newFrame, backgroundArray):
    if (len(backgroundArray) == 0):
        backgroundArray = np.zeros((15,40), dtype=np.int16)
    for i in range(60):
        ii = int(i/4)
        for j in range(160):
            jj = int(j/4)
            if (newFrame[i,j] > 0):
                backgroundArray[ii,jj] += 1
    #print(newFrame)
    #print(backgroundArray)
    return backgroundArray


def removeBackground(newFrame, backgroundArray):
    if (len(backgroundArray) == 0):
        return newFrame
    else:
        frame = newFrame
        for i in range(60):
            ii = int(i/4)
            for j in range(160):
                jj = int(j/4)
                n = backgroundArray[ii,jj]
                if (n > 2*backgroundFrames):
                    frame[i,j] = 0
        return frame

"""
The main function
The record for a blob has the following structure:
[current_position, id, centre_of_blob, area_of_blob, starting_position, time_of_entry]
"""
def run(camera, framesDir):
    global blob_id, lower_blue, upper_blue, minBlobSize, lostSet
    last_cnts = []	# holds blobs from the previous frame
    blob_id = 0
    lostSet = []
    backThresh = []
    gc.collect()
    if not(framesDir == None):
        delay = 0.1 #sec
        mult = 1
        fileList = os.listdir(framesDir)
        fileList.sort()
        nFiles = len(fileList)
        iFile = 0
    bIsGood = True
    backCount = 0
    while bIsGood:
        if (camera == None):
            frame = False
            # read a frame from the list of files
            filename = fileList[iFile]
            iFile = iFile + 1
            if (iFile >= nFiles):
                bIsGood = False
                break
            with open(os.path.join(framesDir, filename), 'rb') as f:
                dataArray = bytearray(f.read())
                frame = Camera.composeFrame(dataArray, FrameType.DISTANCE_AMPLITUDE)
            pass
        else:
            # get a frame from the camera
            frame = camera.readFrame(FrameType.DISTANCE_AMPLITUDE)
        # if we have a frame analyse it
        if frame:
            centres = []
            areas = []
            newcnts = []
            mat_depth_rgb = np.frombuffer(frame.data_depth_rgb, dtype=np.uint16, count=-1, offset=0).reshape(frame.height, frame.width, 3)
            mat_depth_rgb = mat_depth_rgb.astype(np.uint8)
            """
            Next section added by GADC 15-06-21
            """
            # convert to hue for easier colour selection
            mat_depth_hsv = cv2.cvtColor(mat_depth_rgb, cv2.COLOR_RGB2HSV)
            # Threshold the HSV image to get only the desired colors
            mask = cv2.inRange(mat_depth_hsv, lower_blue, upper_blue)
            # Bitwise-AND mask and original image
            res = cv2.bitwise_and(mat_depth_rgb,mat_depth_rgb, mask= mask)
            # convert to greyscale image and then threshold to get the blobs
            # as pure white
            gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            if backCount < backgroundFrames:
                backThresh = updateBackground(thresh, backThresh)
                backCount = backCount + 1
            else:
                thresh = removeBackground(thresh, backThresh)
            # Find contours, obtain bounding box, extract and save ROI
            ROI_number = 0
            cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[0] if len(cnts) == 2 else cnts[1]
            """
            get the image again but from the camera, as a b&w image
            """
            mat_amplitude = np.frombuffer(frame.data_amplitude, dtype=np.float32, count=-1, offset=0).reshape(frame.height, frame.width)
            mat_amplitude = mat_amplitude.astype(np.uint8)
            # draw the bounding boxes onto the b&w image
            for c in cnts:
                x,y,w,h = cv2.boundingRect(c)
                position = [x, y, w, h]
                cv2.rectangle(mat_amplitude, (x, y), (x + w, y + h), (36,255,12), 2)
                # get the centre point of the blob
                cenY = y + int(h/2)
                centre = [x+int(w/2), cenY]
                area = h*w
                if (area > minBlobSize):
                    newcnts.append([position, 100, centre, area, position, time.time()])	# use 100 as an undefined id
            # now try the match these blobs with those from the previous frame - so we can track
            
            if (len(newcnts) > 1):
                #print(len(newcnts))
                #newcnts = mergeBlobs(newcnts, 10.0)
                #print(newcnts)
                pass
            
            newcnts = blobMatching(newcnts, last_cnts)
            last_cnts = newcnts
            """
            if (len(last_cnts) > 0):
                mult = 4
            else:
                mult = 1
            
            print(last_cnts)
            """
            #print("arrays: ", len(last_cnts), lostSet)

            # Upscaling the image
            upscale = 4
            depth_img =  cv2.resize(res, (frame.width*upscale, frame.height*upscale))
            amplitude_img =  cv2.resize(mat_amplitude, (frame.width*upscale, frame.height*upscale))
            cv2.imshow('Depth Map', depth_img)
            cv2.imshow('Amplitude', amplitude_img)
            #thresh_img = cv2.resize(thresh, (frame.width*upscale, frame.height*upscale))
            #cv2.imshow('Threshold', thresh_img)
            #if (camera == None): time.sleep(delay*mult)
            if cv2.waitKey(1) == 27: break
            """
            if ((camera == None) and (len(last_cnts) > 0)):
                bViewed = False
                viewCount = 0
                while ((not(bViewed)) and (viewCount < 10)) :
                     if cv2.waitKey(1) == 32: bViewed = True
                     time.sleep(0.5)
                     viewCount = viewCount + 1
             """

def cleanup(camera):
    print('\nShutting down ...')
    cv2.destroyAllWindows()
    camera.close()


if __name__ == "__main__":
    camera = TauCameraSetup.setup()
    gc.collect()

    if camera:
        try:
            cv2.namedWindow('Depth Map')
            cv2.namedWindow('Amplitude')
            
            cv2.moveWindow('Depth Map', 20, 20)
            cv2.moveWindow('Amplitude', 20, 360)
            run(camera, None)
        except Exception as e:
            print(e)

        cleanup(camera)
    else:
        # try to read from file
        camera = None
        framesDir = 'samples'
        if len(sys.argv) > 1:
           framesDir = sys.argv[1]

        frsetup()

        if os.path.exists(framesDir):
            try:
                print("\nPress Esc key over GUI or Ctrl-c in terminal to shutdown ...")
                run(None, framesDir)
            except Exception as e:
                print(e)
        pass
