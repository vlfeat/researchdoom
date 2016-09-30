addpath coco/MatlabAPI

dataPath = '../datasetCOCOBig' ;
coco = CocoApi(fullfile(dataPath,'anno2.json')) ;
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
  
  
  subplot(1,4,1);
  [pixels,cols] = imread(fullfile(dataPath,imageInfo.file_name)) ;
  image(ind2rgb(pixels,cols)) ;
  
  
  subplot(1,4,2);
  depth_filename  = strrep(imageInfo.file_name, 'rgb', 'depth');
  imshow(fullfile(dataPath, depth_filename))
  
  coco.showAnns(annos) ;
  subplot(1,4,3);
  subplot(1,4,4);
  axis image ;  
  
  pause;
end


