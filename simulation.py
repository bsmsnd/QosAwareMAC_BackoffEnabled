# -*- coding: UTF-8 -*-

import numpy as np
import math
import os
import Event
import csv
import WarningPrint
import BPNN
import Parameters


############################################################
# FILE OPERATIONS
############################################################

if os.path.exists("para_K.csv"):
	os.remove("para_K.csv")

############################################################
# global vars & constants definition (use global mark when use externally?)
############################################################

eps = 0.00000001

# Frame structure
M = 16  # Total time slots per frame
M_BE = 8  # BE Slots
M_HQ = 8  # HQ Slots
M_Sleep = M - M_BE - M_HQ  # Sleep slots, deprecated if 802.15.4 in usage
HQ_TYPES = 3
BE_TYPES = 3
aNumSuperframeSlots = M  # for IEEE 802.15.4

# Channel & Access (MAC) Info <IEEE 802.15.4 parameters: superframes>
ChannelRate = 62500  # <symbol rate: 16us, i.e., 250kbps> Unit: sym/s
aBaseSlotDuration = 60  # unit: symbols
BO = 1
SO = 1  # When BO ~= SO ==> inactive portion exist (sleep)
aBaseSuperframeDuration = aBaseSlotDuration * aNumSuperframeSlots
BI = aBaseSuperframeDuration * math.pow(2, BO)
SD = aBaseSuperframeDuration * math.pow(2, SO)
FrameLength = BI / ChannelRate  # Unit: sec
SlotRate = BI / M  # Data Rate per slot (unit: sym)
SlotLength = SlotRate / ChannelRate
macMaxBe = 3  # by default

# Simulation Info
RunTime = 500  # Second
totSlots = RunTime / FrameLength * M
curTime = 0  # slot

# HQ & BE Indicator
HQ_INDICATOR = 0
BE_INDICATOR = 1

# All Events
newEventList_HQ_1 = []
newEventList_HQ_2 = []
newEventList_HQ_3 = []
newEventList_BE_1 = []
newEventList_BE_2 = []
newEventList_BE_3 = []

completeEventList_HQ_1 = []
completeEventList_HQ_2 = []
completeEventList_HQ_3 = []
completeEventList_BE_1 = []
completeEventList_BE_2 = []
completeEventList_BE_3 = []

# Controllers of Generators & CW
# Warning: due to multiple usage, CW controllers are all stored in Parameter module
TrafficSpeedController = [0.03, 0.03, 0.03, 0.03, 0.03, 0.03]  # total traffic: [sum] slotsize / slot
Parameters.CW_index_controller = np.array([1 for _ in range(HQ_TYPES + BE_TYPES)])
Parameters.CW_exponent_controller = np.array([1 for _ in range(HQ_TYPES + BE_TYPES)])
CW_index_switch = False
CW_exponent_switch = True# Use NO MORE THAN ONE controller
ChannelState_HQ = 0  # 0 = Idle, 1 = Busy.
ChannelState_BE = 0

# Stat
collisionCount = [0, 0, 0, 0, 0, 0]
failCount = [0, 0, 0, 0, 0, 0]  # Counter of failed transmissions of each type
# Generate events before simulation begins (?)

# State & time Markers
busyBefore_HQ = 0
busyBefore_BE = 0
idleTimeStamp_HQ = 0
idleTimeStamp_BE = 0

# First Time markers
model_first_time = True
controller_first_time_marker = True
stat_first_time_marker = True

# QoS Expectation
QoS_expect = [0.022, 0.027, 0.02, 0.015, 0.025, 0.02]

# Variables for simulation process
HQ_NotFinishedSlots = 0
BE_NotFinishedSlots = 0
HQ_NotFinishedType = 0
BE_NotFinishedType = 0
last_event_HQ = []
last_event_BE = []

# Controllers:
NN_QoS = []
NN_exponent = []


############################################################
# function definitions
############################################################


