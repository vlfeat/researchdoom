function cocodoomSplit(varargin)
%COCODOOMSPLIT   Generate standard Cocodoom splits.
opts = cocodoomPaths() ;
opts = vl_argparse(opts, varargin) ;

addpath matlab ;
addpath('matlab/coco/MatlabAPI', '-end') ;
full = {} ;
standard = {} ;

% Copy meta data
for r = 1:3
  copyfile(fullfile(opts.rawDataDir, sprintf('run%d', r), 'log.txt'), ...
           fullfile(opts.dataDir, sprintf('run%d', r), 'log.txt')) ;
end


% --------------------------------------------------------------------
% Get player splits
% --------------------------------------------------------------------
train = {} ;
val = {} ;
test = {} ;
for run = 1:3
  for map = 1:32
    str = fullfile(opts.dataDir, sprintf('run%d', run), sprintf('map%02d', map), 'coco.json') ;
    if ~exist(str, 'file'), continue ; end
    switch run
      case 1
        train = horzcat(train, str) ;
      case 2
        val = horzcat(val, str) ;
      case 3
        test = horzcat(test, str) ;
    end
  end
end

% Get statistics
standard{end+1} = cocodoomCombine(train, fullfile(opts.dataDir, 'run-train.json'), 'skip', 5) ;
coco = CocoApi(fullfile(opts.dataDir, 'run-train.json')) ;
cats = coco.loadCats(coco.getCatIds()) ;
for c = 1:numel(cats)
  annId = coco.getAnnIds('catIds', cats(c).id) ;
  numInstances(c) = numel(annId) ;
end
selCats = [cats(find(numInstances >= 100)).id] ;
fprintf('Selected %d categories out of %d\n', numel(selCats), numel(numInstances)) ;

standard{end+1} = cocodoomCombine(train, fullfile(opts.dataDir, 'run-train.json'), 'skip', 5, 'categories', selCats) ;
standard{end+1} = cocodoomCombine(val,   fullfile(opts.dataDir, 'run-val.json'),   'skip', 20, 'categories', selCats) ;
standard{end+1} = cocodoomCombine(test,  fullfile(opts.dataDir, 'run-test.json'),  'skip', 20, 'categories', selCats) ;

full{end+1} = cocodoomCombine(train, fullfile(opts.dataDir, 'run-full-train.json'), 'categories', selCats) ;
full{end+1} = cocodoomCombine(val,   fullfile(opts.dataDir, 'run-full-val.json'), 'categories', selCats) ;
full{end+1} = cocodoomCombine(test,  fullfile(opts.dataDir, 'run-full-test.json'), 'categories', selCats) ;

% --------------------------------------------------------------------
% Get map splits
% --------------------------------------------------------------------
train = {} ;
val = {} ;
test = {} ;
for run = 1:3
  for map = 1:32
    str = fullfile(opts.dataDir, sprintf('run%d', run), sprintf('map%02d', map), 'coco.json') ;
    if mod(map-1,4) <= 1
      train = horzcat(train, str) ;
    elseif mod(map-1,4) == 2
      val = horzcat(val, str) ;
    else
      test = horzcat(test, str) ;
    end
  end
end

standard{end+1} = cocodoomCombine(train, fullfile(opts.dataDir, 'map-train.json'), 'skip', 5, 'categories', selCats) ;
standard{end+1} = cocodoomCombine(val,   fullfile(opts.dataDir, 'map-val.json'),   'skip', 20, 'categories', selCats) ;
standard{end+1} = cocodoomCombine(test,  fullfile(opts.dataDir, 'map-test.json'),  'skip', 20, 'categories', selCats) ;

full{end+1} = cocodoomCombine(train, fullfile(opts.dataDir, 'map-full-train.json'), 'categories', selCats) ;
full{end+1} = cocodoomCombine(val,   fullfile(opts.dataDir, 'map-full-val.json'), 'categories', selCats) ;
full{end+1} = cocodoomCombine(test,  fullfile(opts.dataDir, 'map-full-test.json'), 'categories', selCats) ;


standard = strjoin(unique(horzcat(standard{:})),'\n') ;
full = strjoin(unique(horzcat(full{:})),'\n') ;

writeText(fullfile(opts.dataDir, 'images.txt'), standard) ;
writeText(fullfile(opts.dataDir, 'images-full.txt'), full) ;
