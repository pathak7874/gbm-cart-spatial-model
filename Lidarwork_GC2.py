import os
import time
import sys
import person_GC2

import numpy as np
import cv2
import matplotlib.pyplot as plt
from TauLidarCommon.frame import FrameType
from TauLidarCamera.camera import Camera
from persondetection import DetectorAPI

cnt_exit   = 0
cnt_entry = 0
BinarizationThreshold = 70 
ReferenceFrame = None

try:
    log = open('log.txt',"w")
except:
    print( "can not open log file")

#open camera
#cap = cv2.VideoCapture(0)
# print(cap.get(3))
# print(cap.get(4))    


h = 480
w = 640
frameArea = h*w
areaTH = frameArea/250
print( 'Area Threshold', areaTH)

# # # Lineas de entrada/salida
# line_entry = int(2*(h/9))
# line_exit  = int(3*(h/9))

# entry_limit =   int(1*(h/5))
# exit_limit = int(4*(h/5))


line_exit =180
line_entry  =60

exit_limit =238
entry_limit =1


# print( "Red line y:",str(line_entry))
# print( "Blue line y:", str(line_exit))
line_exit_color = (255,0,0)
line_entry_color = (0,0,255)

pt1 =  [0, line_exit];
pt2 =  [w, line_exit];
pts_L1 = np.array([pt1,pt2], np.int32)
pts_L1 = pts_L1.reshape((-1,1,2))

pt3 =  [0, line_entry];
pt4 =  [w, line_entry];
pts_L2 = np.array([pt3,pt4], np.int32)
pts_L2 = pts_L2.reshape((-1,1,2))

pt5 =  [0, exit_limit];
pt6 =  [w, exit_limit];
pts_L3 = np.array([pt5,pt6], np.int32)
pts_L3 = pts_L3.reshape((-1,1,2))

pt7 =  [0, entry_limit];
pt8 =  [w, entry_limit];
pts_L4 = np.array([pt7,pt8], np.int32)
pts_L4 = pts_L4.reshape((-1,1,2))


fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows = True)

kernelOp = np.ones((3,3),np.uint8)
kernelOp2 = np.ones((5,5),np.uint8)
kernelCl = np.ones((11,11),np.uint8)

font = cv2.FONT_HERSHEY_SIMPLEX
persons = []
max_p_age = 5
pid = 1



# while(cap.isOpened()):
#     ret, frame = cap.read()


#     for i in persons:
#         i.age_one()

# def center_handle(x,y,w,h):
#     x1 = int(w/2)
#     y1 = int(h/2)
#     cx = x+x1
#     cy = y+y1 
#     return cx, cy   


    
def setup():
    Camera.setRange(0, 2000)

    print("\nPress Esc key over GUI or Ctrl-c in terminal to shutdown ...")

    cv2.namedWindow('Depth Map')
    cv2.namedWindow('Amplitude')

    cv2.moveWindow('Depth Map', 20, 20)
    cv2.moveWindow('Amplitude', 20, 360)