def save_backup_data(backup_file_name_prefix):
	# Warning: This function will modify the original file if exists
	# File format: time, event_type, packet_type, size
	# File naming: backup_file_name_prefix$TypeIndicator$.csv, where $TypeIndicator$ = 1,2,...,HQ_TYPES + BE_TYPES
	for i in range(HQ_TYPES + BE_TYPES):
		if i < HQ_TYPES:
			file_name = backup_file_name_prefix + str(i + 1) + ".csv"
			if os.path.exists(file_name):
				os.remove(file_name)
			with open(file_name, 'w') as f:
				if i == 0:
					for j in range(len(newEventList_HQ_1)):
						print(newEventList_HQ_1[j].time, ',', newEventList_HQ_1[j].event_type, ',',
							  newEventList_HQ_1[j].packet_type, ',', newEventList_HQ_1[j].size, file=f)
				elif i == 1:
					for j in range(len(newEventList_HQ_2)):
						print(newEventList_HQ_2[j].time, ',', newEventList_HQ_2[j].event_type, ',',
							  newEventList_HQ_2[j].packet_type, ',', newEventList_HQ_2[j].size, file=f)
				elif i == 2:
					for j in range(len(newEventList_HQ_3)):
						print(newEventList_HQ_3[j].time, ',', newEventList_HQ_3[j].event_type, ',',
							  newEventList_HQ_3[j].packet_type, ',', newEventList_HQ_3[j].size, file=f)
				else:
					WarningPrint.warning_print("error packet type at data saving process")
		else:
			file_name = backup_file_name_prefix + str(i + 1) + ".csv"
			if os.path.exists(file_name):
				os.remove(file_name)
			with open(file_name, 'w') as f:
				if i == 3:
					for j in range(len(newEventList_BE_1)):
						print(newEventList_BE_1[j].time, ',', newEventList_BE_1[j].event_type, ',',
							  newEventList_BE_1[j].packet_type, ',', newEventList_BE_1[j].size, file=f)
				elif i == 4:
					for j in range(len(newEventList_BE_2)):
						print(newEventList_BE_2[j].time, ',', newEventList_BE_2[j].event_type, ',',
							  newEventList_BE_2[j].packet_type, ',', newEventList_BE_2[j].size, file=f)
				elif i == 5:
					for j in range(len(newEventList_BE_3)):
						print(newEventList_BE_3[j].time, ',', newEventList_BE_3[j].event_type, ',',
							  newEventList_BE_3[j].packet_type, ',', newEventList_BE_3[j].size, file=f)
				else:
					WarningPrint.warning_print("error packet type at data saving process")


def load_backup_data(backup_file_name_prefix):
	# File format: time, event_type, packet_type, size
	# File naming: backup_file_name_prefix$TypeIndicator$.csv, where $TypeIndicator$ = 1,2,...,M_BE + M_HQ
	global newEventList_HQ_1
	global newEventList_HQ_2
	global newEventList_HQ_3
	global newEventList_BE_1
	global newEventList_BE_2
	global newEventList_BE_3
	for i in range(HQ_TYPES + BE_TYPES):
		file_name = backup_file_name_prefix + str(i + 1) + ".csv"
		if os.path.exists(file_name):
			event_list = []
			with open(file_name, 'r') as f:
				reader = csv.reader(f)
				for row in reader:
					read_time = int(row[0])
					read_event_type = int(row[1])
					read_packet_type = int(row[2])
					read_size = int(row[3])
					event = Event.Event(time=read_time, event_type=read_event_type, packet_type=read_packet_type,
										size=read_size)
					event_list.append(event)
			if i < HQ_TYPES:
				if i == 0:
					newEventList_HQ_1 = event_list
				elif i == 1:
					newEventList_HQ_2 = event_list
				elif i == 2:
					newEventList_HQ_3 = event_list
				else:
					WarningPrint.warning_print("error packet type at data recovery process")
			else:
				if i == 3:
					newEventList_BE_1 = event_list
				elif i == 4:
					newEventList_BE_2 = event_list
				elif i == 5:
					newEventList_BE_3 = event_list
				else:
					WarningPrint.warning_print("error packet type at data recovery process")


