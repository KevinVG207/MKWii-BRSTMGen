# MKWii race BRSTM generator.
# Author: KevinVG207
# Version: 1.0.0
# Info/usage: https://github.com/KevinVG207/MKWii-BRSTMGen
import os
import sys
import json
import math
import shutil
import subprocess

# You may edit these parameters
FAST_PITCH_SEMITONES_UP = 2  # Default: 2
FAST_SPEED_MULTI = 1.1  # Default: 1.1
SAMPLE_RATE = 32000  # Default: 32000
MAKE_FINAL_LAP = True
VERBOSE_LOG = False


if sys.platform == 'win32':
    TONAME = r'\\.\pipe\ToSrvPipe'
    FROMNAME = r'\\.\pipe\FromSrvPipe'
    EOL = '\r\n\0'
else:
    print("This script currently is only supported on Windows.\nPlease manually edit the script and test it on your own system.\nExiting...")
    sys.exit(1)
    # TONAME = '/tmp/audacity_script_pipe.to.' + str(os.getuid())
    # FROMNAME = '/tmp/audacity_script_pipe.from.' + str(os.getuid())
    # EOL = '\n'

TOFILE = None
FROMFILE = None
CWD = os.getcwd()

def main():
    global TOFILE, FROMFILE
    exception = None
    try:
        TOFILE = open(TONAME, 'w', encoding='utf-8')
        FROMFILE = open(FROMNAME, 'r', encoding='utf-8')
        run()
    except Exception as e:
        exception = e
    finally:
        if TOFILE:
            TOFILE.close()
        if FROMFILE:
            FROMFILE.close()
    
    if exception:
        raise exception

def run():
    print("Getting information from Audacity.")
    tracks = do_command_json('GetInfo: Type=Tracks')
    wave_tracks = [track for track in tracks if track['kind'] == 'wave']
    print(f"Setting sample rate to {SAMPLE_RATE}.")
    do_command(f"SetProject: Rate={SAMPLE_RATE}")

    loop_start_sample, loop_end_sample = get_loop_points(wave_tracks)
    print(f"Loop start: {loop_start_sample}, Loop end: {loop_end_sample}")

    print(f"Exporting {len(wave_tracks)} audio tracks.")
    out_paths = []
    for i in range(len(tracks)):
        if tracks[i]['kind'] != 'wave':
            continue
        out_path = f"{CWD}\\{i}.wav"
        out_paths.append(out_path)
        print_debug(f"Exporting track {i} to {out_path}")
        export_track(i, loop_end_sample / SAMPLE_RATE, out_path)
    
    normal_out_path = f"{CWD}\\output\\output_n.brstm"
    fast_out_path = f"{CWD}\\output\\output_f.brstm"
    os.makedirs(os.path.dirname(normal_out_path), exist_ok=True)

    print("Converting to BRSTM. (VGAudio)")
    convert_vgaudio(out_paths, normal_out_path, loop_start_sample, loop_end_sample)

    # TODO: Speed up inside Audacity and use VGAudio? (Audacity speed/pitch up takes too long!)
    if MAKE_FINAL_LAP:
        print("Creating final lap BRSTM. (LoopingAudioConverter)")
        create_fast_brstm(normal_out_path, fast_out_path)

    print("Cleaning up.")
    for path in out_paths:
        os.remove(path)

    print("Done!")

# def speed_up_tracks(tracks, end_sample):
#     end_time = end_sample / SAMPLE_RATE + 1
#     do_command(f"Select: Start=0 End={end_time} RelativeTo=ProjectStart Track=0 TrackCount={len(tracks)} Mode=Set")
#     do_command(f"ChangeSpeedAndPitch: Percentage={SPEED_UP_PERCENTAGE}")
#     do_command(f"Undo:")


def get_loop_points(tracks):
    loop_start_sample = 0
    loop_end_sample = 0

    labels = do_command_json('GetInfo: Type=Labels')

    for track in labels:
        for label in track[1]:
            name = label[2].lower()
            if name in ['start', 's'] or loop_start_sample == 0:
                loop_start_sample = label[0] * SAMPLE_RATE
            elif name in ['end', 'e'] or loop_end_sample == 0:
                loop_end_sample = label[0] * SAMPLE_RATE
    
    if loop_end_sample == 0:
        loop_end_sample = max([track['end'] if 'end' in track else 0 for track in tracks]) * SAMPLE_RATE - 1
    
    return math.floor(loop_start_sample), math.floor(loop_end_sample)

def convert_vgaudio(in_paths, out_path, loop_start_sample=0, loop_end_sample=-1):
    in_paths_str = " ".join([f'-i "{path}"' for path in in_paths])
    command = f"VGAudioCli.exe {in_paths_str} {out_path} -l {loop_start_sample}-{loop_end_sample} --out-format gd-adpcm"
    print_debug(command)
    call_subprocess(command)
    # os.system(command)

