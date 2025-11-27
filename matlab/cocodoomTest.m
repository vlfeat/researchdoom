function cocodoomTest(varargin)
%COCODOOMTEST   Test the Cocodoom data
opts = cocodoomPaths() ;
opts = vl_argparse(opts, varargin) ;

addpath matlab ;
addpath('matlab/coco/MatlabAPI', '-end') ;
full = {} ;
standard = {} ;

stats = {} ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'map-full-train.json')) ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'map-full-val.json')) ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'map-full-test.json')) ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'map-train.json')) ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'map-val.json')) ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'map-test.json')) ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'run-full-train.json')) ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'run-full-val.json')) ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'run-full-test.json')) ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'run-train.json')) ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'run-val.json')) ;
stats{end+1} = getStats(fullfile(opts.dataDir, 'run-test.json')) ;
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
[im,cols] = imread(fullfile(opts.dataDir, imag.file_name)) ;
figure(1) ;clf;image(ind2rgb(im,cols)) ;hold on ; axis image;
coco.showAnns(anno) ;