def packet_init(start_time, end_time, pkt_type, traffic_mode):
	# pktType: 1, 2, 3 - HQ_1, 2, 3;  4, 5, 6 - BE_1, 2, 3;
	# TrafficMode: packet arriving rate ratio with respect to ChannelRate

	# EVENT DEFINITION:
	# time: Which slot this event begins
	# event_type: 1 = new packet, 2 = backoff, 3 = transmitted,
	# 4 = retransmit
	# packet_type: defined as above "pktType"
	# size: how many slots it needs for transmission

	packet_min_size = 0.5 * SlotRate
	packet_mean_size = SlotRate
	interval_mean = packet_mean_size / ChannelRate / traffic_mode
	cur_time = start_time  # Note that cur_time in this file is a local var
	alpha = 5  # Change this value to change the shape of distribution
	scale = (alpha - 1) * SlotRate / alpha
	event_list = None  # Pointer of list:)
	if pkt_type == 1:
		event_list = newEventList_HQ_1
	elif pkt_type == 2:
		event_list = newEventList_HQ_2
	elif pkt_type == 3:
		event_list = newEventList_HQ_3
	elif pkt_type == 4:
		event_list = newEventList_BE_1
	elif pkt_type == 5:
		event_list = newEventList_BE_2
	elif pkt_type == 6:
		event_list = newEventList_BE_3
	else:
		print("packet type %d not found", pkt_type)
	while True:
		# Packet size distribution: PARETO
		pkt_size = (np.random.pareto(alpha) + 1) * scale  # +1 to shift cutoff value
		interval = math.ceil(abs(np.random.normal(interval_mean,interval_mean/5)) / SlotLength)
		cur_time = cur_time + interval
		if cur_time > end_time:
			break
		else:
			new_event = Event.Event(time=cur_time, packet_type=pkt_type, size=math.ceil(pkt_size/SlotRate))
			event_list.append(new_event)


def update_remain_slots_for_hq():
	if M_HQ - curTime % M < 0:
		WarningPrint.warning_print("error update remaining slots")
	return M_HQ - curTime % M


def update_remain_slots_for_be():
	return M_HQ + M_BE - curTime % M


