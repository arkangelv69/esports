#!/bin/bash

cat download/downloadedFile.html | sed -E 's/MarketSubGroup_Label[ "=style]+>([a-zA-Z0-9\ -:\!]+)</_ROBOT-Torneo:\1_/g' | sed -E 's/Participant_Name">([a-zA-Z0-9\ \!-]+)/_ROBOT-Equipo:\1_/g' | sed -E 's/Participant_Odds">([0-9\ \.]+)/_ROBOT-odds:\1_/g' | tr '_' '\n' | grep -e "ROBOT" | awk -f parser.awk