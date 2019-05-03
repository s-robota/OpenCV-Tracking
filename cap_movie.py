# -*- coding: utf-8 -*-
"""
Created on Fri May 3 2019
@author: robota
"""
import argparse
import cv2
import datetime
import numpy as np
import os
import sys
import time


# settings
font = cv2.FONT_HERSHEY_SIMPLEX
c_normal = (255, 255, 255)
c_caution = (0, 0, 255)  # BGR


class FpsCounter():
    def __init__(self):
        self._interval_secs = []
        self._history_num = 20
        self._t = time.time()
    
    def count(self):
        cur_t = time.time()
        int_sec = cur_t - self._t
        self._t = cur_t
        self._interval_secs.append(int_sec)
        if len(self._interval_secs) > self._history_num:
            self._interval_secs.pop(0)
    
    @property
    def cur_fps(self):
        mean_sec = np.mean(self._interval_secs)
        return 1 / mean_sec


def cur_datetime_str():
    return datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog='cam_capture.py',
        description='Capture a movie with web-cam.',
        add_help=True,
        )
    parser.add_argument('-o', '--outdir', type=str, default='./out')
    parser.add_argument('-s', '--size', help='width and height', 
                        type=int, nargs=2, default=(640, 480))
    parser.add_argument('--lr_flip', default=False, action='store_true', 
                        help='If true, left-right flipped video will be shown & captured.')

    args = parser.parse_args()

    # 1. parse args
    outdir = args.outdir
    outdir += '/' if outdir[-1] != '/' else ''
    print('OUTPUT DIR : ' + outdir)
    if not os.path.exists(outdir):
        os.mkdir(outdir)
        print('- {} was newly created.'.format(outdir))

    cap_w, cap_h = args.size
    cap_size = (cap_w, cap_h)
    print('CAPTURE SIZE (width, height) : {}'.format(cap_size))

    lr_flip = args.lr_flip

    # 2. capture

    # (initialize) create a VideoCapture Instance. Specify camera by the argment.
    cap = cv2.VideoCapture(0)
    is_capturing = False
    out_fpath = None
    video_writer = None  # cv2.VideoWriter
    fps_counter = FpsCounter()

    # start loading camera's images
    while True:
        # Read a single frame from VideoCapture
        ret, frame = cap.read()
        if frame is None:
            raise Exception('Can not capture. Please check if the camera is connected correctly.')

        fps_counter.count()
        frame = cv2.resize(frame, cap_size)
        if lr_flip:
            frame = frame[:,::-1]

        # display some information
        frame_disp = np.copy(frame)
        cv2.putText(frame_disp, 'FPS : {:0.1f}'.format(fps_counter.cur_fps),
                    (10, 20), font, 0.5, c_normal)
        if is_capturing:
            cv2.putText(frame_disp, 'Now capturing', (10, 40), font, 0.5, c_caution)
            cv2.putText(frame_disp, 'Save Path : ' + out_fpath, (10, 60), font, 0.5, c_caution)
        else:
            cv2.putText(frame_disp, "Push 'Enter' to capture", (10, 40), font, 0.5, c_normal)

        # update
        cv2.imshow('webcam', frame_disp)
        if is_capturing:
            video_writer.write(frame)
    
        # wait for key input for 1ms
        k = cv2.waitKey(1)
        if k == 27 or k == ord('q'): # Esc
            break
        elif k == 13: # Enter
            is_capturing = not is_capturing
            if is_capturing:
                out_fpath = outdir + 'cap_{}.mp4'.format(cur_datetime_str())
                video_writer = cv2.VideoWriter(out_fpath, cv2.VideoWriter_fourcc('m','p','4','v'), 30, cap_size)
                print('start capture')
            else:
                video_writer.release()
                print('stop capture')

    # Release Capture & Destroy all windows
    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()