def run(end_time):
	# TODO: pointer mistake at event_handler for transmission completed.
	# New idea: put all stat data into original definition.
	global curTime
	global HQ_NotFinishedSlots
	global HQ_NotFinishedType
	global BE_NotFinishedSlots
	global BE_NotFinishedType
	global busyBefore_HQ
	global idleTimeStamp_HQ
	global idleTimeStamp_BE
	global last_event_HQ
	global last_event_BE
	global busyBefore_HQ
	global busyBefore_BE
	global cur_cycle_remain_slot_for_hq
	global cur_cycle_remain_slot_for_be

	while curTime < end_time and (
			len(newEventList_HQ_1) > 0 or len(newEventList_HQ_2) > 0 or len(newEventList_HQ_3) > 0 or len(
		newEventList_BE_1) > 0 or len(newEventList_BE_2) > 0 or len(newEventList_BE_3) > 0):
		# print(curTime)
		# if newEventList_HQ_1[0].event_type == 3 or newEventList_HQ_2[0].event_type == 3 \
		# 	or newEventList_HQ_3[0].event_type == 3 or newEventList_BE_1[0].event_type == 3 \
		# 	   or newEventList_BE_2[0].event_type == 3 or newEventList_BE_3[0].event_type == 3:
		# 	pass
		while curTime % M < M_HQ:
			cur_cycle_remain_slot_for_hq = update_remain_slots_for_hq()
			if HQ_NotFinishedSlots > 0:  # complete transmission from last period
				if HQ_NotFinishedSlots > cur_cycle_remain_slot_for_hq:
					curTime += cur_cycle_remain_slot_for_hq
					HQ_NotFinishedSlots -= cur_cycle_remain_slot_for_hq
					cur_cycle_remain_slot_for_hq = 0
				else:
					curTime += HQ_NotFinishedSlots
					cur_cycle_remain_slot_for_hq = update_remain_slots_for_hq()
					busyBefore_HQ = 1
					if HQ_NotFinishedType == 1:
						newEventList_HQ_1[0].event_type = 3
						newEventList_HQ_1[0].events_handler(cur_time=curTime, idle_time_stamp=idleTimeStamp_HQ)
						completeEventList_HQ_1.append(newEventList_HQ_1.pop(0))
					elif HQ_NotFinishedType == 2:
						newEventList_HQ_2[0].event_type = 3
						newEventList_HQ_2[0].events_handler(cur_time=curTime, idle_time_stamp=idleTimeStamp_HQ)
						completeEventList_HQ_2.append(newEventList_HQ_2.pop(0))
					elif HQ_NotFinishedType == 3:
						newEventList_HQ_3[0].event_type = 3
						newEventList_HQ_3[0].events_handler(cur_time=curTime, idle_time_stamp=idleTimeStamp_HQ)
						completeEventList_HQ_3.append(newEventList_HQ_3.pop(0))
					else:
						print("packet type ", HQ_NotFinishedType, " runs in HQ by mistake" )
					HQ_NotFinishedSlots = 0
			while cur_cycle_remain_slot_for_hq > 0:  # transmission in this cycle
				min_time = math.inf
				if len(newEventList_HQ_1):
					if newEventList_HQ_1[0].event_type == 1:
						min_time = newEventList_HQ_1[0].time
					elif newEventList_HQ_1[0].event_type == 2:
						min_time = curTime + (newEventList_HQ_1[0].backoffCompleteTimeStamp - idleTimeStamp_HQ)
					else:
						WarningPrint.warning_print("Error type of event with packet type: 1")

					if newEventList_HQ_2[0].event_type == 1:
						min_time = min(newEventList_HQ_2[0].time, min_time)
					elif newEventList_HQ_2[0].event_type == 2:
						min_time = min(curTime + (newEventList_HQ_2[0].backoffCompleteTimeStamp - idleTimeStamp_HQ), min_time)
					else:
						WarningPrint.warning_print("Error type of event with packet type: 2")

					if newEventList_HQ_3[0].event_type == 1:
						min_time = min(newEventList_HQ_3[0].time, min_time)
					elif newEventList_HQ_3[0].event_type == 2:
						min_time = min(curTime + (newEventList_HQ_3[0].backoffCompleteTimeStamp - idleTimeStamp_HQ), min_time)
					else:
						WarningPrint.warning_print("Error type of event with packet type: 3")

				if min_time - curTime >= cur_cycle_remain_slot_for_hq:  # start transmission in next frame
					curTime += cur_cycle_remain_slot_for_hq
					idleTimeStamp_HQ = idleTimeStamp_HQ + cur_cycle_remain_slot_for_hq
					cur_cycle_remain_slot_for_hq = update_remain_slots_for_hq()
					break
				else:  # start transmission within this frame, move to that slot
					if min_time > curTime:  # change the time
						idleTimeStamp_HQ = idleTimeStamp_HQ + (min_time - curTime)
						curTime = min_time
						cur_cycle_remain_slot_for_hq = update_remain_slots_for_hq()
				# else: # init. should have started earlier # do nothing, as handler will work later
				transmission_log = [False for _ in range(HQ_TYPES)]
				to_transmit = -1
				if len(newEventList_HQ_1) > 0:
					if newEventList_HQ_1[0].event_type == 1 and newEventList_HQ_1[0].time <= curTime:
						newEventList_HQ_1[0].events_handler(idle_time_stamp=idleTimeStamp_HQ)
					if newEventList_HQ_1[0].event_type == 2 and newEventList_HQ_1[
						0].backoffCompleteTimeStamp == idleTimeStamp_HQ:
						transmission_log[0] = True
						to_transmit = 1

				if len(newEventList_HQ_2) > 0:
					if newEventList_HQ_2[0].event_type == 1 and newEventList_HQ_2[0].time <= curTime:
						newEventList_HQ_2[0].events_handler(idle_time_stamp=idleTimeStamp_HQ)
					if newEventList_HQ_2[0].event_type == 2 and newEventList_HQ_2[
						0].backoffCompleteTimeStamp == idleTimeStamp_HQ:
						transmission_log[1] = True
						to_transmit = 2

				if len(newEventList_HQ_3) > 0:
					if newEventList_HQ_3[0].event_type == 1 and newEventList_HQ_3[0].time <= curTime:
						newEventList_HQ_3[0].events_handler(idle_time_stamp=idleTimeStamp_HQ)
					if newEventList_HQ_3[0].event_type == 2 and newEventList_HQ_3[
						0].backoffCompleteTimeStamp == idleTimeStamp_HQ:
						transmission_log[2] = True
						to_transmit = 3

				if sum(transmission_log) > 1:  # Collide
					if transmission_log[0]:
						newEventList_HQ_1[0].event_type = 4
						newEventList_HQ_1[0].events_handler(idle_time_stamp=idleTimeStamp_HQ)
						if newEventList_HQ_1[0].event_type == 5:
							newEventList_HQ_1.pop(0)
					if transmission_log[1]:
						newEventList_HQ_2[0].event_type = 4
						newEventList_HQ_2[0].events_handler(idle_time_stamp=idleTimeStamp_HQ)
						if newEventList_HQ_2[0].event_type == 5:
							newEventList_HQ_2.pop(0)
					if transmission_log[2]:
						newEventList_HQ_3[0].event_type = 4
						newEventList_HQ_3[0].events_handler(idle_time_stamp=idleTimeStamp_HQ)
						if newEventList_HQ_3[0].event_type == 5:
							newEventList_HQ_3.pop(0)
					curTime = curTime + 1
					cur_cycle_remain_slot_for_hq = cur_cycle_remain_slot_for_hq - 1
					continue

				if sum(transmission_log) == 1:  # start transmission
					if to_transmit == 1:
						this_event = newEventList_HQ_1[0]  # confirmed to be processed, delete from Event list
					elif to_transmit == 2:
						this_event = newEventList_HQ_2[0]
					elif to_transmit == 3:
						this_event = newEventList_HQ_3[0]
					if this_event.size > cur_cycle_remain_slot_for_hq:  # unable to finish in this frame
						curTime += cur_cycle_remain_slot_for_hq
						HQ_NotFinishedSlots = this_event.size - cur_cycle_remain_slot_for_hq
						HQ_NotFinishedType = this_event.packet_type
						cur_cycle_remain_slot_for_hq = 0
					else:  # complete transmission now
						curTime += this_event.size
						cur_cycle_remain_slot_for_hq = update_remain_slots_for_hq()
						this_event.event_type = 3
						this_event.events_handler(cur_time=curTime, idle_time_stamp=idleTimeStamp_HQ)
						if to_transmit == 1:
							completeEventList_HQ_1.append(newEventList_HQ_1.pop(0))
						elif to_transmit == 2:
							completeEventList_HQ_2.append(newEventList_HQ_2.pop(0))
						elif to_transmit == 3:
							completeEventList_HQ_3.append(newEventList_HQ_3.pop(0))
						else:
							print("packet type ", to_transmit, " runs in HQ by mistake")
						HQ_NotFinishedSlots = 0
						HQ_NotFinishedType = -1
					del this_event
					continue

				if sum(transmission_log) == 0:
					curTime += 1
					cur_cycle_remain_slot_for_hq = update_remain_slots_for_hq()
					idleTimeStamp_HQ += 1
					break

		while M_HQ <= curTime % M < M_HQ + M_BE:
			cur_cycle_remain_slot_for_be = update_remain_slots_for_be()
			if BE_NotFinishedSlots > 0:  # complete transmission from last period
				if BE_NotFinishedSlots > cur_cycle_remain_slot_for_be:
					curTime += cur_cycle_remain_slot_for_be
					BE_NotFinishedSlots -= cur_cycle_remain_slot_for_be
					cur_cycle_remain_slot_for_be = 0
				else:
					curTime += BE_NotFinishedSlots
					cur_cycle_remain_slot_for_be = update_remain_slots_for_be()
					busyBefore_BE = 1
					if BE_NotFinishedType == 4:
						newEventList_BE_1[0].event_type = 3
						newEventList_BE_1[0].events_handler(cur_time=curTime, idle_time_stamp=idleTimeStamp_BE)
						completeEventList_BE_1.append(newEventList_BE_1.pop(0))
					elif BE_NotFinishedType == 5:
						newEventList_BE_2[0].event_type = 3
						newEventList_BE_2[0].events_handler(cur_time=curTime, idle_time_stamp=idleTimeStamp_BE)
						completeEventList_BE_2.append(newEventList_BE_2.pop(0))
					elif BE_NotFinishedType == 6:
						newEventList_BE_3[0].event_type = 3
						newEventList_BE_3[0].events_handler(cur_time=curTime, idle_time_stamp=idleTimeStamp_BE)
						completeEventList_BE_3.append(newEventList_BE_3.pop(0))
					else:
						print("packet type ", BE_NotFinishedType, " runs in BE by mistake", )
					BE_NotFinishedSlots = 0
			while cur_cycle_remain_slot_for_be > 0:  # transmission in this cycle
				min_time = math.inf
				if len(newEventList_BE_1):
					if newEventList_BE_1[0].event_type == 1:
						min_time = newEventList_BE_1[0].time
					elif newEventList_BE_1[0].event_type == 2:
						min_time = curTime + (newEventList_BE_1[0].backoffCompleteTimeStamp - idleTimeStamp_BE)
					else:
						WarningPrint.warning_print("Error type of event with packet type: 4")

					if newEventList_BE_2[0].event_type == 1:
						min_time = min(newEventList_BE_2[0].time, min_time)
					elif newEventList_BE_2[0].event_type == 2:
						min_time = min(curTime + (newEventList_BE_2[0].backoffCompleteTimeStamp - idleTimeStamp_BE), min_time)
					else:
						WarningPrint.warning_print("Error type of event with packet type: 5")

					if newEventList_BE_3[0].event_type == 1:
						min_time = min(newEventList_BE_3[0].time, min_time)
					elif newEventList_BE_3[0].event_type == 2:
						min_time = min(curTime + (newEventList_BE_3[0].backoffCompleteTimeStamp - idleTimeStamp_BE), min_time)
					else:
						WarningPrint.warning_print("Error type of event with packet type: 3")
				if min_time - curTime >= cur_cycle_remain_slot_for_be:  # start transmission in next frame
					curTime += cur_cycle_remain_slot_for_be
					idleTimeStamp_BE = idleTimeStamp_BE + cur_cycle_remain_slot_for_be
					cur_cycle_remain_slot_for_be = update_remain_slots_for_hq()
					break
				else:  # start transmission within this frame, move to that slot
					if min_time >= curTime:  # change the time
						idleTimeStamp_BE = idleTimeStamp_BE + (min_time - curTime)
						curTime = min_time
						cur_cycle_remain_slot_for_be = update_remain_slots_for_be()
				# else: # init. should have started earlier # do nothing, as handler will work later
				transmission_log = [False for _ in range(BE_TYPES)]
				to_transmit = -1
				if len(newEventList_BE_1) > 0:
					if newEventList_BE_1[0].event_type == 1 and newEventList_BE_1[0].time <= curTime:
						newEventList_BE_1[0].events_handler(idle_time_stamp=idleTimeStamp_BE)
					if newEventList_BE_1[0].event_type == 2 and newEventList_BE_1[
						0].backoffCompleteTimeStamp == idleTimeStamp_BE:
						transmission_log[0] = True
						to_transmit = 4

				if len(newEventList_BE_2) > 0:
					if newEventList_BE_2[0].event_type == 1 and newEventList_BE_2[0].time <= curTime:
						newEventList_BE_2[0].events_handler(idle_time_stamp=idleTimeStamp_BE)
					if newEventList_BE_2[0].event_type == 2 and newEventList_BE_2[
						0].backoffCompleteTimeStamp == idleTimeStamp_BE:
						transmission_log[1] = True
						to_transmit = 5

				if len(newEventList_BE_3) > 0:
					if newEventList_BE_3[0].event_type == 1 and newEventList_BE_3[0].time <= curTime:
						newEventList_BE_3[0].events_handler(idle_time_stamp=idleTimeStamp_BE)
					if newEventList_BE_3[0].event_type == 2 and newEventList_BE_3[
						0].backoffCompleteTimeStamp == idleTimeStamp_BE:
						transmission_log[2] = True
						to_transmit = 6

				if sum(transmission_log) > 1:  # Collide
					if transmission_log[0]:
						newEventList_BE_1[0].event_type = 4
						newEventList_BE_1[0].events_handler(idle_time_stamp=idleTimeStamp_BE)
						if newEventList_BE_1[0].event_type == 5:
							newEventList_BE_1.pop(0)
					if transmission_log[1]:
						newEventList_BE_2[0].event_type = 4
						newEventList_BE_2[0].events_handler(idle_time_stamp=idleTimeStamp_BE)
						if newEventList_BE_2[0].event_type == 5:
							newEventList_BE_2.pop(0)
					if transmission_log[2]:
						newEventList_BE_3[0].event_type = 4
						newEventList_BE_3[0].events_handler(idle_time_stamp=idleTimeStamp_BE)
						if newEventList_BE_3[0].event_type == 5:
							newEventList_BE_3.pop(0)
					curTime = curTime + 1
					cur_cycle_remain_slot_for_be = cur_cycle_remain_slot_for_be - 1
					continue

				if sum(transmission_log) == 1:  # start transmission
					if to_transmit == 4:
						this_event = newEventList_BE_1[0]  # confirmed to be processed, delete from Event list
					elif to_transmit == 5:
						this_event = newEventList_BE_2[0]
					elif to_transmit == 6:
						this_event = newEventList_BE_3[0]
					if this_event.size > cur_cycle_remain_slot_for_be:  # unable to finish in this frame
						curTime += cur_cycle_remain_slot_for_be
						BE_NotFinishedSlots = this_event.size - cur_cycle_remain_slot_for_be
						BE_NotFinishedType = this_event.packet_type
						cur_cycle_remain_slot_for_be = 0
					else:  # complete transmission now
						curTime += this_event.size
						cur_cycle_remain_slot_for_be = update_remain_slots_for_be()
						this_event.event_type = 3
						this_event.events_handler(cur_time=curTime, idle_time_stamp=idleTimeStamp_BE)
						if to_transmit == 4:
							completeEventList_BE_1.append(newEventList_BE_1.pop(0))
						elif to_transmit == 5:
							completeEventList_BE_2.append(newEventList_BE_2.pop(0))
						elif to_transmit == 6:
							completeEventList_BE_3.append(newEventList_BE_3.pop(0))
						else:
							print("packet type ", to_transmit, " runs in BE by mistake")
						BE_NotFinishedSlots = 0
						BE_NotFinishedType = -1
					del this_event
					continue

				if sum(transmission_log) == 0:
					curTime += 1
					cur_cycle_remain_slot_for_be = update_remain_slots_for_be()
					idleTimeStamp_BE += 1
					break


