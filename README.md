# MKWii-BRSTMGen
BRSTMGen is a Python script that creates BRSTM files from an open Audacity project. It is effectively a pipeline that exports the audio from Audacity, and then uses VGAudioCli and LoopingAudioConverter to create the BRSTMs. See the Setup and Usage sections.

# Features
- Multi-channel BRSTM support, simply add more stereo tracks in Audacity.
- Set looping points in Audacity using labels.
- Generates both normal speed and final lap BRSTMs.
- Configurable parameters.

# Dependencies
See the Setup section for installation instructions.
- [Python 3](https://www.python.org/) (Tested on 3.13, other versions might still work.)
- [Audacity](https://www.audacityteam.org/)
- [LoopingAudioConverter](https://github.com/libertyernie/LoopingAudioConverter)
- [VGAudioCli](https://github.com/Thealexbarney/VGAudio)

# Setup
Note: Currently only Windows is supported.

1. Install [Audacity](https://www.audacityteam.org/) if you haven't already.
2. Open Audacity and go to Edit -> Preferences -> Modules and set mod-script-pipe to Enabled and click OK. (You may need to scroll down.)
3. Audacity must be closed and restarted for this change to take effect.
4. Install [Python 3](https://www.python.org/) if you haven't already. (Tested on 3.13, other versions might still work.)
5. Download the LoopingAudioConverter zip from its [latest release](https://github.com/libertyernie/LoopingAudioConverter/releases/latest).
6. Create a folder on your computer and extract the contents of the LoopingAudioConverter zip into it. This folder will be referred to as the LAC folder in the rest of this readme.
7. Download VGAudioCli.exe from its [latest release](https://github.com/Thealexbarney/VGAudio/releases/latest). **Make sure it's the Cli, not VGAudioTools!**
8. Copy VGAudioCli.exe to the LAC folder.
9. Download BRSTMGen.py from the [latest release](https://github.com/KevinVG207/MKWii-BRSTMGen/releases/latest).
10. Copy BRSTMGen.py to the LAC folder.

# Usage
When the setup is complete, usage is fairly simple, assuming you want to create standard (multi-channel) BRSTMs used for Mario Kart Wii course music. Just a few things to note about the Audacity project and running the script.
## Setting up the Audacity project
- Each stereo track becomes a stereo stream in the BRSTM. For multi-channel BRSTMs, simply add more stereo tracks.
- The loop start and end points are determined by labels. To create a label, click on the timeline and press Ctrl+B. You will see a new labels track with one label.
  - The first label (from left-to-right) will be the loop start point.
  - The second label will be the loop end point. (Not needed if you want the end point to be the end of the audio.)
  - If you already use labels for things, you may name the labels "Start", "S", "End" or "E" (case-insensitive).
  - Without labels, the BRSTM will loop from 0s to the end of the longest audio track. (Currently, it is not possible to disable looping. This may change in the future as a parameter.)
  - Labels can technically be ranges, but only the start of the range will be used for each label.
  - Order of the tracks is from top to bottom, top-most audio track is stream 1, below that is stream 2 etc.. The location of the labels is not important.
- No need to worry about resampling, running the script will set the project's sample rate to 32000 Hz (or whatever is specified in the parameter).

## Running the script
- Make sure there is only one Audacity project open, before running the script.
- Run the script by double-clicking on BRSTMGen.py or running it from the command line with Python.
- You will find the BRSTMs in a folder called "output" in the LAC folder.
- For convenience, you could create a shortcut to the script somewhere else on your computer, like the desktop.

## Adjusting script parameters
Towards the top of the script BRSTMGen.py, there are a few parameters you can adjust. The parameters are described below. (You can edit the script in any text editor, like Notepad.)
- FAST_PITCH_SEMITONES_UP (Default: 1)
  - The number of semitones to pitch up the final lap BRSTM.
- FAST_SPEED_MULTI (Default: 1.1)
  - The speed multiplier for the final lap BRSTM. (1.1 is 10% faster.)
- SAMPLE_RATE (Default: 32000)
  - The sample rate of the output BRSTMs, in Hz.
- MAKE_FINAL_LAP (Default: True)
  - Whether to create a final lap BRSTM.
- VERBOSE_LOG (Default: False)
  - Whether to print more information to the console about what the script is doing.

## Troubleshooting
- If you get an error during the LoopingAudioConverter stage, you may need to change your number formats to use . (period) as decimal separator. (Control Panel -> Clock and Region -> Change date, time, or number formats -> Additional settings -> Decimal symbol)
  - This is an issue with LAC, not with BRSTMGen.