def create_fast_brstm(in_path, out_path):
    tmp_folder = f"{CWD}\\tmp"
    tmp_output = tmp_folder + f"\\{os.path.basename(in_path)}"
    tmp_xml_path = tmp_folder + "\\lac.xml"

    os.makedirs(tmp_folder, exist_ok=True)

    xml = LAC_XML_TEMPLATE \
        .replace("{OUTPUT_DIR}", tmp_folder) \
        .replace("{FAST_PITCH_SEMITONES_UP}", str(FAST_PITCH_SEMITONES_UP)) \
        .replace("{FAST_SPEED_MULTI}", str(FAST_SPEED_MULTI))

    with open(tmp_xml_path, "w", encoding='utf-8') as f:
        f.write(xml)
    
    command = f'LoopingAudioConverter "{tmp_xml_path}" "{in_path}" --auto'
    call_subprocess(command)
    # os.system(command)

    shutil.copy(tmp_output, out_path)
    shutil.rmtree(tmp_folder)

def call_subprocess(command):
    if VERBOSE_LOG:
        print(command)
        subprocess.call(command, shell=True)
    else:
        subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def select_track(index):
    do_command(f'Select: Track={index} Mode=Set')

def export_track(index, end, out_path):
    do_command(f"Select: Start=0 End={end} RelativeTo=ProjectStart Track={index} Mode=Set")
    do_command(f"SetTrack: Mute=0")
    do_command(f'Export2: Filename="{out_path}" NumChannels=2')


def do_command(command):
    """Send one command, and return the response."""
    _send_command(command)
    response = _get_response()
    print_debug("=== RESPONSE ===")
    print_debug(response)
    print_debug("===")
    return response

def do_command_json(command):
    a = do_command(command)
    b = a.replace("\r\n", "\n").rsplit("\n", 2)[0]
    return json.loads(b)

def _send_command(command):
    """Send a single command."""
    print_debug("Send: >>> \n"+command)
    TOFILE.write(command + EOL)
    TOFILE.flush()

def _get_response():
    """Return the command response."""
    result = ''
    line = ''
    while True:
        result += line
        line = FROMFILE.readline()
        if line == '\n' and len(result) > 0:
            break
    return result

def print_debug(*args, **kwargs):
    if VERBOSE_LOG:
        print(*args, **kwargs)

LAC_XML_TEMPLATE = """<?xml version="1.0"?>
<Options xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <OutputDir>{OUTPUT_DIR}</OutputDir>
  <InputDir />
  <Channels xsi:nil="true" />
  <SampleRate xsi:nil="true" />
  <AmplifydB xsi:nil="true" />
  <AmplifyRatio xsi:nil="true" />
  <PitchSemitones>{FAST_PITCH_SEMITONES_UP}</PitchSemitones>
  <TempoRatio>{FAST_SPEED_MULTI}</TempoRatio>
  <DefaultInputDuration />
  <ChannelSplit>OneFile</ChannelSplit>
  <ExporterType>VGAudio_BRSTM</ExporterType>
  <AACEncodingParameters />
  <OggVorbisEncodingParameters />
  <MP3FFmpegParameters />
  <AACFFmpegParameters />
  <AdxOptions>
    <TrimFile>true</TrimFile>
    <Version>4</Version>
    <FrameSize>18</FrameSize>
    <Filter>2</Filter>
    <Type>Linear</Type>
    <EncryptionType>None</EncryptionType>
    <KeyCode xsi:nil="true" />
  </AdxOptions>
  <HcaOptions>
    <TrimFile>true</TrimFile>
    <Quality>NotSet</Quality>
    <LimitBitrate>false</LimitBitrate>
    <Bitrate>0</Bitrate>
    <KeyCode xsi:nil="true" />
  </HcaOptions>
  <BxstmOptions>
    <TrimFile>true</TrimFile>
    <RecalculateSeekTable>true</RecalculateSeekTable>
    <RecalculateLoopContext>true</RecalculateLoopContext>
    <SamplesPerInterleave>14336</SamplesPerInterleave>
    <SamplesPerSeekTableEntry>14336</SamplesPerSeekTableEntry>
    <LoopPointAlignment>14336</LoopPointAlignment>
    <Codec>GcAdpcm</Codec>
    <Endianness xsi:nil="true" />
    <Version>
      <UseDefault>true</UseDefault>
      <Major>0</Major>
      <Minor>0</Minor>
      <Micro>0</Micro>
      <Revision>0</Revision>
    </Version>
    <TrackType>Standard</TrackType>
    <SeekTableType>Standard</SeekTableType>
  </BxstmOptions>
  <WaveEncoding>PCM8</WaveEncoding>
  <InputLoopBehavior>ForceLoop</InputLoopBehavior>
  <ExportWholeSong>true</ExportWholeSong>
  <WholeSongExportByDesiredDuration>false</WholeSongExportByDesiredDuration>
  <WholeSongSuffix />
  <NumberOfLoops>1</NumberOfLoops>
  <DesiredDuration>900</DesiredDuration>
  <FadeOutSec>0</FadeOutSec>
  <ExportPreLoop>false</ExportPreLoop>
  <PreLoopSuffix> (beginning)</PreLoopSuffix>
  <ExportLoop>false</ExportLoop>
  <LoopSuffix> (loop)</LoopSuffix>
  <ExportPostLoop>false</ExportPostLoop>
  <PostLoopSuffix> (end)</PostLoopSuffix>
  <ExportLastLap>false</ExportLastLap>
  <LastLapSuffix> (final lap)</LastLapSuffix>
  <BypassEncoding>false</BypassEncoding>
</Options>"""

if __name__ == "__main__":
    main()
