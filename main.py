import numpy as np
from scipy import stats
import cv2
import numexpr as ne
import imutils
import math
import time
from queue import TQueue

# Get video feed
cap = cv2.VideoCapture("aa.mp4")

# Get region of interest (crop)
ret, frame = cap.read()
# resize
scale = 5
frame = cv2.resize(frame, (frame.shape[1] * scale, frame.shape[0] * scale), cv2.INTER_NEAREST)
(x, y, w, h) = cv2.selectROI(frame)
# (x, y, w, h) = (x // scale, y // scale, w // scale, h // scale)
leftbound = int(w * 0.02)
rightbound = int(w * 0.98)
v0 = int(h * 0.0)
v1 = int(h * 0.33)
v2 = int(h * 0.34)
v3 = int(h * 0.66)
v4 = int(h * 0.67)
v5 = int(h * 1)
lowerchroma = np.array([18, 31, 76])
upperchroma = np.array([45, 63, 122])


def get_cnt(thresh):
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    for (i, c) in enumerate(cnts):
        try:
            # compute the area of the contour along with the bounding box
            # to compute the aspect ratio
            area = cv2.contourArea(c)
            (x, y, w, h) = cv2.boundingRect(c)

            # compute the aspect ratio of the contour, which is simply the width
            # divided by the height of the bounding box
            aspectRatio = w / float(h)

            # use the area of the contour and the bounding box area to compute
            # the extent
            extent = area / float(w * h)

            # compute the convex hull of the contour, then use the area of the
            # original contour and the area of the convex hull to compute the
            # solidity
            hull = cv2.convexHull(c)
            hullArea = cv2.contourArea(hull)
            solidity = area / float(hullArea)
            angle = -1
            if len(c) > 4:
                (x, y), (MA, ma), angle = cv2.fitEllipse(c)

            equi_diameter = np.sqrt(4 * area / np.pi)
            # visualize the original contours and the convex hull and initialize
            # the name of the shape
            # cv2.drawContours(hullImage, [hull], -1, 255, -1)
            # cv2.drawContours(image, [c], -1, (240, 0, 159), 3)
            shape = ""

            if area < 2000:
                continue
            # O aspect ratio is square
            if 0.9 <= aspectRatio <= 1.1:
                shape = "o"

            # I aspect ratio is long
            elif aspectRatio >= 2.0:
                shape = "i"

            # Angle magic
            elif angle > 160 or angle < 40 or area < 3000:
                shape = "t"

            elif angle >= 115:
                shape = "z"

            elif angle >= 100:
                shape = "j"

            elif angle >= 60:
                shape = "l"

            elif angle > 50:
                shape = "s"
            else:
                shape = "?"
            return shape
            # show the contour properties
            # print("{}, {:.2f}, {:.2f}, {:.2f}, {:.2f} , {:.2f}, {:.2f}"
            #        .format(shape, aspectRatio, extent, solidity, angle, equi_diameter, area))
        except:
            # print("Error")
            return "?"
    return "?"


# Go through all the frames##
total_frames = int(cap.get(cv2.cv2.CAP_PROP_FRAME_COUNT))
skip = 5
count = 0
times = 0
last = ""
cv2.destroyAllWindows()
start = time.time()
colors = {"?":(0,0,0),
          "z": (0,0,255),
          "s": (0,255,0),
          "t": (255,0,255),
          "j": (255,121,40),
          "l": (0,150,255),
          "o": (0,255,255),
          "i": (255,255,0)
          }
while cap.isOpened():
    ret, frame = cap.read()
    if ret is None or frame is None:
        break
    if count % 500 == 0:
        print("progress {:.2f}%, {}/{}".format(count / total_frames * 100, count, total_frames))
    count += 1
    if count % skip != 0:
        continue
    frame = cv2.resize(frame, (frame.shape[1] * scale, frame.shape[0] * scale), cv2.INTER_NEAREST)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    roi = frame[y:y + h, x:x + w]
    roi = roi[math.ceil(roi.shape[0] * 0.01):int(roi.shape[0] * 0.98),
          math.ceil(roi.shape[1] * 0.05):int(roi.shape[1] * 0.98)]
    roi = cv2.blur(roi, (20, 20))
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 86, 255, cv2.THRESH_BINARY)[1]
    border = np.array([[[0, 0],
                        [int(thresh.shape[1] * .22), 0],
                        [int(thresh.shape[1] * .22), int(thresh.shape[0])],
                        [0, int(thresh.shape[0])]]], dtype=np.int32)
    thresh = cv2.fillPoly(thresh, border, (0, 0, 0))

    # Isolate Preview slots
    # pv1 = roi[v0:v1, leftbound:rightbound]
    # pv2 = roi[v2:v3, leftbound:rightbound]
    # pv3 = roi[v4:v5, leftbound:rightbound]
    pvt1 = thresh[v0:v1, leftbound:rightbound]
    pvt2 = thresh[v2:v3, leftbound:rightbound]
    pvt3 = thresh[v4:v5, leftbound:rightbound]

    # Get guesses for all three previews
    # each pv guess will have a number i guess?
    guesses = [get_cnt(pvt1), get_cnt(pvt2), get_cnt(pvt3)]

    # fix ?? guesses
    # verify different
    if TQueue.is_different(guesses, 1):
        for i, g in enumerate(guesses):
            cv2.putText(roi, g, (70, 90 + i * 210), cv2.FONT_HERSHEY_COMPLEX, 3, colors[g], 2, cv2.LINE_AA)

    TQueue.add_data(count, guesses, roi)

    # cv2.imshow('frame', stacked)
    # cv2.waitKey(0)
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #    break

TQueue.print_queue()
# TQueue.cross_check()
# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
end = time.time()
print(time.strftime("%H:%M:%S", time.gmtime(end - start)))
