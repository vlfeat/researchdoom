function cocodoomSplit()
%COCODOOMSPLIT   Generate standard Cocodoom splits.

addpath matlab ;
addpath matlab/coco/MatlabAPI ;
full = {} ;
standard = {} ;

% --------------------------------------------------------------------
% Get map splits
% --------------------------------------------------------------------
train = {} ;
val = {} ;
test = {} ;
for run = 1:1
  for map = 1:4
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

full{end+1} = cocodoomCombine(train, 'data/cocodoom/map-full-train.json') ;
full{end+1} = cocodoomCombine(val,   'data/cocodoom/map-full-val.json') ;
full{end+1} = cocodoomCombine(test,  'data/cocodoom/map-full-test.json') ;

standard{end+1} = cocodoomCombine(train, 'data/cocodoom/map-train.json', 'skip', 5) ;
standard{end+1} = cocodoomCombine(val,   'data/cocodoom/map-val.json',   'skip', 20) ;
standard{end+1} = cocodoomCombine(test,  'data/cocodoom/map-test.json',  'skip', 20) ;

% --------------------------------------------------------------------
% Get player splits
% --------------------------------------------------------------------
train = {} ;
val = {} ;
test = {} ;
for run = 1:1
  for map = 1:4
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

full{end+1} = cocodoomCombine(train, 'data/cocodoom/run-full-train.json') ;
%full{end+1} = cocodoomCombine(val,   'data/cocodoom/run-full-val.json') ;
%full{end+1} = cocodoomCombine(test,  'data/cocodoom/run-full-test.json') ;

standard{end+1} = cocodoomCombine(train, 'data/cocodoom/run-train.json', 'skip', 5) ;
%standard{end+1} = cocodoomCombine(val, 'data/cocodoom/run-val.json',   'skip', 20) ;
%standard{end+1} = cocodoomCombine(test, 'data/cocodoom/run-test.json',  'skip', 20) ;

standard = strjoin(unique(horzcat(standard{:})),'\n') ;
full = strjoin(unique(horzcat(full{:})),'\n') ;

writeText('data/cocodoom/images.txt', standard) ;
writeText('data/cocodoom/images-full.txt', full) ;