def print_data_to_file(file_name, var_to_print, delete_switch=False):
	# Recommendation: save file in CSV format for further usage
	if delete_switch and os.path.exists(file_name):
		os.remove(file_name)
	with open(file_name, 'a') as f:
		if (not isinstance(var_to_print, list)) and (not isinstance(var_to_print,np.ndarray)):  # single value output [as expected]
			print(var_to_print, file=f)
		else:
			for i in range(len(var_to_print) - 1):
				print(var_to_print[i], ",", end="", file=f)
			print(var_to_print[len(var_to_print) - 1], file=f)


def stat():
	global last_time  # should exist a better way?
	global delay_average
	if 'last_time' not in globals().keys():  # First time init
		if os.path.exists("pktCnt.csv"):
			os.remove("pktCnt.csv")
		if os.path.exists("delay.csv"):
			os.remove("delay.csv")
		last_time = 0
	pkt_count = [0 for _ in range(BE_TYPES + HQ_TYPES)]
	pkt_count[0] = len(completeEventList_HQ_1)
	pkt_count[1] = len(completeEventList_HQ_2)
	pkt_count[2] = len(completeEventList_HQ_3)
	pkt_count[3] = len(completeEventList_BE_1)
	pkt_count[4] = len(completeEventList_BE_2)
	pkt_count[5] = len(completeEventList_BE_3)

	effective_slots = 0
	tot_collisions = 0
	delay = [0 for _ in range(BE_TYPES + HQ_TYPES)]
	while len(completeEventList_HQ_1) > 0:
		obj = completeEventList_HQ_1.pop()
		effective_slots += obj.size
		tot_collisions += obj.collisionCount
		delay[0] += obj.time_cost()
	while len(completeEventList_HQ_2) > 0:
		obj = completeEventList_HQ_2.pop()
		effective_slots += obj.size
		tot_collisions += obj.collisionCount
		delay[1] += obj.time_cost()
	while len(completeEventList_HQ_3) > 0:
		obj = completeEventList_HQ_3.pop()
		effective_slots += obj.size
		tot_collisions += obj.collisionCount
		delay[2] += obj.time_cost()
	while len(completeEventList_BE_1) > 0:
		obj = completeEventList_BE_1.pop()
		effective_slots += obj.size
		tot_collisions += obj.collisionCount
		delay[3] += obj.time_cost()
	while len(completeEventList_BE_2) > 0:
		obj = completeEventList_BE_2.pop()
		effective_slots += obj.size
		tot_collisions += obj.collisionCount
		delay[4] += obj.time_cost()
	while len(completeEventList_BE_3) > 0:
		obj = completeEventList_BE_3.pop()
		effective_slots += obj.size
		tot_collisions += obj.collisionCount
		delay[5] += obj.time_cost()
	delay_average = np.divide(delay, pkt_count)

	# Display some data on screen
	print("effective/total slots: ", effective_slots, ' / ', curTime - last_time)
	print("collision count: ", tot_collisions)
	print("average delay(sec): ", np.multiply(delay_average, SlotLength))
	print("average delay(slots): ", delay_average)
	print("failure count: ", Event.failCount)

	# Write data to file for further analysis
	print_data_to_file(file_name='pktCnt.csv', var_to_print=pkt_count, delete_switch=(last_time == 0))
	print_data_to_file(file_name="delay.csv", var_to_print=np.multiply(delay_average, SlotLength),
					   delete_switch=(last_time == 0))
	last_time = curTime


