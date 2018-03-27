# -*- coding: UTF-8 -*-
import math
import random
import WarningPrint
import Parameters

global _CW_exponent_controller
global _CW_index_controller
global _last_transmit_type_HQ
global _last_transmit_type_BE
global _collision_count
global _fail_count


# EVENT DEFINITION:
# time: Which slot this event begins
# event_type: 1 = new packet, 2 = backoff, 3 = transmitted, 4 = retransmit
# packet_type: defined as above "pktType"
# size: how many slots it needs for transmission
class CompleteEvent:
    # This is an empty class used to create C-struct-like data
    # In a CompleteEvent, those fields are necessary:
    # time_cost: total cost of time, starting from its arrival
    # retransmit: #{retransmission}
    # collisionCount: may be the same as retransmit
    # size: size of packet
    pass


class Event:
    def __init__(self, time, packet_type, size, event_type=1):
        self.time = time
        self.start_time = time
        self.event_type = event_type
        self.backoffCompleteTimeStamp = 0
        self.collisionCount = 0
        self.retransmit = 0
        self.packet_type = packet_type
        self.size = size

    def events_handler(self, idle_time_stamp, last_transmit_type=-1, cur_time=-1):
        # global curTime

        # Handler 1: new packet arrival, necessary para: idle_time_stamp
        if self.event_type == 1:
            # Parameter check: last_transmit_type must be set externally
            if last_transmit_type == -1:  # default value remains
                WarningPrint.warning_print('last_transmit_type not set!')
                return None
            self.event_type = 2
            CW = math.ceil(
                math.pow(2, self.retransmit + _CW_exponent_controller[self.packet_type - 1]) * _CW_index_controller[
                    self.packet_type - 1])
            backoff_time = round(random.randint(0, CW))
            self.backoffCompleteTimeStamp = idle_time_stamp + backoff_time
            if self.packet_type == last_transmit_type:
                self.backoffCompleteTimeStamp = self.backoffCompleteTimeStamp + 1
        # Handler 2: deprecated
        elif self.event_type == 2:
            WarningPrint.warning_print('Entered deprecated event handler')
            pass
        # Handler 3: Transmission Complete
        elif self.event_type == 3:  # necessary para: cur_time
            # Parameter check: cur_time must be set externally
            if cur_time == -1:
                WarningPrint.warning_print('cur_time not set!')
                return None
            CompleteEvent.time_cost = cur_time - self.start_time
            CompleteEvent.retransmit = self.retransmit
            CompleteEvent.collision_count = self.collisionCount
            CompleteEvent.size = self.size
            return CompleteEvent
        # Handler 4: Collision, necessary para: idle_time_stamp
        elif self.event_type == 4:
            # Parameter check: last_transmit_type must be set externally
            if last_transmit_type == -1:  # default value remains
                WarningPrint.warning_print('last_transmit_type not set!')
                return None
            self.event_type = 2
            self.collisionCount = self.collisionCount + 1
            self.retransmit = self.retransmit + 1
            _collision_count[self.packet_type - 1] = _collision_count[self.packet_type - 1] + 1
            if self.retransmit > Parameters.macMaxBe:
                _fail_count[self.packet_type - 1] = _fail_count[self.packet_type - 1] + 1
                self.event_type = 5  # indicate to be deleted
            else:
                CW = math.ceil(
                    math.pow(2, self.retransmit + _CW_exponent_controller[self.packet_type - 1]) * _CW_index_controller[
                        self.packet_type - 1])
                backoff_time = round(random.randint(0, CW))
                self.backoffCompleteTimeStamp = idle_time_stamp + backoff_time
