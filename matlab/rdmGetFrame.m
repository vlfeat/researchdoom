function frame = rdmGetFrame(rdb, tic)

[frame.rgb,frame.rgbcols] = imread(fullfile(...
  rdb.basePath, 'rgb', sprintf('%06d.png', tic))) ;
frame.rgbcols = single(frame.rgbcols) ;

frame.depthmap = imread(fullfile(...
  rdb.basePath, 'depth', sprintf('%06d.png', tic))) ;

frame.objectmap = imread(fullfile(...
  rdb.basePath, 'objects', sprintf('%06d.png', tic))) ;
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
  dx = 320 / 2 ; % half for HDPI (retina) screens
  dy = 200 / 2 ;
  set(gcf, 'windowstyle', 'normal') ;
  set(gcf,'units', 'pixels', 'position',[10 400 4*dx dy]) ;
  objcols = jet(2^8) ;
  objcols(2^7+1,:) = [1 1 0] ;
  objcols(2^7+2,:) = [0 1 0] ;
  objcols(2^7+3,:) = [0 0 1] ;
  depthcols = gray(2^16) ;

  axes('units', 'pixels', 'position',[1 1 dx dy]) ;
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
  makeText(1,1,dx,dy,sprintf('Appearance and objects (time %06d)', tic)) ;

  axes('units', 'pixels', 'position',[dx+1, 1, dx, dy]) ;
  imagesc(ind2rgb(frame.depthmap,depthcols)) ;
  axis image off ;
  makeText(1,2,dx,dy,'Depth map') ;

  axes('units', 'pixels', 'position',[2*dx+1, 1, dx, dy]) ;
  objmap = bitand(frame.objectmap, 255) ;
  objmap(frame.objectmap >= 2^23) = objmap(frame.objectmap >= 2^23) + 2^7 ;
  imagesc(ind2rgb(objmap,objcols)) ;
  axis image off ;
  makeText(1,3,dx,dy,'Class and instance segmentation') ;

  axes('units', 'pixels', 'position',[3*dx+1, 1, dx, dy]) ;
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

  makeText(1,4,dx,dy,sprintf('Ego-motion (level %s)',levelName)) ;
  drawnow ;
  clear fr ;
end

function h = makeText(i,j,dx,dy,str)
pos = [(j-.5)*dx - .4*dx, i*dy-12, .8*dx, 11] ;
h = annotation('textbox', ...
               'String', str, ...
               'Units', 'pixels', ...
               'Position', pos, ...
               'LineStyle', 'none', ...
               'BackgroundColor', 'w', ...
               'FontSize', 6, ...
               'FontWeight', 'bold', ...
               'FontName', 'AndaleMono', ...
               'Margin', 1, ...
               'VerticalAlignment', 'middle', ...
               'HorizontalAlignment', 'center', ...
               'Units', 'pixels') ;
