import json, os
from opentrons import protocol_api
from opentrons import simulate

# Record the protocol's metadata # ##################################
metadata = {
    "protocolName": "CSC8331 Practical 2 – PCR Example",
    "author": "Bradley Brown",
    "author-email": "b.bradley2@newcastle.ac.uk",
    "user": "",
    "user-email": "",
    "source": "Adapted from NEB international.neb.com/protocols/2013/12/13/pcr-using-q5-high-fidelity-dna-polymerase-m0491",
    "apiLevel": "2.11",
}

def next_empty_slot(protocol):
    # temporary workaround if Thermocycler is loaded
    if str(protocol.deck[7]) == "Thermocycler Module on 7":
        for slot in [1,2,3,4,5,6,9]:
            labware = protocol.deck[slot]
            if labware is None: # if no labware loaded into slot    
                return(slot)
    else:
        for slot in protocol.deck:
            labware = protocol.deck[slot]
            if labware is None: # if no labware loaded into slot
                return(slot)
    raise IndexError('No Deck Slots Remaining')

def load_custom_labware(parent, file, deck_position = None, label = None):
    # Open the labware json file
    with open(file) as labware_file:
        labware_file = json.load(labware_file)

    # Check if `parent` is the deck or a hardware module, and treat it acordingly
    if parent.__class__ == protocol_api.protocol_context.ProtocolContext:
        # If no deck position, get the next empty slot
        if not deck_position:
            deck_position = next_empty_slot(parent)
        labware = parent.load_labware_from_definition(labware_file, deck_position, label)
    else:
        labware = parent.load_labware_from_definition(labware_file, label)

    return(labware)

