export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
D=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3_scripts
for c in current_reuse_telescopic_ota folded_cascode two_stage_ota nmcnr_amplifier; do
  s=$(date +%s); C:/Python314/python.exe -B -P $D/p3v82_relaxed_reach.py C:/g135/iso_r $c C:/g135/out_reach/$c.json >> C:/g135/out_reach/log.txt 2>&1; echo "$c exit=$? t=$(( $(date +%s)-s ))s" >> C:/g135/out_reach/log.txt
done
echo DONE >> C:/g135/out_reach/log.txt
