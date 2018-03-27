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
BI = aBaseSuperframeDuration * (2 ^ BO)
SD = aBaseSuperframeDuration * (2 ^ SO)
FrameLength = BI / ChannelRate  # Unit: sec
SlotRate = BI / M  # Data Rate per slot (unit: sym)
SlotLength = SlotRate / ChannelRate
macMaxBe = 3  # by default