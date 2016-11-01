function err = rdmTestWarp(varargin)
%RDMTESTWARP  Demonstrate RDMGETWARP()

% Copyright (c) 2016 Andrea Vedaldi

opts.basePath = 'data/doomrecord'  ;
opts = vl_argparse(opts, varargin) ;

rdb = rdmLoad(opts.basePath) ;
t1 = rdb.tics.id(860) ;
t2 = rdb.tics.id(865) ;
%t1 = rdb.tics.id(860) ;
%t2 = rdb.tics.id(865) ;

f1 = rdmGetFrame(rdb,t1) ;
f2 = rdmGetFrame(rdb,t2) ;
[u,v] = rdmGetWarp(f1,f2) ;

im1=im2single(ind2rgb(f1.rgb,f1.rgbcols));
im2=im2single(ind2rgb(f2.rgb,f2.rgbcols));
for k=1:3
  im2_(:,:,k) = interp2(im1(:,:,k),u,v) ;
end

figure(1); clf ;
err=sqrt(sum((im2_-im2).^2,3)) ;
subplot(2,2,1) ;imagesc(im1) ;
subplot(2,2,2) ;imagesc(im2) ;
subplot(2,2,3) ;imagesc(err,[0 3]) ;
subplot(2,2,4) ;imagesc(im2_) ;

err = mean(err(~isnan(err(:)))) ;

if 1
figure(2) ;clf;
while true
  clf ; imagesc(im2) ; axis image off ; title('Press any key') ;
  pause ;
  clf ; imagesc(im2_) ; axis image off ; title('Press any key') ;
  pause ;
end
end

%keyboard

function A = getPlayerTransform(rdb,tic)
i=find(rdb.player.tic==tic) ;
T = rdb.player.position(:,i) ;
r = rdb.player.orientation(i) - pi/2;
A = [
  cos(r)  0 -sin(r)  T(1) ;
  0       1       0  T(3) ;
  sin(r)  0  cos(r)  T(2) ;
  0       0       0  1] ;

%A = [
%  cos(r)  0 -sin(r)  T(2) ;
%  0       1       0  T(3) ;
%  sin(r)  0  cos(r)  T(1) ;
%  0       0       0  1] ;



