import os
import time
from signal import signal, SIGINT

from TauLidarCommon.frame import FrameType
from TauLidarCamera.camera import Camera
import TauCameraSetup


outputDir = './samples'
runLoop = True



def run(camera):
    global runLoop
    count = 0

    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    print('Recording...')

    while runLoop:
        frame = camera.readFrameRawData(FrameType.DISTANCE_AMPLITUDE)

        if frame:
            fName = '%s/%s.frame'%(outputDir, time.time())
            with open(fName, "wb") as binary_file:
                binary_file.write(frame)
            print('\rFrame: %d'%count, end='')
            count += 1

def cleanup(camera):
    print('\nShutting down ...')
    camera.close()

def handler(signal_received, frame):
    global runLoop
    runLoop = False


if __name__ == "__main__":
    camera = TauCameraSetup.setup()

    signal(SIGINT, handler)

    if camera:
        try:
            run(camera)
        except Exception as e:
            print(e)

        cleanup(camera)

