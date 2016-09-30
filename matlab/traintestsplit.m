% This script will split the data into training validation and test

addpath coco/MatlabAPI

dataPath = '../datasetCOCOBig' ;
coco = CocoApi(fullfile(dataPath,'anno2.json')) ;
imageIds = coco.getImgIds() ;

fs1train = fopen(fullfile('..', 'trainvaltest', 'split1_train.txt'), 'w');
fs1val = fopen(fullfile('..', 'trainvaltest', 'split1_val.txt'), 'w');
fs1test = fopen(fullfile('..', 'trainvaltest', 'split1_test.txt'), 'w');

fs2train = fopen(fullfile('..', 'trainvaltest', 'split2_train.txt'), 'w');
fs2val = fopen(fullfile('..', 'trainvaltest', 'split2_val.txt'), 'w');
fs2test = fopen(fullfile('..', 'trainvaltest', 'split2_test.txt'), 'w');

for t = 1:numel(imageIds)
  imageId = imageIds(t) ;
  imageInfo = coco.loadImgs(imageId) ;
  annoIds = coco.getAnnIds('imgIds', imageId) ;
  annos = coco.loadAnns(annoIds) ;  
  
  tokens = regexp(imageInfo.file_name, '([\d\w]+)/([\d\w]+)/([\d\w]+)/([\d\w]+).png','tokens');
  runName = tokens{1}{1};
  mapName = tokens{1}{2};
  rgb = tokens{1}{3};
  imgName = tokens{1}{4};
  
  if(strcmp(runName, 'run2'))
      fprintf(fs1test, '%d\n', imageId);
  elseif(strcmp(runName, 'run3'))
      fprintf(fs1val, '%d\n', imageId);
  else
      fprintf(fs1train, '%d\n', imageId);
  end
  
  mapNum = sscanf(mapName, 'map%d');
  if(mod(mapNum, 2) == 0)
      fprintf(fs2train, '%d\n', imageId);
  elseif(mod(mapNum, 3) == 0)
      fprintf(fs2val, '%d\n', imageId);
  else
      fprintf(fs2test, '%d\n', imageId);
  end
end

fclose(fs1train);
fclose(fs2train);
fclose(fs1val);
fclose(fs2val);
fclose(fs1test);
fclose(fs2test);
