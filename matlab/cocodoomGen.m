function cocodoomGen(varargin)
%COCODOOMGEN
opts.dataDir = 'data' ;
opts = vl_argparse(opts, varargin) ;

for run = 1:3
  runName = sprintf('run%d',run) ;
  cocodoomMake(fullfile(opts.dataDir, 'cocodoom-raw', runName), ...
               fullfile(opts.dataDir, 'cocodoom'), ...
               'runId', run, 'runName', runName) ;
end
