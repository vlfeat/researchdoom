function images = cocodoomCombine(src, dst, varargin)
%COCODOOMCOMBINE   Merge CocoDoom annotation files.
opts.skip = 1 ;
opts.minArea = 30 ;
opts.categories = [] ;
opts = vl_argparse(opts, varargin) ;

fprintf('cocodoomCombine: producing %s\n', dst) ;

srcobj = {} ;
for i = 1:numel(src)
  srcobj{i} = gason(fileread(src{i})) ;
end

dstobj = srcobj{1} ;
for i = 2:numel(src)
  dstobj.images = horzcat(dstobj.images, srcobj{i}.images) ;
  dstobj.annotations = horzcat(dstobj.annotations, srcobj{i}.annotations) ;
end

% Skip some images if needed.
dstobj.images = dstobj.images(1:opts.skip:end) ;
keep = ismember([dstobj.annotations.image_id], [dstobj.images.id]) ;
dstobj.annotations = dstobj.annotations(keep) ;

% Skip very small objects and retain only a subset of the
% categories.
keep = ([dstobj.annotations.area] >= opts.minArea) ;
if ~isempty(opts.categories)
  keep = keep & ismember([dstobj.annotations.category_id], opts.categories) ;
end
dstobj.annotations = dstobj.annotations(keep) ;

% Remove unused categories.
keep = ismember([dstobj.categories.id], unique([dstobj.annotations.category_id])) ;
dstobj.categories = dstobj.categories(keep) ;

% Convert bit ID fields to uint64 to avoid loss of precision when saving
for i = 1:numel(dstobj.annotations)
  dstobj.annotations(i).id = uint64(dstobj.annotations(i).id) ;
  dstobj.annotations(i).image_id = uint64(dstobj.annotations(i).image_id) ;
end
for i = 1:numel(dstobj.images)
  dstobj.images(i).id = uint64(dstobj.images(i).id) ;
end

% Save the JSON file back.
txt = gason(dstobj) ;
f = fopen(dst,'w') ; fwrite(f,txt) ; fclose(f) ;

% Return the list of images used.
images = {dstobj.images.file_name} ;
