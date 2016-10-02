function genCocoData()
%GENCOCODATA
parpool('local',12) ;
makeCocoData('data/cocodoom-raw/run1', 'data/cocodoom', 'runId', 1, 'runName', 'run1') ;
makeCocoData('data/cocodoom-raw/run2', 'data/cocodoom', 'runId', 2, 'runName', 'run2') ;
makeCocoData('data/cocodoom-raw/run3', 'data/cocodoom', 'runId', 3, 'runName', 'run3') ;
