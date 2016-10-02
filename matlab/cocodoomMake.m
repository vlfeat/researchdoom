function cocodoomMake(rdmDir, cocoDir, varargin)
%COCODOOMMAKE   Convert ResearchDoom output to Coco
%    COCODOOMMAKE(RDMDIR, COCODIR) takes the ResearchDoom recording and converst it in
%    MS Coco format.
%
%    Arguments
%    `runName`:: dataset/<runName> should contain rgb, depth and objects and log.txt
%    `runId`:: Used to assign image ids and also the coco format uses run1, run2 folder names
%    `tickSkip`:: Integer value >= 1 - From the list of ticks we use
%        ticks(1:tickSkip:end) This is useful when somebody wants only
%        a subset of the data roughly evently spaced out.  Note that
%        this cannot be used for reducing the frame rate directly
%        because ticks aren't all numbered from 1 to n ... they skip
%        some in the middle.

opts.runId = 1 ;
opts.runName = 'run1' ;
opts.ticSkip = 1 ;
opts.useSymlinks = true ;
opts = vl_argparse(opts, varargin) ;

% Load ResearchDoom database.
fprintf('Loading ResearchDoom database %s\n', rdmDir) ;
rdb = rdmLoad(rdmDir) ;

% Prepare output directory.
mkdir(fullfile(cocoDir,opts.runName)) ;

