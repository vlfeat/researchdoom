function rdmTest(varargin)
%RDMTEST  Test rdmLoad() and rdmGetFrame()

% Copyright (c) 2016 Andrea Vedaldi

opts.basePath = 'data/doomrecord'  ;
opts.moviePath = 'data/doom.mp4' ;
opts.layout = [1 4] ;
opts = vl_argparse(opts, varargin) ;

rdb = rdmLoad(opts.basePath) ;

figure(100) ; clf ;
subplot(1,2,1) ; plot([rdb.objects.endTic(:),rdb.objects.startTic(:)]) ; legend('start', 'end') ; ylabel('tic') ;
subplot(1,2,2) ; plot([rdb.objects.endTic(:)-rdb.objects.startTic(:)]) ; title('duration') ; ylabel('tic') ;
drawnow ;

figure(101) ; clf ;
x = rdb.player.position(1,:) ;
y = rdb.player.position(2,:) ;
z = rdb.player.position(3,:) ;
a = rdb.player.orientation ;
quiver3(x,y,z,cos(a),sin(a),zeros(size(a))) ; hold on ;
plot3(x,y,z,'g','linewidth',2) ;
plot3(x(1),y(1),z(1),'ro','linewidth',4) ;
axis equal ;

v = VideoWriter(opts.moviePath, 'MPEG-4') ;
open(v) ;
stop = max(find(rdb.tics.id <= rdb.levels.endTic(2))) ;
for tic = rdb.tics.id(1:min(numel(rdb.tics.id),stop))
  rdmGetFrame(rdb, tic, 'layout', opts.layout) ;
  writeVideo(v, getframe(1)) ;
end
close(v) ;
