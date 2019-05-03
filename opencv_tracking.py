# -*- coding: utf-8 -*-
"""
Created on Fri May 3 2019
@author: robota
"""
import argparse
import cv2
import json
import numpy as np
import os
import time


# settings
font = cv2.FONT_HERSHEY_SIMPLEX
c_normal = (255, 255, 255)
c_caution = (0, 0, 255)  # BGR


class TrackingResult():

    def __init__(self, video_path, method):
        self._video_path = video_path
        self._method = method
        self._target_bbox = None
        self._ret_bboxes = []
        self._proc_mss = []

    def set_target_bbox(self, bbox):
        self._target_bbox = bbox
    
    def add_ret_bbox(self, bbox):
        self._ret_bboxes.append(bbox)
    
    def add_proc_ms(self, proc_ms):
        self._proc_mss.append(proc_ms)

    def save(self, out_path=None):
        video_fname = os.path.basename(self._video_path)
        save_path = '{}_{}.json'.format(video_fname[:-4], self._method)
        json_file = open(save_path, 'w')

        results = {'video path' : self._video_path,
                   'tracking method' : self._method,
                   'average fps' : np.mean(self._proc_mss),
                   'target bbox in 1st frame' : self._target_bbox,
                   'result bboxes' : self._ret_bboxes}
        json.dump(results, json_file)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog='opencv_tracking.py',
        description='Apply tracking to a movie.',
        add_help=True,
    )
    parser.add_argument('-v', '--video', type=str, required=True)
    parser.add_argument('-m', '--method', type=str, default='kcf',
                        choices=['boosting', 'mil', 'kcf', 'tld', 'median_flow', 'goturn'],)
    
    # 1. parse args
    args = parser.parse_args()

    method = args.method
    video_path = args.video
    if not os.path.exists(video_path):
        raise Exception(video_path + ' does not exist.')
    print('- INPUT VIDEO : ' + video_path)
    print('- TRACKING METHOD : ' + method)

    # 2. initialize tracker
    if method == 'boosting':  # Boosting
        tracker = cv2.TrackerBoosting_create()
    elif method == 'mil':     # MIL
        tracker = cv2.TrackerMIL_create()
    elif method == 'kcf':     # KCF
        tracker = cv2.TrackerKCF_create()
    elif method == 'tld':     # TLD
        tracker = cv2.TrackerTLD_create()
    elif method == 'median_flow':  # MedianFlow
        tracker = cv2.TrackerMedianFlow_create()
    elif method == 'goturn':  # GOTURN
        # Can't open "goturn.prototxt" in function 'ReadProtoFromTextFile'
        # - https://github.com/opencv/opencv_contrib/issues/941#issuecomment-343384500
        # - https://github.com/Auron-X/GOTURN-Example
        # - http://cs.stanford.edu/people/davheld/public/GOTURN/trained_model/tracker.caffemodel
        tracker = cv2.TrackerGOTURN_create()

    # load video & track a target
    video = cv2.VideoCapture(video_path)

    im_w = video.get(cv2.CAP_PROP_FRAME_WIDTH)
    im_h = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_num = video.get(cv2.CAP_PROP_FRAME_COUNT)
    
    int_ms = 1000 // int(fps)

    # to save the results
    results = TrackingResult(video_path, method)

    bbox_is_ready = False
    while(video.isOpened()):
        ret, frame = video.read()
        if not ret and bbox_is_ready:  # end of the frame
            break

        if not bbox_is_ready:
            bbox = cv2.selectROI(frame, False)
            tracker.init(frame, bbox)
            results.set_target_bbox(bbox)
            bbox_is_ready = True

        # update tracker
        t = time.time()
        track, bbox = tracker.update(frame)
        proc_ms = 1000.0 * (time.time() - t)

        # update window
        frame_disp = np.copy(frame)
        cv2.putText(frame_disp, 'FPS : {:0.1f}'.format(1000 / proc_ms),
                    (10, 20), font, 0.5, c_normal)
        if track:  # tracking success
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame_disp, p1, p2, (0,255,0), 2, 1)
        else :
            # show caution if tracking fails
            cv2.putText(frame_disp, "failure", (10,40), font, 0.5, c_caution, 1, cv2.LINE_AA)
        cv2.imshow('frame', frame_disp)

        results.add_proc_ms(1000 / proc_ms)
        results.add_ret_bbox(bbox)

        # key input
        tmp_int_ms = max(int(int_ms - proc_ms), 1)
        k = cv2.waitKey(tmp_int_ms)
        if k == 27 or k == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()

    results.save()