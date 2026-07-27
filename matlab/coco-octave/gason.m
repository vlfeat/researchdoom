function out = gason(in)
%GASON Octave-compatible JSON wrapper that shadows the vendored COCO copy.

persistent didTryBuild

if exist('OCTAVE_VERSION', 'builtin') ~= 0
  try
    out = gasonMex('convert', in) ;
    return ;
  end

  if isempty(didTryBuild)
    didTryBuild = true ;
    root = fileparts(mfilename('fullpath')) ;
    cmd = sprintf([...
      'cd ''%s'' && mkoctfile --mex private/gasonMex.cpp ../coco/common/gason.cpp ' ...
      '-I../coco/common -o private/gasonMex'], root) ;
    [status, ~] = system(cmd) ;
    if status == 0
      out = gasonMex('convert', in) ;
      return ;
    end
  end
end

if ischar(in)
  out = jsondecode(in) ;
else
  out = jsonencode(in) ;
end