def run(framesDir):
    delay = 0.0 #sec

    fileList = os.listdir(framesDir)
    fileList.sort()
    global ReferenceFrame
    global cnt_exit
    global cnt_entry
    global pid

    #print("ssssssssssssssss")

    for filename in fileList:
        if not '.frame' in filename:
            continue

        #print (filename)
        #print("sssssssssssssssss")
        with open(os.path.join(framesDir, filename), 'rb') as f:
            dataArray = bytearray(f.read())
            # print("ssssssss")
            frame = Camera.composeFrame(dataArray, FrameType.DISTANCE_AMPLITUDE)
            for i in persons:
                i.age_one() 
            # print("sssssssssssssssss")
            # fgmask = fgbg.apply(frame)
          
            # imBin= cv2.threshold(fgmask,200,255,cv2.THRESH_BINARY)
                
                
            # mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp)
               
                
            # mask =  cv2.morphologyEx(mask , cv2.MORPH_CLOSE, kernelCl)
                


            if frame:
                mat_depth_rgb = np.frombuffer(frame.data_depth_rgb, dtype=np.uint16, count=-1, offset=0).reshape(frame.height, frame.width, 3)
                mat_depth_rgb = mat_depth_rgb.astype(np.uint8)

                mat_amplitude = np.frombuffer(frame.data_amplitude, dtype=np.float32, count=-1, offset=0).reshape(frame.height, frame.width)
                mat_amplitude = mat_amplitude.astype(np.uint8)

                # Upscalling the image
                upscale = 4
                depth_img =  cv2.resize(mat_depth_rgb, (frame.width*upscale, frame.height*upscale))
                amplitude_img =  cv2.resize(mat_amplitude, (frame.width*upscale, frame.height*upscale))
                
                
                # fgmask = fgbg.apply(depth_img)
          
                # imBin= cv2.threshold(fgmask,200,255,cv2.THRESH_BINARY)
                # print("sssssssssss")    
                    
                # mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp)
                
                    
                # mask =  cv2.morphologyEx(mask , cv2.MORPH_CLOSE, kernelCl)
                GrayFrame = cv2.cvtColor(depth_img, cv2.COLOR_BGR2GRAY)
                GrayFrame = cv2.GaussianBlur(GrayFrame, (21, 21), 0)

                if ReferenceFrame is None:
                    ReferenceFrame = GrayFrame
                    continue
                #Background subtraction and image binarization
                FrameDelta = cv2.absdiff(ReferenceFrame, GrayFrame)
                FrameThresh = cv2.threshold(FrameDelta, BinarizationThreshold, 255, cv2.THRESH_BINARY)[1]
        
                 #Dilate image and find all the contours
                FrameThresh = cv2.dilate(FrameThresh, None, iterations=2)
                cnts,_ = cv2.findContours(FrameThresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                #contours0, hierarchy = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                for cnt in cnts:
                    area = cv2.contourArea(cnt)         
 
                    if area > areaTH:
                        M = cv2.moments(cnt)
                        cx = int(M['m10']/M['m00'])
                        cy = int(M['m01']/M['m00'])
                        x,y,w,h = cv2.boundingRect(cnt)

                        new = True
                        if cy in range(entry_limit,exit_limit):
                            for i in persons:
                                if abs(x-i.getX()) <= w and abs(y-i.getY()) <= h:
                                    new = False
                                    i.updateCoords(cx,cy)   #actualiza coordenadas en el objeto and resets age
                                    if i.going_UP(line_entry,line_exit) == True:
                                        cnt_entry += 1;
                                        print( "ID:",i.getId(),'entry at',time.strftime("%c"))
                                        log.write("ID: "+str(i.getId())+' entry at ' + time.strftime("%c") + '\n')
                                    elif i.going_DOWN(line_entry,line_exit) == True:
                                        cnt_exit += 1;
                                        print( "ID:",i.getId(),' exit at',time.strftime("%c"))
                                        log.write("ID: " + str(i.getId()) + ' exit at ' + time.strftime("%c") + '\n')

                                    break
                                if i.getState() == '1':
                                    if i.getDir() == 'down' and i.getY() > entry_limit:
                                        i.setDone()
                                    elif i.getDir() == 'up' and i.getY() < exit_limit:
                                        i.setDone()
                                        i.setDone()
                                if i.timedOut():
                                    index = persons.index(i)
                                    persons.pop(index)
                                    del i     

                            if new == True:
                                p = person_GC2.MyPerson(pid,cx,cy, max_p_age)
                                persons.append(p)
                                pid += 1                
                        cv2.circle(depth_img,(cx,cy), 5, (0,0,255), -1)
                        img = cv2.rectangle(depth_img,(x,y),(x+w,y+h),(0,255,0),2) 


                for i in persons:
                    cv2.putText(depth_img, str(i.getId()),(i.getX(),i.getY()),font,0.3,i.getRGB(),1,cv2.LINE_AA)             


                str_exit = 'EXIT: '+ str(cnt_exit)
                str_entry = 'ENTRY: '+ str(cnt_entry)
                depth_img = cv2.polylines(depth_img,[pts_L1],False,line_exit_color,thickness=2)
                depth_img = cv2.polylines(depth_img,[pts_L2],False,line_entry_color,thickness=2)
                depth_img= cv2.polylines(depth_img,[pts_L3],False,(255,255,255),thickness=2)
                depth_img= cv2.polylines(depth_img,[pts_L4],False,(255,255,255),thickness=2)
                #cv2.putText(depth_img, str_exit ,(550,40),font,0.5,(255,255,255),2,cv2.LINE_AA)
                cv2.putText(depth_img, str_exit ,(550,40),font,0.5,(0,0,255),2,cv2.LINE_AA)
                cv2.putText(depth_img, str_entry ,(10,40),font,0.5,(255,255,255),2,cv2.LINE_AA)
                #cv2.putText(depth_img, str_entry ,(10,40),font,0.5,(255,255,255),1,cv2.LINE_AA)

                
                cv2.imshow('Depth Map', depth_img)
                cv2.imshow('Amplitude', amplitude_img)

                if cv2.waitKey(1) == 27:
                    break
        time.sleep(delay)





if __name__ == "__main__":
    framesDir = 'samples'
    if len(sys.argv) > 1:
        framesDir = sys.argv[1]

    setup()

    if os.path.exists(framesDir):
        try:
            print("\nPress Esc key over GUI or Ctrl-c in terminal to shutdown ...")
            run(framesDir)
        except Exception as e:
            print(e)



x = [cnt_exit]
# plt.plot(x,  label = "line 1")
y = [cnt_entry]

plt.scatter(x, y, c ="blue")
# # x-axis label
plt.xlabel('x - Exit')
# # frequency label
plt.ylabel('y - Entrance')

plt.title('plot chart !')

# function to show the plot
plt.show()
