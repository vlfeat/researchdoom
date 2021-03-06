function frame = rdmGetFrame(rdb, tic, varargin)
%RDMGETFRAME   Get ResearchDoom frame information.
%   FRAME = RDMGETFRAME(RDB, TIC) extracts the information for
%   frame TIC from the ReasearchDoom database RDB.
%
%   See also: RDMLOAD().

% Copyright (c) 2016 Andrea Vedaldi

opts.layout = [1 4] ;
opts = vl_argparse(opts, varargin) ;

t = find(rdb.tics.id == tic) ;
if isempty(t), error('Tic %d not found in RDB', tic) ; end

% Figure out if data layout is basePath/rgb or basePath/map**/rgb.
mapPath = fullfile(rdb.basePath, sprintf('map%02d', rdb.tics.level(t))) ;
if exist(mapPath, 'dir')
  basePath = mapPath ;
else
  basePath = rdb.basePath ;
end

frame.rgbPath = fullfile(basePath, 'rgb', sprintf('%06d.png', tic)) ;
[frame.rgb,frame.rgbcols] = imread(frame.rgbPath) ;
frame.rgbcols = single(frame.rgbcols) ;

frame.depthmapPath = fullfile(...
  basePath, 'depth', sprintf('%06d.png', tic)) ;
frame.depthmap = imread(frame.depthmapPath) ;

frame.objectmapPath = fullfile(...
  basePath, 'objects', sprintf('%06d.png', tic)) ;
frame.objectmap = imread(frame.objectmapPath) ;
frame.objectmap = ...
    uint32(frame.objectmap(:,:,1)) + ...
    uint32(frame.objectmap(:,:,2)) * uint32(2^8) + ...
    uint32(frame.objectmap(:,:,3)) * uint32(2^16) ;

% Extract visible object identities and bounding boxes
[ids,~,map] = unique(frame.objectmap) ;
map = reshape(map, size(frame.objectmap)) ;
ids = ids' ;
eids = 1:numel(ids) ; % enumerate objects from 1 to n in this image
eids(ids >= 2^23) = 0 ; % assign id 0 to sky,walls,ground/ceiling
props = regionprops(eids(map),'basic') ;

ids = ids(1,1:numel(props)) ;
boxes = zeros(4,0,'single') ;

if numel(props) > 0
  boxes = vertcat(props.BoundingBox)' ;
  boxes(3:4,:) = boxes(1:2,:)+boxes(3:4,:) ;
end

frame.objects.frameId = ids ;
frame.objects.id = zeros(size(frame.objects.frameId)) ;
frame.objects.box = boxes ;

% This is still not quite enough. The object ids are modulus 2^23. We need
% to find the original ID by matching the annotation file -- as well as
% the object type

for i = 1:numel(frame.objects.frameId)
  ok1 = mod(rdb.objects.id, 2^23) == frame.objects.frameId(i) ;
  ok2 = rdb.objects.startTic <= tic ;
  ok3 = rdb.objects.endTic >= tic ;
  sel = find(ok1 & ok2 & ok3) ;
  if numel(sel) > 1
    warning('Ambiguous match for object with frameId %d at tic %d', frame.objects.frameId(i), tic) ;
  end
  if isempty(sel)
    warning('Unmatched object') ;
    frame.objects.id(i) = NaN ;
    frame.objects.label(i) = NaN ;
  else
    match = sel(end) ;
    frame.objects.id(i) = rdb.objects.id(match) ;
    frame.objects.label(i) = rdb.objects.label(match) ;
  end
end

% Get player info.
i = find(rdb.player.tic == tic) ;
frame.player.position = rdb.player.position(:,i) ;
frame.player.orientation = rdb.player.orientation(i) ;

