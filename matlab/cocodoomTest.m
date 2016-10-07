function cocodoomTest()
%COCODOOMTEST   Test the Cocodoom data

addpath matlab ;
addpath matlab/coco/MatlabAPI ;
full = {} ;
standard = {} ;

stats = {} ;
stats{end+1} = getStats('data/cocodoom/map-full-train.json') ;
stats{end+1} = getStats('data/cocodoom/map-full-val.json') ;
stats{end+1} = getStats('data/cocodoom/map-full-test.json') ;
stats{end+1} = getStats('data/cocodoom/map-train.json') ;
stats{end+1} = getStats('data/cocodoom/map-val.json') ;
stats{end+1} = getStats('data/cocodoom/map-test.json') ;
stats{end+1} = getStats('data/cocodoom/run-full-train.json') ;
stats{end+1} = getStats('data/cocodoom/run-full-val.json') ;
stats{end+1} = getStats('data/cocodoom/run-full-test.json') ;
stats{end+1} = getStats('data/cocodoom/run-train.json') ;
stats{end+1} = getStats('data/cocodoom/run-val.json') ;
stats{end+1} = getStats('data/cocodoom/run-test.json') ;
stats = horzcat(stats{:}) ;

bar = repmat('-', 1,50);
fprintf('|%-15s|%10s|%10s|\n', 'split', 'images', 'objects') ;
fprintf('|%-15.15s|%10.10s|%10.10s|\n', bar, bar, bar) ;
for i = 1:numel(stats)
  fprintf('|%-15s|%10d|%10d|\n', stats(i).name, stats(i).images, stats(i).objects) ;
end

function stats = getStats(filePath)
fprintf('==== %s ====\n', filePath) ;
coco = CocoApi(filePath) ;
cats = coco.loadCats(coco.getCatIds());
[~,stats.name] = fileparts(filePath) ;
stats.cats.name = {cats.name} ;
stats.images = numel(coco.getImgIds());
stats.objects = numel(coco.getAnnIds());
fprintf('%d images, %d objects\n', stats.images, stats.objects) ;

function plotAnno(coco,annoId)
anno = coco.loadAnns(annoId) ;
imageId = anno.image_id ;
imag = coco.loadImgs(imageId) ;
[im,cols] = imread(fullfile('data','cocodoom',imag.file_name)) ;
figure(1) ;clf;image(ind2rgb(im,cols)) ;hold on ; axis image;
coco.showAnns(anno) ;
