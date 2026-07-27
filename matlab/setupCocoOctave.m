function setupCocoOctave()
%SETUPCOCOOCTAVE Add the local COCO Octave overlay ahead of the vendored API.
if exist('OCTAVE_VERSION', 'builtin') == 0
	return ;
end

root = fileparts(mfilename('fullpath')) ;
addpath(fullfile(root, 'coco-octave')) ;