def controller():
	global NN_QoS
	global NN_exponent
	global delay_average

	if not isinstance(NN_QoS, BPNN.PIDWithBPNN):
		NN_QoS = BPNN.PIDWithBPNN(expect_ratio=QoS_expect)
		NN_QoS.scale = 0.1
		NN_QoS.eta = 0.1126
		NN_exponent = BPNN.PIDWithBPNN(expect_ratio=QoS_expect)
		NN_exponent.scale = 0.3
		NN_exponent.eta = 0.1126
	if CW_index_switch:
		K = NN_QoS.train(np.multiply(delay_average, SlotLength))
		error = NN_QoS.error
		r = np.array([K[i][0] * (error[0][i] - error[1][i]) + K[i][1] * error[0][i]
			 + K[i][2] * (error[0][i] - 2 * error[1][i] + error[2][i]) for i in range(BE_TYPES + HQ_TYPES)])
		Parameters.CW_index_controller = np.add(Parameters.CW_exponent_controller, -r)
		print("CW_index_controller = ", Parameters.CW_index_controller)
		print_data_to_file(file_name="CW index controller.csv", var_to_print=Parameters.CW_index_controller,
						   delete_switch=(abs(r[0]) < eps))
	elif CW_exponent_switch:
		K = NN_exponent.train(np.multiply(delay_average, SlotLength))
		error = NN_exponent.error
		r = np.array([K[i][0] * (error[0][i] - error[1][i]) + K[i][1] * error[0][i]
			 + K[i][2] * (error[0][i] - 2 * error[1][i] + error[2][i]) for i in range(BE_TYPES + HQ_TYPES)])
		Parameters.CW_exponent_controller = np.add(Parameters.CW_exponent_controller, -r)
		print("CW_exponent_controller = ", Parameters.CW_exponent_controller)
		print_data_to_file(file_name="CW exponent controller.csv", var_to_print=Parameters.CW_exponent_controller,
						   delete_switch=(abs(r[0]) < eps))
	else:
		return
	# Print K to file
	# Format:
	with open("para_K.csv", 'a') as f:
		for i in range(len(K)):
			for j in range(BPNN.D):
				print(K[i][j], end=("\n" if (j == len(K) - 1 and i == BPNN.D - 1) else ","), file=f)


