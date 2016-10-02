%TESTCOCODATA

opts.cocoPath = 'data/cocodoom/run1/map01/coco.json' ;
opts.dataPath = 'data/cocodoom' ;

addpath matlab/coco/MatlabAPI

coco = CocoApi(opts.cocoPath) ;
imageIds = coco.getImgIds() ;

for t = 1:numel(imageIds)
  imageId = imageIds(t) ;
  imageInfo = coco.loadImgs(imageId) ;
  annoIds = coco.getAnnIds('imgIds', imageId) ;
  annos = coco.loadAnns(annoIds) ;

  format long
  imageId
  imageInfo

  figure(1) ; clf ;

  subplot(2,1,1);
  [pixels,cols] = imread(fullfile(opts.dataPath,imageInfo.file_name)) ;
  image(ind2rgb(pixels,cols)) ;
  axis image off ;

  subplot(2,1,2);
  depth_filename  = strrep(imageInfo.file_name, 'rgb', 'depth');
  imagesc(imread(fullfile(opts.dataPath, depth_filename))) ;
  coco.showAnns(annos(2)) ;
  axis image off ;

  keyboard ;
end


