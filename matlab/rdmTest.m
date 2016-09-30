run ~/src/vlfeat/toolbox/vl_setup ;
basePath = '/Users/vedaldi/Data/1427uv01' ;
basePath = '/Users/vedaldi/Data/ep1-507' ;
basePath = '/Users/vedaldi/Desktop/doomrecord'  ;

rdb = rdmLoad(basePath) ;

figure(100) ; clf ;
subplot(1,2,1) ; plot([rdb.objects.endTic(:),rdb.objects.startTic(:)]) ; legend('start', 'end') ; ylabel('tick') ;
subplot(1,2,2) ; plot([rdb.objects.endTic(:)-rdb.objects.startTic(:)]) ; title('duration') ; ylabel('tick') ;
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

v = VideoWriter('~/Desktop/out3.mp4', 'MPEG-4') ;
open(v) ;
for tic = rdb.ticks.id(1:min(numel(rdb.ticks.id),2e3))
  rdmGetFrame(rdb, tic) ;
  writeVideo(v, getframe(1)) ;
end
close(v) ;