if nargout == 0

  strings = {} ;
  for i = 1:numel(frame.objects.id)
    k = find(frame.objects.label(i)==rdb.classes.label) ;
    strings{i} = sprintf('%d/%d (%s)', ...
      frame.objects.id(i), ...
      frame.objects.label(i), ...
      rdb.classes.name{k}) ;
  end

  figure(1) ; clf ;
  opts.dx = 320 / 2 ; % half for HDPI (retina) screens
  opts.dy = 200 / 2 ;
  set(gcf, 'windowstyle', 'normal', 'units', 'pixels') ;
  pos  = get(gcf, 'position') ;
  pos(3:4) = [opts.layout(2)*opts.dx, opts.layout(1)*opts.dy] ;
  set(gcf,'units', 'pixels', 'position', pos) ;
  set(gcf,'units', 'normalized') ;
  objcols = colorcube(2^7) ;
  objcols(2^7+1,:) = [1 1 .3] ;
  objcols(2^7+2,:) = [.5 1 .3] ;
  objcols(2^7+3,:) = [.3 .7 1] ;
  depthcols = gray(2^16) ;

  makeAxes(opts,1) ;
  imagesc(ind2rgb(frame.depthmap,depthcols)) ;
  axis image off ;
  makeText(opts,1,'Depth map') ;

  makeAxes(opts,2) ;
  imagesc(ind2rgb(frame.rgb,frame.rgbcols)) ;
  axis image off ; hold on ;
  h = vl_plotbox(frame.objects.box,'g','label',strings) ;
  if ~isempty(h)
    set(h(2,:), ...
      'FontWeight', 'bold', ...
      'FontName', 'AndaleMono', ...
      'FontSize', 6, ...
      'Margin', 0.1) ;
  end
  makeText(opts,2,sprintf('Appearance and objects (time %06d)', tic)) ;

  makeAxes(opts,3) ;
  objmap = bitand(frame.objectmap, 255) ;
  objmap(frame.objectmap >= 2^23) = objmap(frame.objectmap >= 2^23) + 2^7 ;
  imagesc(ind2rgb(objmap,objcols)) ;
  axis image off ;
  makeText(opts,3,'Class and instance segmentation') ;

  makeAxes(opts,4) ;
  levelNumber = max(find(rdb.levels.startTic <= tic)) ;
  levelName = rdb.levels.name{levelNumber} ;
  sel = find(rdb.levels.startTic(levelNumber) <= rdb.player.tic & rdb.player.tic <= tic) ;
  selAll = find(rdb.levels.startTic(levelNumber) <= rdb.player.tic & rdb.player.tic <= rdb.levels.endTic(levelNumber)) ;
  x = rdb.player.position(1,sel) ;
  y = rdb.player.position(2,sel) ;
  z = rdb.player.position(3,sel) ;
  a = rdb.player.orientation(sel) ;
  bounds = [min(rdb.player.position(:,selAll),[],2), max(rdb.player.position(:,selAll),[],2)] ;
  lambda = -0.05 ;
  xbounds = bsxfun(@plus,(1-lambda) * bounds, lambda * mean(bounds,2)) ;

  quiver3(x,y,z,cos(a),sin(a),zeros(size(a))) ; hold on ;
  plot3(x,y,z,'g','linewidth',2) ;
  plot3(x(1),y(1),z(1),'ro','linewidth',4) ;
  axis equal ;
  box on ;
  xlim(xbounds(1,:)) ;
  ylim(xbounds(2,:)) ;
  zlim(xbounds(3,:)) ;
  set(gca,'XTickLabel',[]) ;
  set(gca,'YTickLabel',[]) ;
  set(gca,'ZTickLabel',[]) ;
  grid on ;

  makeText(opts,4,sprintf('Ego-motion (level %s)',levelName)) ;
  drawnow ;
  clear fr ;
end

function h = makeAxes(opts,i)
M = opts.layout(1) ;
N = opts.layout(2) ;
j = mod(i-1,N)+1 ;
i = fix((i-1)/N)+1 ;
i = M-i+1;
dx = opts.dx ;
dy = opts.dy ;
h = axes('units', 'normalized', 'position', ...
         [((j-1)*dx)/(N*dx), ((i-1)*dy)/(M*dy), 1/N, 1/M]) ;

function h = makeText(opts,i,str)
M = opts.layout(1) ;
N = opts.layout(2) ;
j = mod(i-1,N)+1 ;
i = fix((i-1)/N)+1 ;
i = M-i+1 ;
dx = opts.dx ;
dy = opts.dy ;
pos = [((j-.5)*dx - .4*dx)/(N*dx), (i*dy-12)/(M*dy), .8/N, 11/(M*dy)] ;
h = annotation('textbox', ...
               'String', str, ...
               'Units', 'normalized', ...
               'Position', pos, ...
               'LineStyle', 'none', ...
               'BackgroundColor', 'w', ...
               'FontSize', 6, ...
               'FontWeight', 'bold', ...
               'FontName', 'AndaleMono', ...
               'Margin', 1, ...
               'VerticalAlignment', 'middle', ...
               'HorizontalAlignment', 'center') ;
