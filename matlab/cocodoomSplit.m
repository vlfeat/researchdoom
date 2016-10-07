function cocodoomSplit()
%COCODOOMSPLIT   Generate standard Cocodoom splits.

addpath matlab ;
addpath matlab/coco/MatlabAPI ;
full = {} ;
standard = {} ;

% Copy meta data
for r = 1:3
  copyfile(sprintf('data/cocodoom-raw/run%d/log.txt',r), ...
           sprintf('data/cocodoom/run%d/log.txt',r)) ;
end


% --------------------------------------------------------------------
% Get player splits
% --------------------------------------------------------------------
train = {} ;
val = {} ;
test = {} ;
for run = 1:3
  for map = 1:32
    str = sprintf('data/cocodoom/run%d/map%02d/coco.json',run,map) ;
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
standard{end+1} = cocodoomCombine(train, 'data/cocodoom/run-train.json', 'skip', 5) ;
coco = CocoApi('data/cocodoom/run-train.json') ;
cats = coco.loadCats(coco.getCatIds()) ;
for c = 1:numel(cats)
  annId = coco.getAnnIds('catIds', cats(c).id) ;
  numInstances(c) = numel(annId) ;
end
selCats = [cats(find(numInstances >= 100)).id] ;
fprintf('Selected %d categories out of %d\n', numel(selCats), numel(numInstances)) ;

standard{end+1} = cocodoomCombine(train, 'data/cocodoom/run-train.json', 'skip', 5, 'categories', selCats) ;
standard{end+1} = cocodoomCombine(val,   'data/cocodoom/run-val.json',   'skip', 20, 'categories', selCats) ;
standard{end+1} = cocodoomCombine(test,  'data/cocodoom/run-test.json',  'skip', 20, 'categories', selCats) ;

full{end+1} = cocodoomCombine(train, 'data/cocodoom/run-full-train.json', 'categories', selCats) ;
full{end+1} = cocodoomCombine(val,   'data/cocodoom/run-full-val.json', 'categories', selCats) ;
full{end+1} = cocodoomCombine(test,  'data/cocodoom/run-full-test.json', 'categories', selCats) ;

% --------------------------------------------------------------------
% Get map splits
% --------------------------------------------------------------------
train = {} ;
val = {} ;
test = {} ;
for run = 1:3
  for map = 1:32
    str = sprintf('data/cocodoom/run%d/map%02d/coco.json',run,map) ;
    if mod(map-1,4) <= 1
      train = horzcat(train, str) ;
    elseif mod(map-1,4) == 2
      val = horzcat(val, str) ;
    else
      test = horzcat(test, str) ;
    end
  end
end

standard{end+1} = cocodoomCombine(train, 'data/cocodoom/map-train.json', 'skip', 5, 'categories', selCats) ;
standard{end+1} = cocodoomCombine(val,   'data/cocodoom/map-val.json',   'skip', 20, 'categories', selCats) ;
standard{end+1} = cocodoomCombine(test,  'data/cocodoom/map-test.json',  'skip', 20, 'categories', selCats) ;

full{end+1} = cocodoomCombine(train, 'data/cocodoom/map-full-train.json', 'categories', selCats) ;
full{end+1} = cocodoomCombine(val,   'data/cocodoom/map-full-val.json', 'categories', selCats) ;
full{end+1} = cocodoomCombine(test,  'data/cocodoom/map-full-test.json', 'categories', selCats) ;


standard = strjoin(unique(horzcat(standard{:})),'\n') ;
full = strjoin(unique(horzcat(full{:})),'\n') ;

writeText('data/cocodoom/images.txt', standard) ;
writeText('data/cocodoom/images-full.txt', full) ;
