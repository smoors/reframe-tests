ml ReFrame/4.9.1-GCCcore-14.2.0 GitPython/3.1.45-GCCcore-14.2.0

export REFRAME_HOME=$PWD
echo REFRAME_HOME=$REFRAME_HOME

if [[ $VSC_INSTITUTE_CLUSTER == "sofia" ]]; then
    MACHINE="sofia"
else
    MACHINE="brussel"
fi
export REFRAME_SOURCEPATH="/apps/$MACHINE/sources"

export RFM_CONFIG_FILES=$REFRAME_HOME/config/config.py
export RFM_PREFIX=$VSC_SCRATCH_VO_USER/hpc-reframe-tests
export RFM_OUTPUT_DIR=$RFM_PREFIX
export RFM_PERFLOG_DIR=$RFM_PREFIX/perflogs
export RFM_SAVE_LOG_FILES=true
export RFM_VERBOSE

mkdir -p $RFM_PREFIX/logs
