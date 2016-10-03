function images = cocodoomCombine(src, dst, varargin)
%COCODOOMCOMBINE   Merge CocoDoom annotation files.
opts.skip = 1 ;
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

% Skip some images if needed
dstobj.images = dstobj.images(1:opts.skip:end) ;
keep = ismember([dstobj.annotations.image_id], [dstobj.images.id]) ;
dstobj.annotations = dstobj.annotations(keep) ;

% Save
txt = gason(dstobj) ;
f = fopen(dst,'w') ; fwrite(f,txt) ; fclose(f) ;

% Return list of images used
images = {dstobj.images.file_name} ;