% Break run in levels.
parfor levelId = 1:numel(rdb.levels.name)
  %levelName = rdb.levels.name{levelId} ;
  levelName = sprintf('map%02d', levelId) ;
  qualPath = fullfile(opts.runName, levelName) ;
  levelDir = fullfile(cocoDir, qualPath) ;

  if exist(fullfile(levelDir, 'coco.json'), 'file')
    fprintf('Skipping level %d because it is already there (%s)\n', ...
            levelId, fullfile(levelDir, 'coco.json')) ;
  else
    fprintf('Processing level %d\n', levelId) ;
  end

  mkdir(fullfile(levelDir, 'rgb')) ;
  mkdir(fullfile(levelDir, 'depth')) ;
  mkdir(fullfile(levelDir, 'objects')) ;

  ticStart = rdb.levels.startTic(levelId) ;
  ticEnd = rdb.levels.endTic(levelId) ;
  tics = [rdb.tics.id] ;
  tics = tics(ticStart <= tics & tics <= ticEnd) ;

  imageTxt = {} ;
  objectTxt = {} ;

  % Extract indifidual frames.
  for tic = tics(1:opts.ticSkip:end)
    frame = rdmGetFrame(rdb, tic) ;

    % Get image entry in Coco format.
    imageId = 10e8 * opts.runId + 10e6 * levelId + tic ;
    imageName = sprintf('%06d.png', tic) ;
    imageTxt{end+1} = sprintf([...
      '{' ...
      '"id":%d,' ...
      '"width":320,' ...
      '"height":200,' ...
      '"file_name":"%s",' ...
      '"license":1,' ...
      '"flickr_url":"",' ...
      '"coco_url":"",' ...
      '"date_captured":"%s"}\n'], ...
      imageId, fullfile(qualPath, 'rgb', imageName), char(datetime));

    putImage(opts, frame.rgbPath, fullfile(levelDir,'rgb',imageName)) ;
    putImage(opts, frame.depthmapPath, fullfile(levelDir,'depth',imageName)) ;
    putImage(opts, frame.objectmapPath, fullfile(levelDir,'objects',imageName)) ;

    % Extract all objects from the frame, find polygonal contour,
    % and get a string in  Coco format.
    for i = 1:numel(frame.objects.id)
      mask = (frame.objectmap == frame.objects.frameId(i)) ;
      area = sum(mask(:)) ;
      maskUp = imresize(mask, 4, 'nearest') ;
      polys = bwboundaries(maskUp, 'noholes')

      polyTxt = {} ;
      for p = 1:numel(polys)
        onePoly_ = polys{p}(:,[2 1])' ;
        onePoly = (onePoly_-2.5)/4+1 ;
        onePolySimple = dpsimplify(onePoly',0.25)' ;
        onePolySimpleRound = round(onePolySimple * 2)/2;
        onePolyVerySimple = dpsimplify(onePolySimpleRound',0.75)' ;
        if 0
          clf ; subplot(1,2,1);
          imagesc(maskUp==0) ;
          axis equal ;
          hold on;
          plot(onePoly_(1,2:end),onePoly_(2,2:end),'rx-') ;
          subplot(1,2,2) ;
          imagesc(mask) ;
          axis equal ;
          hold on;
          %plot(onePoly(1,2:end),onePoly(2,2:end),'rx-') ;
          %plot(onePolySimple(1,2:end),onePolySimple(2,2:end),'g--') ;
          %plot(onePolySimpleRound(1,2:end),onePolySimpleRound(2,2:end),'co:') ;
          plot(onePolyVerySimple(1,2:end),onePolyVerySimple(2,2:end),'wd--');
          keyboard
        end
        txt = cellfun(@(x)sprintf('%g',x), ...
                      num2cell(onePolyVerySimple(:)-0.5),'uniformoutput',0) ;
        polyTxt{end+1} = sprintf('[%s]',strjoin(txt,',')) ;
      end
      polyTxt = sprintf('[%s]',strjoin(polyTxt,',')) ;
      box = frame.objects.box(:,i)-1 ;
      objectTxt{end+1} = sprintf([...
        '{' ...
        '"id" : %d,' ...
        '"image_id" : %d,' ...
        '"category_id" : %d,' ...
        '"segmentation" : %s,' ...
        '"area" : %.0f,' ...
        '"bbox" : [%.0f %.0f %.0f %.0f],' ...
        '"iscrowd" : 0}\n'], ...
        imageId * 1e6 + frame.objects.id(i), ...
        imageId, ...
        frame.objects.label(i), ...
        polyTxt, ...
        area, ...
        box(1),box(2),box(3)-box(1)+1,box(4)-box(2)+1) ;
    end
    fprintf(1, 'Done: run %s, level: %d/%d, tic: %d/%d\n', ...
      opts.runName, levelId, numel(rdb.levels.name), ...
      tic, max(tics));
  end

  imageTxt = sprintf('%s', strjoin(imageTxt,',')) ;
  objectTxt = sprintf('%s', strjoin(objectTxt,',')) ;

  % MS Cooco object categories.
  catTxt = {};
  for c = 1:numel(rdb.classes.label)
    catTxt{end+1} = sprintf([...
      '{'...
      '"id":%d,' ...
      '"name":"%s",' ...
      '"supercategory":""}\n'], ...
      rdb.classes.label(c), ...
      rdb.classes.name{c}) ;
  end
  catTxt = sprintf('%s', strjoin(catTxt,',')) ;

  % MS Coco info.
  infoTxt = sprintf([...
    '{' ...
    '"year":2016,' ...
    '"version":1,', ...
    '"description":"ResearchDoom",' ...
    '"contributor":"VGG",' ...
    '"url":"",' ...
    '"date_created":"%s"}'], ...
    char(datetime)) ;

  % MS Coco lincense.
  licenseTxt = '{"id":1,"name":"rdoom","url":""}' ;

  % MS Coco annotation file.
  cocoTxt = sprintf(...
    '{"info":%s,"images":[%s],"annotations":[%s],"categories":[%s],"licenses":[%s]}', ...
    infoTxt, imageTxt, objectTxt, catTxt, licenseTxt) ;

  writeText(fullfile(levelDir, 'images.json'), imageTxt) ;
  writeText(fullfile(levelDir, 'objects.json'), objectTxt) ;
  writeText(fullfile(levelDir, 'categories.json'), catTxt) ;
  writeText(fullfile(levelDir, 'info.json'), infoTxt) ;
  writeText(fullfile(levelDir, 'license.json'), licenseTxt) ;
  writeText(fullfile(levelDir, 'coco.json'), cocoTxt) ;
end

function putImage(opts,src,dst)
if ~exist(dst)
  if ~ispc && opts.useSymlinks
    system(sprintf('ln -sf %s %s', fullfile(pwd,src), dst)) ;
  else
    copyfile(src, dst) ;
  end
end

function imwrite_if_notexist(image, ibndex, name)
% Write an image file if it doesn't already exist
% image - matrix of pixel values
% index - if it is an indexed image, empty otherwise
% name - filename
if(~exist(name, 'file'))
  if(~isempty(index))
    imwrite(image, index, name);
  else
    imwrite(image, name);
  end
end
