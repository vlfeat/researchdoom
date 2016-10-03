function cocodoomGen(varargin)
%COCODOOMGEN
opts.dataDir = 'data' ;
opts = vl_argparse(opts, varargin) ;

jobs = struct ;
t = 0 ;
for run = 1:3
  for map = 1:32
    t = t + 1 ;
    jobs(t).run = run ;
    jobs(t).map = map ;
  end
end

parfor i=1:numel(jobs)
  fprintf('### run%d map%d\n',jobs(i).run,jobs(i).map) ;
  runName = sprintf('run%d', jobs(i).run) ;
  cocodoomMake(fullfile(opts.dataDir, 'cocodoom-raw', runName), ...
               fullfile(opts.dataDir, 'cocodoom'), ...
               'runId', jobs(i).run, 'runName', runName, 'maps', jobs(i).map) ;
end
