A python script for anonymizing Company of Heroes replays for the purpose of shoutcasting during tournaments.

Usage:

Download the replay_anonymizer.py file into the directory containing the COH1 replay files you want to anonymize.


replay_anonymizer.py input.rec output.rec

input.rec -> The file you want to anonymize
output.rec -> The file you want to create

Result:

The program creates a new output replay file but changes the player names to "Player 1, Player 2, etc"
The orginal names and the associated replacement are printed to console and in the log_file.log
