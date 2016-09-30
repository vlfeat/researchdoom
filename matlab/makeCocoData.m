function makeCocoData(runName, runId)
% Some of the pahts are hardcoded below.
% Please download vlfeat and put the path to the vl_setup file below.
% The data is assumed to be inside  ../dataset/<runName> where runName is the input argument
% Please change it below if you have saved it elsewhere.


run vlfeat/toolbox/vl_setup ; % Hardcoded path

outPrefix = fullfile('..', 'datasetCOCOBig') ; % Hardcoded path
vl_xmkdir(outPrefix) ;


runIdName = sprintf('run%d', runId);

% for runId = 1:numel(runNames)
  rdmPath = fullfile('..', 'dataset', runName); % Hardcoded path
  rdb = rdmLoad(rdmPath) ;
  
  % Get object categories.
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
  
  txt = sprintf('%s', strjoin(catTxt,',')) ;

  f = fopen(fullfile(outPrefix, runIdName, 'categories.json'),'w') ;
  fwrite(f,txt) ;
  fclose(f) ;
  
  % Break run in levels.
  for levelId = 1:numel(rdb.levels.name)
    levelName = rdb.levels.name{levelId} ;
    qualPath = fullfile(runIdName, levelName) ;
    vl_xmkdir(fullfile(outPrefix, qualPath, 'rgb')) ;
    vl_xmkdir(fullfile(outPrefix, qualPath, 'depth')) ;
    vl_xmkdir(fullfile(outPrefix, qualPath, 'objects')) ;
     
    ticStart = rdb.levels.startTic(levelId) ;
    ticEnd = rdb.levels.endTic(levelId) ;
    tics = [rdb.ticks.id] ;
    tics = tics(ticStart <= tics & tics <= ticEnd) ;
    
    imageTxt = {} ;
    annoTxt = {} ;
    % Get frames.
    for tic = tics
      frame = rdmGetFrame(rdb, tic) ;
%       clf ; 
%       subplot(1,2,1);imagesc(ind2rgb(frame.rgb,frame.rgbcols))
%       subplot(1,2,2);imagesc(frame.depthmap) ; drawnow ;
%       pause
      imageId = 10e8 * runId + 10e6 * levelId + tic ;
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
        imageId, fullfile(qualPath, 'rgb', imageName), datetime);
      
      imwrite_if_notexist(frame.rgb,double(frame.rgbcols),fullfile(outPrefix,qualPath,'rgb',imageName)) ;
      imwrite_if_notexist(frame.depthmap, [], fullfile(outPrefix,qualPath,'depth',imageName)) ;
      imwrite_if_notexist(frame.objectmap,[], fullfile(outPrefix,qualPath,'objects',imageName)) ;
      
      for i = 1:numel(frame.objects.id)
        mask = (frame.objectmap == frame.objects.frameId(i)) ;
        mask = imfill(mask,'holes') ;
        area = sum(mask(:)) ;
        maskUp = imresize(mask,4,'nearest') ;
        poly = contourc(double(maskUp),[.5 .5]) ;
        polyTxt = {} ;
        polyBegin = 1 ;
        while polyBegin < size(poly,2)
          polyLength = poly(2,polyBegin) ;
          polyEnd = polyBegin + polyLength ;
          onePoly = (poly(:,polyBegin+1:polyEnd)-2.5)/4+1 ;
          onePoly = round(onePoly + .5) - .5 ;
          %clf ; imagesc(mask);axis equal ;hold on; plot(onePoly(1,2:end),onePoly(2,2:end),'rx-') ;
          onePoly = dpsimplify(onePoly',1)' ;
          txt = cellfun(@(x)sprintf('%.0f',x),num2cell(onePoly(:)-0.5),'uniformoutput',0) ;
          polyTxt{end+1} = sprintf('[%s]',strjoin(txt,',')) ;
          polyBegin = polyEnd + 1 ;
        end
        polyTxt = sprintf('[%s]',strjoin(polyTxt,',')) ;
        box = frame.objects.box(:,i)-1 ;
        annoTxt{end+1} = sprintf([...
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
            runName, levelId, numel(rdb.levels.name), ...
            tic, max(tics));
    end
    txt = sprintf('%s', strjoin(imageTxt,',')) ;

    f = fopen(fullfile(outPrefix, qualPath, 'images.json'),'w') ;
    fwrite(f,txt) ;
    fclose(f) ;
    
    txt = sprintf('%s', strjoin(annoTxt,',')) ;

    f = fopen(fullfile(outPrefix, qualPath, 'anno.json'),'w') ;
    fwrite(f,txt) ;
    fclose(f) ;
  end
% end

infoTxt = sprintf([...
  '{' ...
  '"year":2016,' ...
  '"version":1,', ...
  '"description":"ResearchDoom",' ...
  '"contributor":"VGG",' ...
  '"url":"",' ...
  '"date_created":"%s"}'], ...
  datetime) ;
licenseTxt = '{"id":1,"name":"rdoom","url":""}' ;
txt = sprintf('{"info":%s,"licenses":[%s]}', infoTxt, licenseTxt) ;

f = fopen(fullfile(outPrefix, 'core.json'),'w') ;
fwrite(f,txt) ;
fclose(f) ;


function imwrite_if_notexist(image, index, name)
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
