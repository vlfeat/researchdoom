function cocodoomGallery()
%COCODOOMGALLERY   Produce a gallery of the CocoDoom categories

addpath matlab ;
addpath matlab/coco/MatlabAPI ;
full = {} ;
standard = {} ;

coco = CocoApi('data/cocodoom/run-train.json') ;
cats = coco.loadCats(coco.getCatIds()) ;

M = 14 ;
N = 7 ;
a = 320/200 ;

figure(1) ; clf ;
p = get(gcf,'position') ;
p(3:4) = [N*32*a M*32] ;
set(gcf,'position',p) ;
set(gcf,'paperunits', 'points', 'papersize', p(3:4), 'paperposition', [1 1 p(3:4)]) ;

for c = 1:numel(cats)
  annId = coco.getAnnIds('catIds', cats(c).id) ;
  fprintf('%03d) id:%03d name:%10s inst:%d\n', c, cats(c).id, cats(c).name, numel(annId)) ;
  ann = coco.loadAnns(annId) ;
  bboxes = reshape([ann.bbox],4,[]) ;
  bboxes(3:4,:) = bboxes(3:4,:) + bboxes(1:2,:) - 1 ;
  bboxes = bboxes + 1 ;
  height = bboxes(4,:)-bboxes(2,:)+1 ;
  width = bboxes(3,:)-bboxes(1,:)+1 ;
  keep = (bboxes(1,:) > 1 & bboxes(2,:) > 1 & bboxes(3,:) < 320 & bboxes(4,:) < 200) ;
  keep = keep & ([ann.area] ./ (height.*width) > 0.5) ;
  score = height/200 + 0.5 * width/200 ;
  score(~keep) = -inf ;
  [~,sel] = max(score) ;
  ann = ann(sel) ;
  annId = annId(sel) ;

  imgId = ann.image_id ;
  img = coco.loadImgs(imgId) ;

  i = M-fix((c-1)/N)-1;
  j = mod(c-1,N) ;
  axes('units','normalized','position',[j/N i/M 1/N 1/M]) ;
  [im,colors] = imread(fullfile('data/cocodoom', img.file_name)) ;
  image(ind2rgb(im, colors));

  hold on ;
  for i = 1:numel(ann.segmentation) ;
    plot(ann.segmentation{i}(1:2:end),ann.segmentation{i}(2:2:end), ...
         'k', 'linewidth', 1) ;
    plot(ann.segmentation{i}(1:2:end),ann.segmentation{i}(2:2:end), ...
         'y', 'linewidth', 0.5) ;
  end

  h = text(.5, .95, cats(c).name, ...
           'Units', 'normalized', ...
           'LineStyle', 'none', ...
           'BackgroundColor', 'w', ...
           'FontSize', 4, ...
           'FontWeight', 'bold', ...
           'FontName', 'Helvetica', ...
           'Margin', 1, ...
           'VerticalAlignment', 'top', ...
           'HorizontalAlignment', 'center') ;

  axis image off ;
end

print -dpdf -r300 data/cocodoom-gallery.pdf
print -dpng -r300 data/cocodoom-gallery.png