############################################################
# Transmission Init
############################################################

# NOTE: you may use backup dataset or save dataset for further use
# Change the following switches to save data/recover data
useBackupData = False
saveData = False
backupFileNamePrefix = "save_data"

# Set sampling period here
samplingPeriod = 50000

# Set size of data set you wish to init at the beginning
init_size = 300000

if useBackupData:
	load_backup_data(backupFileNamePrefix)
else:
	print("Generating random packets. Please wait.")
	for i in range(HQ_TYPES + BE_TYPES):
		packet_init(start_time=0, end_time=init_size, pkt_type=i + 1, traffic_mode=TrafficSpeedController[i])
	print("Generation Complete")
	if saveData:
		save_backup_data(backupFileNamePrefix)
		print("Data Saved.")

############################################################
# Access & Transmission
############################################################

data_until = init_size

print("*** Simulation begins. ***")
upper = 0
final_time = 5000000
while (len(newEventList_HQ_1) > 0 or len(newEventList_HQ_2) > 0 or len(newEventList_HQ_3) > 0 or len(
		newEventList_BE_1) > 0 or len(newEventList_BE_2) > 0 or len(newEventList_BE_3) > 0) and upper <= final_time:
	if data_until - upper <= samplingPeriod:  # Generate data if necessary
		for i in range(BE_TYPES + HQ_TYPES):
			packet_init(data_until, data_until + samplingPeriod, i + 1, TrafficSpeedController[i])
		data_until += samplingPeriod
	upper = upper + samplingPeriod
	run(upper)
	# Comment the following line to disable controller
	stat()
	# controller()
print("*** Simulation Completed. ***")