# Define the run function
## The run function should take a single argument, 'protocol'
## The value of the protocol argument is an Opentrons object, which stores all information
## about Opentrons protocols
def run(protocol: protocol_api.ProtocolContext):

    #################
    # Load hardware #
    #################
    # Here the hardware of the Opentrons in loaded
    # For this example, the Opentrons being used has two pipettes:
    ## a p20 and a p300
    ## The p20 is mounted in the left position
    ## The p3000 is mounted in the right position
    # Load the p20 pipette in the left position
    p20 = protocol.load_instrument("p20_single_gen2", "left")
    # Load the p300 pipette in the right position
    p300 = protocol.load_instrument("p300_single_gen2", "right")
    # Two modules will be used in this protocol
    ## The temperature module is usually loaded in deck position 4
    ## The thermocycler module spans four deck positions (7, 8, 10, and 11)
    ### The thermocycler module can only be placed in these positions,
    ### so you don't need to specify the location in the code below
    # Load the temperature module in position 4
    Temp_Module = protocol.load_module("temperature module gen2", 4)
    # Load the thermocycler - this takes up positions 7, 8, 10, and 11
    Thermocycler = protocol.load_module("Thermocycler Module")

    ################################
    # Load and assign pipette tips #
    ################################
    # Here the two types of pipette tips are loaded
    # There 20 uL tips work with the p20 pipette
    # The 300 uL tips work with the p300 pipette
    # Load 20 uL tips in deck position 1
    Tip_Rack_20 = protocol.load_labware("opentrons_96_tiprack_20ul", 1)
    # Load 300 uL tips in deck position 2
    Tip_Rack_300 = protocol.load_labware("opentrons_96_tiprack_300ul", 2)
    # The loaded tip racks can be assigned to a pipette
    ## Pipettes with assigned tip racks will automatically select tips
    ## and will keep track of which tips in the rack have already been used
    # Assign tip racks to appropriate pipette
    p20.tip_racks.append(Tip_Rack_20)
    p300.tip_racks.append(Tip_Rack_300)
    #########################
    # Define source labware #
    #########################
    # Here the labware containing the source materials are loaded
    # First the type of labware is defined
    ## Labware type is associated with an API name, as can be seen below
    Reagent_and_Mastermix_Labware_Type = "opentrons_24_aluminumblock_nest_1.5ml_snapcap"
    DNA_and_Primer_Labware_Type = "3dprinted_24_tuberack_1500ul"
    # Once the labware types have been specified, the labware can be loaded to
    # the 'protocol' object
    # The code below loads the labware which contains the reagents onto the
    # # temperature module
    ## The reagent labware is loaded onto the temperature module so they can be kept cool
    ## If you wanted to load the reagent labware directly onto the Opentrons deck instead of ## the temperature module, you would replace `Temp_Module` with `protocol` in the
    ## code below, and specify a deck position
    # In the code below, the `label` argument is used to give the labware
    # a human-friendly name
    Reagent_and_Mastermix_Labware = Temp_Module.load_labware(
        Reagent_and_Mastermix_Labware_Type, label="Reagents"
    )
    # Next the DNA and primer labware is loaded onto position 3 of the Opentrons deck
    # The labware used here is custom labware, which means that its definition is not # included by default
    # Loading custom labware so that it can be used in both simulations and execution
    # can be tricky
    # Here, we use the helper function described earlier to help us
    # The `parent` argument below indicates where the labware should be loaded
    ## Using `protocol` for the `parent` argument means that the labware will be
    ## loaded to the deck
    ## If you wished to load the labware to the temperature deck, then `Temp_Module`
    ## could be used instead
    # The `custom_labware_dir` argument specifies the directory where the custom
    # labware definition is stored
    ## labware definitions are json files which are named using the API name
    ## In the code below, it is indicated that the custom labware is located in a directory
    ## called 'labware', which should be located in the same directory as this protocol
    
    DNA_and_Primer_Labware = load_custom_labware(
        parent=protocol,
        file= "labware/" + DNA_and_Primer_Labware_Type + ".json",
        deck_position=3,
        label="DNA and Primers"
    )
    
    ####################################
    # Define source material locations #
    ####################################
    # In the code below, the location of the source material is stored for use later
    ## As an example, the first line of code states that the Q5_Buffer is stored in the
    ## Reagent_and_Mastermix labware in position A1
    Q5_Buffer = Reagent_and_Mastermix_Labware.wells_by_name()["A1"]
    dNTPs = Reagent_and_Mastermix_Labware.wells_by_name()["A2"]
    Q5_Polymerase = Reagent_and_Mastermix_Labware.wells_by_name()["A3"]
    Water = Reagent_and_Mastermix_Labware.wells_by_name()["A4"]
    pTESTa_Insert1 = DNA_and_Primer_Labware.wells_by_name()["A1"]
    pTESTa_Insert2 = DNA_and_Primer_Labware.wells_by_name()["A2"]
    pTESTa_Insert3 = DNA_and_Primer_Labware.wells_by_name()["A3"]
    pTESTa_Insert4 = DNA_and_Primer_Labware.wells_by_name()["A4"]
    pTESTb_Insert5 = DNA_and_Primer_Labware.wells_by_name()["A5"]
    pTESTb_Insert6 = DNA_and_Primer_Labware.wells_by_name()["A6"]
    pTESTb_Insert7 = DNA_and_Primer_Labware.wells_by_name()["B1"]
    pTESTb_Insert8 = DNA_and_Primer_Labware.wells_by_name()["B2"]
    Forward_Primer_A = DNA_and_Primer_Labware.wells_by_name()["C1"]
    Reverse_Primer_A = DNA_and_Primer_Labware.wells_by_name()["C2"]
    Forward_Primer_B = DNA_and_Primer_Labware.wells_by_name()["C3"]
    Reverse_Primer_B = DNA_and_Primer_Labware.wells_by_name()["C4"]
    ##############################
    # Define destination labware #
    ##############################
    # Similar to above, here the labware which will be used to prepare the PCR
    # reactions is loaded
    Destination_Labware_Type = "nest_96_wellplate_100ul_pcr_full_skirt"
    # The code below loads the PCR reactions labware to the thermocycler
    ## This is similar to how the reagents labware was loaded to the temperature module above
    Destination_Labware = Thermocycler.load_labware(
        Destination_Labware_Type, "PCR Reactions"
    )
    #########################################
    # Define destination material locations #
    #########################################
    # Again, similar to above, the locations where the mastermix and PCR reactions
    # will be prepared is stored for later use
    # Here it is stated that the mastermix will be prepared in a tube at position B1
    # in the same labware as the reagents, which allows the mastermix to be kept cool
    Mastermix = Reagent_and_Mastermix_Labware.wells_by_name()["B1"]
    # The locations for each of the PCR reactions are set below
    pTESTa_Insert1_PCR = Destination_Labware.wells_by_name()["B2"]
    pTESTa_Insert2_PCR = Destination_Labware.wells_by_name()["B3"]
    pTESTa_Insert3_PCR = Destination_Labware.wells_by_name()["B4"]
    pTESTa_Insert4_PCR = Destination_Labware.wells_by_name()["B5"]
    pTESTb_Insert5_PCR = Destination_Labware.wells_by_name()["B6"]
    pTESTb_Insert6_PCR = Destination_Labware.wells_by_name()["B7"]
    pTESTb_Insert7_PCR = Destination_Labware.wells_by_name()["B8"]
    pTESTb_Insert8_PCR = Destination_Labware.wells_by_name()["B9"]
    Negative_Control_PCR = Destination_Labware.wells_by_name()["B10"]
    ####################
    # Set temperatures #
    ####################
    # Before starting the protocol, the temperature and thermocycler modules should be
    # set to 4 celcius
    Temp_Module.set_temperature(4)
    Thermocycler.set_block_temperature(4)
    # You should then ensure that the Thermocycler lid is open, so that the PCR plate # can be loaded
    Thermocycler.open_lid()
    # A good habit to get into before issuing liquid handling commands is to pause
    # the protocol and prompt the user to ensure that everything is loaded to the
    # Opentrons deck
    protocol.pause("Ensure all labware and reagents are loaded")
    #####################
    # Prepare mastermix #
    #####################
    # One of the simplest Opentrons commands is the `transfer()` method
    ## This method is called on the pipette type you wish to use
    ## and defines the amount of liquid to transfer, the source location, and the destination
    # The code below commands the p300 pipette to transfer 100 uL of liquid
    # from the Q5 buffer source location, and dispense it into the mastermix tube
    # As the p300 pipette already has a tip rack assigned to it, the tip will be
    # automatically picked up with this command, and will be disposed of in the
    # trash afterwards p300.transfer(100, Q5_Buffer, Mastermix)
    # The next code block transfers 315 uL of water from the water source tube
    # to the mastermix tube
    # The p300 pipette can only transfer 300 uL at a time, so this transfer action# has been split into two
    # Transfer water to the mastermix (315 uL) p300.transfer(200, Water, Mastermix) p300.transfer(115, Water, Mastermix)
    # In the code below the p20 pipette is used to transfer 10 uL of dNTPs to the
    # mastermix tube
    # The p20 pipette should be used to transfer liquid between 2 and 20 uL
    # For volumes above 20 uL, the p300 pipette can be used p20.transfer(10, dNTPs, Mastermix)
    # Here, a mixing event by pipetting up and down will occur after the Q5 polymerase
    # has been transferred. The mixing will occur by pipetting 20 uL of liquid in the
    # mastermix tube up and down 10 times
    p20.transfer(5, Q5_Polymerase, Mastermix, mix_after=(10, 20))
    ######################################
    # Add mastermix to destination wells #
    ######################################
    # Once the mastermix has been prepared using the code above, it is distributed
    # into each of the PCR wells in the destination plate
    # This list contains all of the destination locations for the PCR reactions
    Destination_Wells = [
        pTESTa_Insert1_PCR,
        pTESTa_Insert2_PCR,
        pTESTa_Insert3_PCR,
        pTESTa_Insert4_PCR,
        pTESTb_Insert5_PCR,
        pTESTb_Insert6_PCR,
        pTESTb_Insert7_PCR,
        pTESTb_Insert8_PCR,
        Negative_Control_PCR,
    ]
    # The `distribute` method is called on a pipette similar to the `transfer` method above
    # This method takes the following arguments:
    ## The volume of liquid to dispense into each destination location (43)
    ## The source location from which the liquid should be taken (the mastermix tube)
    ## A list of destination locations (stored above as `Destination_Wells`)
    # A mixing event can also be specified here, as with the `transfer` method above
    ## Here, the contents of the mastermix tube are mixed by pipetting 300 uL of liquid
    ## up and down 10 times before aspirating the liquid p300.distribute(43, Mastermix, Destination_Wells, mix_before=(10, 300))
    ####################################
    # Add Primers to destination wells #
    ####################################
    # The following code transfers 2.5 uL of the relevant primer
    # to each PCR in the destination plate
    p20.transfer(2.5, Forward_Primer_A, pTESTa_Insert1_PCR)
    p20.transfer(2.5, Reverse_Primer_A, pTESTa_Insert1_PCR)
    p20.transfer(2.5, Forward_Primer_A, pTESTa_Insert2_PCR)
    p20.transfer(2.5, Reverse_Primer_A, pTESTa_Insert2_PCR)
    p20.transfer(2.5, Forward_Primer_A, pTESTa_Insert3_PCR)
    p20.transfer(2.5, Reverse_Primer_A, pTESTa_Insert3_PCR)
    p20.transfer(2.5, Forward_Primer_A, pTESTa_Insert4_PCR)
    p20.transfer(2.5, Reverse_Primer_A, pTESTa_Insert4_PCR)
    p20.transfer(2.5, Forward_Primer_B, pTESTb_Insert5_PCR)
    p20.transfer(2.5, Reverse_Primer_B, pTESTb_Insert5_PCR)
    p20.transfer(2.5, Forward_Primer_B, pTESTb_Insert6_PCR)
    p20.transfer(2.5, Reverse_Primer_B, pTESTb_Insert6_PCR)
    p20.transfer(2.5, Forward_Primer_B, pTESTb_Insert7_PCR)
    p20.transfer(2.5, Reverse_Primer_B, pTESTb_Insert7_PCR)
    p20.transfer(2.5, Forward_Primer_B, pTESTb_Insert8_PCR)
    p20.transfer(2.5, Reverse_Primer_B, pTESTb_Insert8_PCR)
    p20.transfer(2.5, Water, Negative_Control_PCR)
    p20.transfer(2.5, Water, Negative_Control_PCR)
    
    ########################################
    # Add DNA to destination wells and mix #
    ########################################
    # The code below transfers 2 uL of the relevant DNA template to each of the
    # PCR reactions in the destination plate
    # As this is the last reagent to be added to the PCRs, a mixing event is
    # specified once the DNA has been added
    p20.transfer(2, pTESTa_Insert1, pTESTa_Insert1_PCR, mix_after=(10, 20))
    p20.transfer(2, pTESTa_Insert2, pTESTa_Insert2_PCR, mix_after=(10, 20))
    p20.transfer(2, pTESTa_Insert3, pTESTa_Insert3_PCR, mix_after=(10, 20))
    p20.transfer(2, pTESTa_Insert4, pTESTa_Insert4_PCR, mix_after=(10, 20))
    p20.transfer(2, pTESTb_Insert5, pTESTb_Insert5_PCR, mix_after=(10, 20))
    p20.transfer(2, pTESTb_Insert6, pTESTb_Insert6_PCR, mix_after=(10, 20))
    p20.transfer(2, pTESTb_Insert7, pTESTb_Insert7_PCR, mix_after=(10, 20))
    p20.transfer(2, pTESTb_Insert8, pTESTb_Insert8_PCR, mix_after=(10, 20))
    p20.transfer(2, Water, Negative_Control_PCR, mix_after=(10, 20))

    ########################
    # Perform thermocyling #
    ########################
    # The code below closes the thermocycler lid
    Thermocycler.close_lid()
    Thermocycler.set_lid_temperature(105)
     # Here the temperature of the thermocycler lid is set
    ## This helps seal the plate with a thermal film, and also helps prevent
    ## the reaction from condensing at the tops of the tube
    # The Opentrons thermocycler is programmed using profiles
    # The first profile tells the thermocycler block to heat to 98 C # and wait 30 seconds

    Initial_Denaturation_Profile = [{"temperature": 98, "hold_time_seconds": 30}]
    # The second profile has the following instructions:
    ## Heat to 98c and wait 10 seconds
    ## Cool to 60c and wait 30 seconds ## Heat to 72c and wait 30 seconds
    Cycling_Profile = [
        {"temperature": 98, "hold_time_seconds": 10},
        {"temperature": 60, "hold_time_seconds": 30},
        {"temperature": 72, "hold_time_seconds": 30},
    ]
    # The final profile tells the thermocycler to heat to 72c and wait 120 seconds
    Final_Extension_Profile = [{"temperature": 72, "hold_time_seconds": 120}]
    # The code below passes the profiles defined above to the thermocycler,
    # and specifies how many times the profile should be repeated
    # The volume of liquid in each well is also specified
    ## This helps the thermocycler ensure that the entire contents of the wells ## are heated/cooled fully
    Thermocycler.execute_profile(
        steps=Initial_Denaturation_Profile, repetitions=1, block_max_volume=50
    )
    Thermocycler.execute_profile(
        steps=Cycling_Profile, repetitions=35, block_max_volume=50
    )
    Thermocycler.execute_profile(
        steps=Final_Extension_Profile, repetitions=1, block_max_volume=50
    )
    # Once the thermocycling has completed, set the temperature of the thermocycler block
    # and lid so that the reactions can be stored until the user retrieves them
    Thermocycler.set_block_temperature(4)
    Thermocycler.set_lid_temperature(37)
    # Pause the protocol with a message until ready to get samples
    protocol.pause("Click continue to open the thermocycler and retrieve samples")
    
    # Open the lid of the thermocycler so the samples can be retrieved
    Thermocycler.open_lid()


protocol = simulate.get_protocol_api('2.11')
run(protocol)

for line in protocol.commands():
    print(line)
