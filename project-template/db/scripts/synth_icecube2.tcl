#!/usr/bin/env tclsh
# synth_icecube2.tcl — iCEcube2 SBT 배치 빌드 TCL 스크립트
#
# 사용법:
#   tclsh synth_icecube2.tcl                 # Phase 1: synth → route → timer
#   tclsh synth_icecube2.tcl --bitmap-only   # Phase 2: bitmap → copy
#
# build_icecube2.sh 가 Phase 1 → 타이밍 확인 → 사용자 승인 → Phase 2 순으로 호출
#
# 이 스크립트는 build_icecube2.sh 에서 호출됨
#
# ════════════════════════════════════════════════════════════
# FILL GUIDE — 이 블록을 따른 뒤 삭제 (# ==== 라인 포함)
# [1] {{PROJECT_NAME}} (2곳: top_module, base_name 변수) → 레포 base 이름
# [2] device / package (아래 "프로젝트 설정" 섹션) → 실제 디바이스·패키지
#     (install.py --detect-config 가 iCE40 감지 시 자동 채움; 수동 설치 시 직접 수정)
# ════════════════════════════════════════════════════════════

# ── 인자 처리 ────────────────────────────────────────────────
set bitmap_only 0
foreach arg $argv {
    if {$arg eq "--bitmap-only"} {
        set bitmap_only 1
    }
}

if {[info exists env(PROJECT_ROOT)]} {
    set project_root $env(PROJECT_ROOT)
} else {
    set project_root [file normalize [file join [file dirname [info script]] "../.."]]
}

if {[info exists env(ICECUBE2_PATH)]} {
    set sbt_root $env(ICECUBE2_PATH)
} else {
    set sbt_root "C:/lscc/iCEcube2.2020.12"
}

# ── 프로젝트 설정 ────────────────────────────────────────────
set device      "iCE5LP4K"
set package     "SWG36"
set top_module  "{{PROJECT_NAME}}_top"
set base_name   "{{PROJECT_NAME}}"

# external_device_name: SBT API가 요구하는 "디바이스-패키지" 형식
set external_device_name "${device}-${package}"

set proj_dir    [file join $project_root "db/work/$base_name"]
set impl_subdir "$base_name_Implmnt"
set impl_dir    [file join $proj_dir $impl_subdir]
set syn_project [file join $proj_dir "$base_name_syn.prj"]
set img_dir     [file join $project_root "img"]

# 제약 파일 디렉토리 (PCF, SDC)
set constraint_dir [file join $project_root "db/sdc"]

# ── SBT 백엔드 도구 경로 ─────────────────────────────────────
set sbt_backend "$sbt_root/sbt_backend"
set sbt_bin "$sbt_backend/bin"
if {$::tcl_platform(platform) eq "windows"} {
    set sbt_bin "$sbt_bin/win32/opt"
} else {
    set sbt_bin "$sbt_bin/linux/opt"
}

# SBT_DIR 환경변수 설정 (SBT TCL API가 참조)
set ::env(SBT_DIR) $sbt_backend

# ── 헬퍼 ─────────────────────────────────────────────────────
proc log_step {msg} {
    puts "==== \[iCEcube2\] $msg ===="
}

proc run_cmd {desc cmd} {
    log_step $desc
    puts "CMD: $cmd"
    set rc [catch {exec {*}$cmd} result]
    if {$rc != 0} {
        puts stderr "FAILED: $desc"
        puts stderr $result
        exit 1
    }
    puts $result
    return $result
}

# ── SBT 공식 TCL 스크립트 로드 ───────────────────────────────
set sbt_tcl_dir [file join $sbt_backend "tcl"]
source [file join $sbt_tcl_dir "sbt_backend_synpl_top.tcl"]

# SBT API 필수 변수
set sbt_debug 0
set sbt_show_error 1

