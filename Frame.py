import numpy as np
import math

# Class def. for data frame

R = 2e7  # data rate = 20Mbps
T_avg = 400 * 8
G = T_avg / R
classes = 4  # Number of Classes: 4
normal_arrving_rate = 1400
high_arrving_rate = 2000
low_arrving_rate = 800


class Frame:
    def __init__(self, last_in_time, mean_interval=1. / normal_arrving_rate, frame_type=-1):
        self.outTime = 0
        mean = -T_avg / R
        self.frameLength = (np.random.pareto(a=5) + 1) * T_avg
        interval = np.random.rayleigh(mean_interval)
        self.inTime = last_in_time + abs(interval)
        self.frameType = frame_type
        if frame_type == -1:
            self.frameType = np.random.randint(0, classes)

    def complete_transmission(self, end_time: float):
        self.outTime = end_time

    def obtain_delay(self):
        return self.outTime - self.inTime
