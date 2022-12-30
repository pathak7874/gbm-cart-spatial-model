"""
Common camera setup parameters
so we can use for both recording and analysis
"""


from TauLidarCamera.camera import Camera

camRange = 2500
intTime = 200
minAmpl = 10 

def setup():
    camera = None
    ports = Camera.scan()                      ## Scan for available Tau Camera devices

    if len(ports) > 0:
        Camera.setRange(0, camRange)                   ## points in the distance range to be colored
        camera = Camera.open(ports[0])             ## Open the first available Tau Camera
        camera.setModulationChannel(0)             ## autoChannelEnabled: 0, channel: 0
        camera.setIntegrationTime3d(0, intTime)       ## set integration time 0: 1000
        camera.setMinimalAmplitude(0, minAmpl)          ## set minimal amplitude 0: 80

        cameraInfo = camera.info()

        print("\nToF camera opened successfully:")
        print("    model:      %s" % cameraInfo.model)
        print("    firmware:   %s" % cameraInfo.firmware)
        print("    uid:        %s" % cameraInfo.uid)
        print("    resolution: %s" % cameraInfo.resolution)
        print("    port:       %s" % cameraInfo.port)

        print("\nPress Ctrl-c in terminal to shutdown ...")

    return camera


