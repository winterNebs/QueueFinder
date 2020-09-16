from scipy import stats
from functools import reduce
import time
import cv2
import os


class TQueue:
    queue = []
    threshold = 2

    def __init__(self, frame, guesses, img):

        self.frame = frame
        self.img = img
        self.guesses = [[x] for x in guesses]

    def add_guess(self, guesses):
        for i, x in enumerate(self.guesses):
            x.append(guesses[i])

    # returns [pv#, mode/count, index]
    def get_guesses(self):
        # get most frequent occurence in each array
        guesses = []
        for g in self.guesses:
            filterg = list(filter(lambda x: x != "?", g))
            if len(filterg) > 0:
                guesses.append(stats.mode(filterg))
            else:
                guesses.append([["?"], [1]])
        return guesses

    @staticmethod
    def is_different(guesses, c):
        if c <= len(TQueue.queue):
            guess = TQueue.queue[-c].get_guesses()
            diff = 0
            # returns [pv#, mode/count, index]
            for i, g in enumerate(guess):
                if g[0][0] != guesses[i]:
                    diff += 1
            return diff >= TQueue.threshold
        return True

    @staticmethod
    def add_data(frame, guesses, img):
        if len(TQueue.queue) > 0:
            # need to check if 2/3 are distinct from previous data
            if TQueue.is_different(guesses, 1):
                # if so then create a new queue element
                if len(TQueue.queue) > 1 and not TQueue.is_different(guesses, 2):
                    TQueue.queue.pop()
                    print("Artifact frame")
                    TQueue.queue[-1].add_guess(guesses)
                else:
                    TQueue.queue.append(TQueue(frame, guesses, img))
            else:
                TQueue.queue[-1].add_guess(guesses)
        else:
            TQueue.queue.append(TQueue(frame, guesses, img))

    @staticmethod
    def cross_check():
        # TQueues
        for i, q in enumerate(TQueue.queue):
            if i == len(TQueue.queue) - 1:
                continue
            # q2 is [pv#, mode/count, index]
            # p is [mode/count, index]
            q2 = TQueue.queue[i + 1].get_guesses()
            # preview of each queue [mode/count, index]
            for j, p in enumerate(q.get_guesses()):
                if j == 0:
                    continue
                if p[0][0] != q2[j - 1][0][0]:
                    print("Mismatch at {}: {}({:.2f}%), {}({:.2f}%)".
                          format(i + j,
                                 p[0],
                                 p[1][0] / reduce((lambda x, y: x + y), p[1]) * 100,
                                 q2[j - 1][0],
                                 q2[j - 1][1][0] / reduce((lambda x, y: x + y), q2[j - 1][1]) * 100))

    @staticmethod
    def print_queue():
        frames = []
        imgs = []
        outputdir = 0
        error = True
        while os.path.isdir("output" + str(outputdir)):
            outputdir += 1
        os.mkdir("output" + str(outputdir))
        output = [[] for x in TQueue.queue[0].get_guesses()]
        for i, p in enumerate(TQueue.queue):
            guess = p.get_guesses()
            imgs.append(p.img)
            frames.append(p.frame)
            for j, o in enumerate(guess):
                output[j].append(o[0][0])
        # output should be like
        # [[1,2,3,4,5]
        #  [2,3,4,5,6]
        #  [3,4,5,6,7]]
        pvs = len(output)
        length = len(output[0])
        # go through array like this tho
        # i\j------------
        #  |[[1,2,3,4,5]
        #  |   [2,3,4,5,6]
        #  |     [3,4,5,6,7]]
        errors = []
        actual = []
        for j in range(length + pvs):
            guesses = []
            for i in range(pvs):
                if j - i < 0:
                    continue
                if j - i > length - 1:
                    continue
                guesses.append(output[i][j - i])
            filtered = list(filter((lambda x: x != "?"), guesses))

            mode = stats.mode(filtered)
            if j < length:
                if len(filtered) == 0:
                    print("Unknown at: {}({})~, {}".format(j, time.strftime("%H:%M:%S", time.gmtime(frames[j] / 60)),
                                                           guesses))
                    actual.append("?")
                    errors.append(j)
                    continue
                if mode[1][0] < pvs / 2:
                    print("Low acc at: {}({})~, {}".format(j, time.strftime("%H:%M:%S", time.gmtime(frames[j] / 60)),
                                                           guesses))
                    errors.append(j)
                try:
                    cv2.imwrite(os.path.join("output" + str(outputdir), str(j) + ".png"), imgs[j])
                except:
                    print("cannot write ", j)
            if len(mode[0]) == 0:
                actual.append("?")
            else:
                actual.append(mode[0][0])
        print("".join(actual))
        actual.insert(0,"?")
        TQueue.checkbag(actual)


    @staticmethod
    def checkbag(actual):
        bag = 0
        bagcounter = [0, 0, 0, 0, 0, 0, 0, 0]
        pmap = ["?", "z", "s", "t", "j", "l", "o", "i"]
        for i in actual:

            if bag % 7 == 0:
                ok = True
                for j in range(7):
                    if bagcounter[j + 1] != 1:
                        print(pmap[j+1], " at ", bagcounter[j + 1])
                        ok = False
                if not ok:
                    print("BAG ERROR AT ", bag)
                for j in range(len(bagcounter)):
                    bagcounter[j] = 0
            bagcounter[pmap.index(i)] += 1
            bag += 1


