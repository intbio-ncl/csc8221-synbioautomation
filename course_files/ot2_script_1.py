# This code is adapted from the Opentrons guide at https://docs.opentrons.com/v2/writing.html#writing
from opentrons import simulate 
from opentrons import protocol_api

# metadata 
metadata = {
    'protocolName': 'My Protocol',
    'author': 'Name <email@address.com>',
    'description': 'Simple protocol to get started using OT2',
    'apiLevel': '2.11'
}

# protocol run function. the part after the colon lets your editor know 
# where to look for autocomplete suggestions 
def run(protocol: protocol_api.ProtocolContext):
    
    #labware 
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2') 
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')

    # pipettes 
    left_pipette = protocol.load_instrument( 'p300_single', 'left', tip_racks=[tiprack])

    # commands 
    left_pipette.pick_up_tip() 
    left_pipette.aspirate(100, plate['A1']) 
    left_pipette.dispense(100, plate['B2']) 
    left_pipette.drop_tip()

protocol = simulate.get_protocol_api('2.11') 

run(protocol) 

for line in protocol.commands():
    print(line)
