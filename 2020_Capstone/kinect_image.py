try:
    import sim
except:
    print ('--------------------------------------------------------------')
    print ('"sim.py" could not be imported. This means very probably that')
    print ('either "sim.py" or the remoteApi library could not be found.')
    print ('Make sure both are in the same folder as this file,')
    print ('or appropriately adjust the file "sim.py"')
    print ('--------------------------------------------------------------')
    print ('')

import time
import os
import cv2 
import sys
import random
import ctypes
import numpy as np
import array
import math
import skimage.io
from skimage import io
from PIL import Image
import tensorflow as tf
from IPython.display import Image, display

import urllib.request
from absl import app, logging, flags
from absl.flags import FLAGS

#MAIN

def main(_argv):

    print ('Program started')

    sim.simxFinish(-1) # just in case, close all opened connections
    clientID=sim.simxStart('127.0.0.1',19999,True,True,5000,5) # Connect to CoppeliaSim

    if clientID!=-1: #if the client-sersver connection is established, execute the following code
        print ('Connected to remote API server')

        # Now try to retrieve data in a blocking fashion (i.e. a service call):
        res,objs=sim.simxGetObjects(clientID,sim.sim_handle_all,sim.simx_opmode_blocking)
        if res == sim.simx_return_ok:
            print ('Number of objects in the scene: ',len(objs))
        else:
            print ('Remote API function call returned with error code: ',res)

        # Now send some data to CoppeliaSim in a non-blocking fashion:
        sim.simxAddStatusbarMessage(clientID,'SCRIPT HAS LAUNCHED!',sim.simx_opmode_oneshot)

        #access IRB140 robot
        res_irb,robotHandle=sim.simxGetObjectHandle(clientID,'IRB140',sim.simx_opmode_oneshot_wait)
        res_manipsh,robot_ManipulatorSphere = sim.simxGetObjectHandle(clientID,
                                                'IRB140_manipulationSphere',sim.simx_opmode_oneshot_wait)
        res_tip,robot_Tip = sim.simxGetObjectHandle(clientID,'IRB140_tip',sim.simx_opmode_oneshot_wait)

        emptyBuff = bytearray()
        res,retInts,robotInitialState,retStrings,retBuffer=sim.simxCallScriptFunction(clientID,
                                                            'remoteApiCommandServer',sim.sim_scripttype_childscript,'getRobotState',
                                                            [robotHandle],[],[],emptyBuff,sim.simx_opmode_oneshot_wait)

        #access kinect

        errorCodeKinectRGB,kinectRGB=sim.simxGetObjectHandle(clientID,
                                        'kinect_rgb',sim.simx_opmode_oneshot_wait)
        errorCodeKinectDepth,kinectDepth=sim.simxGetObjectHandle(clientID,
                                        'kinect_depth',sim.simx_opmode_oneshot_wait)

        print('RGB_HANDLE = ',kinectRGB)
        print('DEPTH_HANDLE = ',kinectDepth)

        #get RGB image from kinect

        errorImportRGB,resolution_rgb,image_RGB=sim.simxGetVisionSensorImage(clientID,
                                                kinectRGB,0,sim.simx_opmode_streaming)
        print('RGB IMAGE RESOLUTION=',resolution_rgb)
        #print(image_RGB)

        #get depth image from kinect

        errorImportDepth,resolution_depth,image_depth=sim.simxGetVisionSensorDepthBuffer(clientID,kinectDepth,sim.simx_opmode_streaming)
        print('DEPTH IMAGE RESOLUTION=',resolution_depth)
        #print(resolution_depth_image)
            
        flag_write_RGB_image = 0
        flag_write_depth_image = 0

        while (sim.simxGetConnectionId(clientID) != -1):
            err_rgb, resolution_rgb, image_rgb_stream = sim.simxGetVisionSensorImage(clientID, kinectRGB, 0, sim.simx_opmode_buffer)
            if err_rgb == sim.simx_return_ok:
                print("RGB_STREAM_RECEIVED!")
                img_rgb = np.array(image_rgb_stream,dtype=np.uint8)
                img_rgb.resize([resolution_rgb[1],resolution_rgb[0],3])
                img_rgb = cv2.flip(img_rgb, 0)
                img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGB)

                cv2.imshow('RGB image',img_rgb)
                if flag_write_RGB_image == 0:
                    if not cv2.imwrite(r"D:\Research Report\tensorflow\V-REP Simulation\kinect_apple_image.png",img_rgb):
                        raise Exception("UExc: RGB Image Write Failed!")
                    flag_write_RGB_image = 1
                    print('RGB IMAGE WRITTEN TO FOLDER')

                key = cv2.waitKey(1) & 0xFF  
                if key == ord('q'):
                    sim.simxGetPingTime(clientID)
                    break
            elif err_rgb == sim.simx_return_novalue_flag:
                print("RGB_STREAM_NOT_RECEIVED")
                pass
            else:
                print(err_rgb)
            
            errorImportDepth,resolution_depth,image_depth_stream=sim.simxGetVisionSensorDepthBuffer(clientID,kinectDepth,sim.simx_opmode_buffer)
            if errorImportDepth == sim.simx_return_ok:
                resolution_depth_nclip,nearClippingPlane = sim.simxGetObjectFloatParameter(clientID, 
                        kinectDepth,(1000),sim.simx_opmode_oneshot) #sim.visionfloatparam_near_clipping (1000): float parameter : near clipping plane
                resolution_depth_fclip,farClippingPlane = sim.simxGetObjectFloatParameter(clientID, 
                        kinectDepth,(1001),sim.simx_opmode_oneshot) #sim.visionfloatparam_far_clipping (1001): float parameter : far clipping plane

                nearClippingPlane = np.full([resolution_depth[0],resolution_depth[1]],nearClippingPlane,dtype=float)
                farClippingPlane = np.full([resolution_depth[0],resolution_depth[1]],farClippingPlane,dtype=float)

                image_depth_stream = np.asarray(image_depth_stream,dtype=float)#convert list to array
                image_depth_stream = np.reshape(image_depth_stream,[640,480])#give shape to array

                distance_matrix = nearClippingPlane + np.multiply(image_depth_stream,(farClippingPlane-nearClippingPlane))        
                
                img_dist = np.array(distance_matrix,dtype=np.float)
                img_dist.resize([resolution_depth[1],resolution_depth[0]])
                img_dist = cv2.flip(img_dist, 0)                

                cv2.imshow('depth_image', img_dist)
                if flag_write_depth_image == 0:
                    if not cv2.imwrite(r"D:\Research Report\tensorflow\V-REP Simulation\kinect_apple_DEPTH_image.png",img_dist):
                        raise Exception("UExc: Depth Image Write Failed!")
                    flag_write_depth_image = 1
                    print('DEPTH IMAGE WRITTEN TO FOLDER')
                key = cv2.waitKey(1) & 0xFF  
                if key == ord('q'):
                    sim.simxGetPingTime(clientID)   
                    break
            elif err_rgb == sim.simx_return_novalue_flag:
                print("DEPTH_STREAM_NOT_RECEIVED")
                pass
            else:
                print(errorImportDepth)
        
        #Calculate Object position in world

        target_point_pixel_values = (262, 343)# MANUALLY ENTERED from [yolo_detection_program.ipynb], 
        #                                      X & Y values are interchanged since the image is 480x640 
        #   if 0 < target_point_pixel_values[0] < 240 => +ve => 240 - value
        #   if 0 < target_point_pixel_values[1] < 320 => +ve => 320 - value

        center_of_image = (240,320) #resolution is 480x640
        target_point_with_origin_at_center = [0,0] 

        target_point_with_origin_at_center[0] = center_of_image[0] - target_point_pixel_values[0]
        target_point_with_origin_at_center[1] = center_of_image[1] - target_point_pixel_values[1]

        print('target_point_with_origin_as_center = ', target_point_with_origin_at_center)   
        distance_value_at_target_point = img_dist[target_point_pixel_values[0], target_point_pixel_values[1]] #resolution was transposed earlier (actual point location is (383,292))
        print('distance_value_at_target_point = ', distance_value_at_target_point)

        #fov = 62 x 48.6 degrees, 10x10 pixels per degree 
        #kinect_fov = 48.6

        #z_w = distance_value_at_target_point
        
        #x_v, y_v = location on the picture according to the camera frame, with the center of the image as origin
        x_v = target_point_with_origin_at_center[1]
        y_v = target_point_with_origin_at_center[0]
        
        #f = kinect_focal_length = 579.83 from MS Kinect SDK. Also can be approx. calculated using formula in word doc 
        f = 579.83

        #z_w = distance form the camera (z_world) according to the v-rep coordinate system
        D = distance_value_at_target_point 
        #z_w = (D*f)/math.sqrt(x_v**2 + y_v**2 + f**2)
        z_w = D

        #by similar triangles yw / zw = yv / f, xw / zw = xv / f

        y_w = (z_w * y_v) / f            
        x_w = (z_w * x_v) / f

        print("Position of Apple wrt Camera :")
        print("x_w  = ",x_w)
        print("y_w  = ",y_w)
        print("z_w  = ",z_w)
        Pos_apple_wrt_cam = np.mat([x_w,y_w,z_w,1])

        #Pos_apple_wrt_cam is relative to the camera.. now calc actual world position..
        
        #APPLE & CAMERA DATA

        #get actual apple position for reference
        res_apple_get, appleHandle = sim.simxGetObjectHandle(clientID, 'Apple', sim.simx_opmode_oneshot_wait)
        pos_Apple_ret, Apple_position = sim.simxGetObjectPosition(clientID, appleHandle, -1, sim.simx_opmode_oneshot_wait)
        
        cam_pos_ret, kinect_Position = sim.simxGetObjectPosition(clientID, kinectDepth, -1, sim.simx_opmode_oneshot_wait)
        print("Kinect Position: (x = " + str(kinect_Position[0]) + \
                ", y = " + str(kinect_Position[1]) +\
                ", z = " + str(kinect_Position[2]) + ")")
        
        cam_ori_ret, kinect_Orientation = sim.simxGetObjectOrientation(clientID, kinectDepth, -1, sim.simx_opmode_oneshot_wait)
        print("Kinect Orientation: (x(Alpha) = " + str(kinect_Orientation[0]) + \
                ", y(Beta) = " + str(kinect_Orientation[1]) +\
                ", z(Gamma) = " + str(kinect_Orientation[2]) + ")")

        Y = kinect_Orientation[0]
        B = kinect_Orientation[1]
        A = kinect_Orientation[2]

        # Tx_cam_wrt_base_singleStep = np.mat([[math.cos(A)*math.cos(B), math.cos(A)*math.sin(B)*math.sin(Y) - math.sin(A)*math.cos(Y), math.cos(A)*math.sin(B)*math.cos(Y) + math.sin(A)*math.sin(Y), kinect_Position[0]],
        #                                     [math.sin(A)*math.cos(B), math.sin(A)*math.sin(B)*math.sin(Y) + math.cos(A)*math.cos(Y), math.sin(A)*math.sin(B)*math.cos(Y) - math.cos(A)*math.sin(Y), kinect_Position[1]],
        #                                     [-math.sin(B), math.cos(B)*math.sin(Y), math.cos(B)*math.cos(Y), kinect_Position[2]],
        #                                     [0,0,0,1]])

        T_rot_x = np.mat([[1, 0, 0, 0],
                            [0, math.cos(Y), -math.sin(Y), 0],
                            [0, math.sin(Y), math.cos(Y), 0],
                            [0, 0, 0, 1]])
        
        T_rot_y = np.mat([[math.cos(B), 0, math.sin(B), 0],
                            [0, 1, 0, 0],
                            [-math.sin(B), 0, math.cos(B), 0],
                            [0, 0, 0, 1]])

        T_rot_z = np.mat([[math.cos(A), -math.sin(A), 0, 0],
                            [math.sin(A), math.cos(A), 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]])

        T_trans_x = np.mat([[1, 0, 0, kinect_Position[0]],
                                [0, 1, 0, 0],
                                [0, 0, 1, 0],
                                [0, 0, 0, 1]])

        T_trans_y = np.mat([[1, 0, 0, 0],
                                [0, 1, 0, kinect_Position[1]],
                                [0, 0, 1, 0],
                                [0, 0, 0, 1]])
        
        T_trans_z = np.mat([[1, 0, 0, 0],
                                [0, 1, 0, 0],
                                [0, 0, 1, kinect_Position[2]],
                                [0, 0, 0, 1]])

        Tx_cam_wrt_base_process = T_trans_x @ T_trans_y @ T_trans_z @ T_rot_x @ T_rot_y @ T_rot_z
        
        rows = Tx_cam_wrt_base_process.shape[0]
        cols = Tx_cam_wrt_base_process.shape[1]

        for x in range(0, rows):
            for y in range(0, cols):
                if abs(Tx_cam_wrt_base_process[x,y]) < 1e-5:
                    Tx_cam_wrt_base_process[x,y] = 0 #rounding down very small values to zero

        #print('Transform_cam_wrt_base SINGLE_STEP = ', Tx_cam_wrt_base_singleStep)

        print('Transform_cam_wrt_base_PROCESS = ', Tx_cam_wrt_base_process)

        Pos_Apple_wrt_base = np.mat(np.matmul(Tx_cam_wrt_base_process, np.transpose(Pos_apple_wrt_cam)))
        #Pos_Apple_wrt_base = Tx_cam_wrt_base @ np.transpose(Pos_apple_wrt_cam)

        print('Position_Apple_wrt_base (calculated) = ', Pos_Apple_wrt_base)
        print("Actual Apple Position: (x = " + str(Apple_position[0]) + \
                ", y = " + str(Apple_position[1]) +\
                ", z = " + str(Apple_position[2]) + ")")

        robot_target = (Pos_Apple_wrt_base[0], Pos_Apple_wrt_base[1], Pos_Apple_wrt_base[2])

        # Now create a dummy object at coordinate robot_target called 'Robot_target' 
            # and move the end effector towards that point :
            
        res,retInts,retFloats,retStrings,retBuffer=sim.simxCallScriptFunction(clientID,
                                                    'Apple',sim.sim_scripttype_childscript,'createDummy_function',
                                                    [],[robot_target[0],robot_target[1],robot_target[2]],['Robot_target'],
                                                    emptyBuff,sim.simx_opmode_blocking)
        if res==sim.simx_return_ok:
            print ('Dummy Created!! Its handle is: ',retInts[0]) # display the reply from CoppeliaSim (in this case, the handle of the created dummy)
            res,robot_target_point_handle = sim.simxGetObjectHandle(clientID,'Robot_target#',sim.simx_opmode_oneshot_wait)
            res,retInts,robot_target_point_Pose,retStrings,retBuffer=sim.simxCallScriptFunction(clientID,
                                                                    'Apple',sim.sim_scripttype_childscript,'getObjectPose',
                                                                    [robot_target_point_handle],[],[],emptyBuff,
                                                                    sim.simx_opmode_oneshot_wait)
            #print("robot_target_point_Pose = ", robot_target_point_Pose)
            res,retInts,robot_target_point_Pose,retStrings,retBuffer=sim.simxCallScriptFunction(clientID,
                                                                    'Apple',sim.sim_scripttype_childscript,'align_robot_with_target',
                                                                    [],[],[],emptyBuff,sim.simx_opmode_oneshot_wait)
            print("The robot should have moved towards the apple!")
        else:
            print ('Remote function call failed')

        #sim.simxSetObjectPosition(clientID, robot_ManipulatorSphere, -1, robot_target, sim.simx_opmode_oneshot_wait)

        # Before closing the connection to CoppeliaSim, make sure that the last command sent out had time to arrive. You can guarantee this with (for example):
        sim.simxGetPingTime(clientID)

        # Now close the connection to CoppeliaSim:
        sim.simxFinish(clientID)

    else:
        print ('Failed connecting to remote API server')
        print ('Program ended')



if __name__ == '__main__':
    try:
        app.run(main)
    except SystemExit:
        pass