# iCEcube2 버그 패치: sbt_run_edifparser_ip 에 --devicename 누락
rename sbt_run_edifparser_ip sbt_run_edifparser_ip_orig
proc sbt_run_edifparser_ip { top_name option external_device_name output_dir ip_file sdc_file mtcl_file pcf_file {edif_switch ""} {edif_file ""} } {
    upvar sbt_debug sbt_debug
    upvar sbt_show_error sbt_show_error

    set toolName edifparser
    set tool_path [sbt_get_tool_dir]
    set device_file [sbt_device_file $external_device_name]
    set sbt_netlist_dir [sbt_netlist_dir $output_dir]
    set package_name [sbt_parse_package_name $external_device_name]
    set edif_option [sbt_parse_option $option "edifparser"]
    set sbt_dir [sbt_get_sbt_dir]

    set deviceName_tmp [split $external_device_name "-"]
    set DeviceName [lindex $deviceName_tmp 0]
    set softRGBIP "$sbt_dir/devices/ipfiles/iCE5LP/rgbsoft.edf"
    if {[string first "iCE5LP" $DeviceName] == 0 && [file exists $softRGBIP]} {
        append edif_file " $softRGBIP "
    }

    set command "{$tool_path/$toolName} {$device_file} {$edif_file} {$sbt_netlist_dir} $edif_switch "
    if {[string length $ip_file] >= 1} {
        append command " -i {$ip_file} "
    }
    if {[string length $sdc_file] >= 1} {
        append command " -s {$sdc_file} "
    }
    if {[string length $mtcl_file] >= 1} {
        append command " -m {$mtcl_file} "
    }
    if {[string length $pcf_file] >= 1} {
        append command " -y {$pcf_file} "
    }

    if {[string length $edif_switch] < 1} {
        append command " --package {$package_name} $edif_option --devicename $DeviceName"
    }

    if {![sbt_run_command $command $toolName]} {
        return -1
    }

    return 0
}

# ── 출력 디렉토리 생성 ───────────────────────────────────────
file mkdir $impl_dir
file mkdir $img_dir

# ======================================================================
#  Phase 2: --bitmap-only  (bitmap → netlister → copy)
# ======================================================================
if {$bitmap_only} {
    log_step "Phase 2: Bitmap Generation"

    set output_dir [sbt_output_dir $proj_dir $impl_subdir]

    # bitmap
    if {[sbt_run_bitmap $top_module $external_device_name $output_dir ""]} {
        puts stderr "ERROR: Bitmap generation failed"
        exit 1
    }

    # verilog netlister (시뮬레이션용)
    catch {sbt_run_verilog_netlister $top_module $external_device_name $output_dir}

    # 출력 파일 복사
    log_step "Copying output to $img_dir"
    set bitmap_dir [file join $output_dir "sbt/outputs/bitmap"]

    foreach search_dir [list $bitmap_dir $output_dir] {
        foreach pattern {"*.bin" "*.hex" "*.nvcm"} {
            foreach f [glob -nocomplain [file join $search_dir $pattern]] {
                set dest [file join $img_dir [file tail $f]]
                file copy -force $f $dest
                puts "  $f -> $dest"
            }
        }
    }

    log_step "Bitmap complete"
    puts "Output files in: $img_dir"
    exit 0
}

# ======================================================================
#  Phase 1: Synth → Edifparser → Placer → Packer → Router → Timer
# ======================================================================

# ── Step 1: Synplify Pro 합성 ─────────────────────────────────
log_step "Synthesis (Synplify Pro)"
set synpwrap "$sbt_bin/synpwrap/synpwrap"
if {[file exists "${synpwrap}.exe"]} {
    set synpwrap "${synpwrap}.exe"
}

run_cmd "Running Synplify Pro" [list $synpwrap -prj $syn_project -log [file join $impl_dir "synth.log"]]

set edif_file [file join $impl_dir "${base_name}.edf"]
if {![file exists $edif_file]} {
    puts stderr "ERROR: Synthesis output not found: $edif_file"
    exit 1
}
log_step "Synthesis complete: $edif_file"

# ── Step 2: SBT Backend (개별 단계 호출) ─────────────────────
log_step "SBT Backend — Phase 1 (Route + Timer)"

set option ""

# --- init ---
sbt_init_env

if {[sbt_init_dirs $proj_dir $impl_subdir]} {
    puts stderr "ERROR: Failed to create SBT directories"
    exit 1
}

set output_dir [sbt_output_dir $proj_dir $impl_subdir]

if {[sbt_create_device_info_file $output_dir $external_device_name]} {
    puts stderr "ERROR: Failed to create device info"
    exit 1
}

# --- constraint 파일 수집 ---
set sdc_file_path  "$output_dir/sbt/Temp/sbt_temp.sdc"

