# -*- coding: UTF-8 -*-
import math
import random
import WarningPrint
import Parameters

global failCount
global _last_transmit_type_HQ
global _last_transmit_type_BE


# EVENT DEFINITION:
# time: Which slot this event begins
# event_type: 1 = new packet, 2 = backoff, 3 = transmitted, 4 = retransmit
# packet_type: defined as above "pktType"
# size: how many slots it needs for transmission


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
		self.complete_time = -1

	def events_handler(self, idle_time_stamp, last_transmit_type=-1, cur_time=-1):
		global _last_transmit_type_HQ
		global _last_transmit_type_BE
		global failCount
		if '_last_transmit_type_HQ' not in globals().keys():
			_last_transmit_type_HQ = -1
			_last_transmit_type_BE = -1
			failCount = [0 for _ in range(Parameters.BE_TYPES + Parameters.HQ_TYPES)]
		# Handler 1: new packet arrival, necessary para: idle_time_stamp
		if self.event_type == 1:
			self.event_type = 2
			CW = math.ceil(
				math.pow(2, self.retransmit + Parameters.CW_exponent_controller[self.packet_type - 1]) * Parameters.CW_index_controller[
					self.packet_type - 1])
			backoff_time = round(random.randint(0, CW))
			self.backoffCompleteTimeStamp = idle_time_stamp + backoff_time
			if self.packet_type == _last_transmit_type_BE or self.packet_type == _last_transmit_type_HQ:
				self.backoffCompleteTimeStamp = self.backoffCompleteTimeStamp + 1
		# Handler 2: deprecated
		elif self.event_type == 2:  # Events of such type are handled in "run"
			WarningPrint.warning_print('Entered deprecated event handler')
			pass
		# Handler 3: Transmission Complete
		elif self.event_type == 3:  # necessary para: cur_time
			# Parameter check: cur_time must be set externally
			if cur_time == -1:
				WarningPrint.warning_print('cur_time not set!')
				return None
			if cur_time < self.start_time:
				WarningPrint.warning_print('cur time error!')
			self.complete_time = cur_time
			if self.packet_type < 3:
				_last_transmit_type_HQ = self.packet_type
			else:
				_last_transmit_type_BE = self.packet_type
		# Handler 4: Collision, necessary para: idle_time_stamp
		elif self.event_type == 4:
			self.event_type = 2
			self.collisionCount = self.collisionCount + 1
			self.retransmit = self.retransmit + 1
			if self.retransmit > Parameters.macMaxBe:
				failCount[self.packet_type - 1] = failCount[self.packet_type - 1] + 1
				self.event_type = 5  # indicate to be deleted
			else:
				CW = math.ceil(
					math.pow(2, self.retransmit + Parameters.CW_exponent_controller[self.packet_type - 1]) * Parameters.CW_index_controller[
						self.packet_type - 1])
				backoff_time = round(random.randint(0, CW))
				self.backoffCompleteTimeStamp = idle_time_stamp + backoff_time

	def time_cost(self):
		return self.complete_time - self.start_time