set ip_files ""
foreach file [glob -nocomplain -directory $constraint_dir *ip.edf] {
    if {[file exists $file]} { append ip_files $file " " }
}
set localsdc_files ""
foreach file [glob -nocomplain -directory $constraint_dir *.sdc] {
    if {[file exists $file]} { append localsdc_files $file " " }
}
set pcf_files ""
foreach file [glob -nocomplain -directory $constraint_dir *.pcf] {
    if {[file exists $file]} { append pcf_files $file " " }
}
set mtcl_files ""
foreach file [glob -nocomplain -directory $constraint_dir *.mtcl] {
    if {[file exists $file]} { append mtcl_files $file " " }
}

# --- edifparser ---
log_step "Edifparser"
set edif_for_parser "$output_dir/${base_name}.edf"
set option1 $option
set scf_file "$output_dir/${base_name}.scf"
if {[file exists $scf_file]} {
    set option ""
    append option $option1 " :edifparser -c"
}

if {[sbt_run_edifparser_ip $top_module $option $external_device_name $output_dir $ip_files $localsdc_files $mtcl_files $pcf_files "" $edif_for_parser]} {
    puts stderr "ERROR: Edifparser failed"
    exit 1
}

if {![file exists $sdc_file_path]} {
    set sdc_file_path ""
    append sdc_file_path $output_dir "/" $base_name ".scf"
}

# --- placer ---
log_step "Placer"
if {[sbt_run_placer $top_module $option $external_device_name $proj_dir $output_dir $sdc_file_path]} {
    puts stderr "ERROR: Placer failed"
    exit 1
}

# --- packer ---
log_step "Packer"
if {[sbt_run_packer $top_module $external_device_name $output_dir $base_name ""]} {
    puts stderr "ERROR: Packer failed"
    exit 1
}

# --- router ---
log_step "Router"
if {[sbt_run_router $top_module $option $external_device_name $proj_dir $output_dir]} {
    puts stderr "ERROR: Router failed"
    exit 1
}

# --- report ---
sbt_generate_report_file $top_module $output_dir

# --- netlister (timer가 _sbt.sdc 필요, netlister가 생성) ---
log_step "Netlister"
catch {sbt_run_verilog_netlister $top_module $external_device_name $output_dir}

# --- timer ---
log_step "Timer"
sbt_run_timer_utility $top_module $option $external_device_name $output_dir

# ── 타이밍 리포트 요약 출력 ──────────────────────────────────
set timing_rpt [file join $output_dir "sbt/outputs/router/${top_module}_timing.rpt"]
set sbt_sdc    [file join $output_dir "${top_module}_sbt.sdc"]

puts ""
puts "================================================================"
puts "  TIMING REPORT: $timing_rpt"
puts "  SBT SDC:       $sbt_sdc"
puts "  USER SDC:      $constraint_dir"
puts "================================================================"

# Clock Frequency Summary 파싱
if {[file exists $timing_rpt]} {
    set f [open $timing_rpt r]
    set in_freq_summary 0
    set clock_lines {}

    while {[gets $f line] >= 0} {
        if {[string match "*1::Clock Frequency Summary*" $line]} {
            set in_freq_summary 1
            continue
        }
        if {$in_freq_summary} {
            if {[string match "*===*" $line]} { continue }
            if {[string match "*Clock:*" $line]} {
                lappend clock_lines $line
            }
            if {[string match "*2::*" $line]} { break }
            if {[llength $clock_lines] > 0 && [string trim $line] eq ""} { break }
        }
    }
    close $f

    puts ""
    puts "  Clock Frequency Summary:"
    puts "  ---------------------------------------------------------------"
    foreach cl $clock_lines {
        # 주파수와 타겟 파싱
        set met "PASS"
        if {[regexp {Frequency:\s*([\d.]+)\s*MHz.*Target:\s*([\d.]+)\s*MHz} $cl -> freq target]} {
            if {$freq < $target} { set met "** FAIL **" }
        } elseif {[regexp {N/A.*Target:} $cl]} {
            set met "N/A"
        }
        puts "  $cl  $met"
    }
    puts "  ---------------------------------------------------------------"
    puts ""
}

log_step "Phase 1 complete (Route + Timer)"
puts "Bitmap generation pending — awaiting user approval."
exit 0
